"""
    The file contains several different classes with functions for the different
    objects in the game and two other functions.
"""

import images
import pygame
import pymunk
import math
import boxmodels
import sound

DEBUG = False   # Change this to set it in debug mode


def physics_to_display(x):
    """
        This function is used to convert coordinates in the physic engine
        into the display coordinates.
    """
    return x * images.TILE_SIZE


class GameObject:
    """
        Mostly handles visual aspects (pygame) of an object.
        Subclasses need to implement two functions:
        - screen_position    that will return the position of the object on
          the screen
        - screen_orientation that will return how much the object is rotated on
          the screen (in degrees).
    """

    def __init__(self, sprite):
        self.sprite         = sprite

    def update(self):
        """
            Placeholder, supposed to be implemented in a subclass.
            Should update the current state (after a tick) of the object.
        """
        return

    def post_update(self):
        """
            Should be implemented in a subclass. Make updates that depend on
            other objects than itself.
        """
        return

    def update_screen(self, screen):
        """
            Updates the visual part of the game. Should NOT need to be changed
            by a subclass.
        """
        sprite = self.sprite

        p = self.screen_position()
        # Get the position of the object (pygame coordinates)

        sprite = pygame.transform.rotate(sprite, self.screen_orientation())
        # Rotate the sprite using the rotation of the object

        # The position of the screen correspond to the center of the object,
        # but the function screen.blit expect to receive the top left corner
        # as argument, so we need to adjust the position p with an offset
        # which is the vector between the center of the sprite and the top left
        # corner of the sprite
        offset = pymunk.Vec2d(sprite.get_size()) / 2.
        p = p - offset
        screen.blit(sprite, p)   # Copy the sprite on the screen


class GamePhysicsObject(GameObject):
    """
        This class extends GameObject and it is used for objects which have a
        physical shape (such as tanks and boxes). This class handle the
        physical interaction of the objects.
    """

    def __init__(self, x, y, orientation, sprite, space, movable):
        """
            Takes as parameters the starting coordinate (x,y), the orientation,
            the sprite (aka the image representing the object), the physic
            engine object (space) and whether the object can be
            moved (movable).
        """

        super().__init__(sprite)

        # Half dimensions of the object converted from screen coordinates
        # to physic coordinates
        half_width          = 0.5 * self.sprite.get_width() / images.TILE_SIZE
        half_height         = 0.5 * self.sprite.get_height() / images.TILE_SIZE
        self.half_width = half_width
        self.half_height = half_height
        # Physical objects have a rectangular shape, the points correspond to
        # the corners of that shape.
        points              = [[-half_width, -half_height],
                               [-half_width, half_height],
                               [half_width, half_height],
                               [half_width, -half_height]]
        self.points = points
        # Create a body (which is the physical representation of this game
        # object in the physic engine)
        if(movable):
            # Create a movable object with some mass and moments
            # (considering the game is a top view game, with no gravity,
            # the mass is set to the same value for all objects)."""
            mass = 10
            moment = pymunk.moment_for_poly(mass, points)
            self.body         = pymunk.Body(mass, moment)
        else:
            self.body         = pymunk.Body(body_type=pymunk.Body.STATIC)
            # Create a non movable (static) object

        self.body.position  = x, y
        self.body.angle     = math.radians(orientation)
        # orientation is provided in degress, but pymunk expects radians.
        self.shape          = pymunk.Poly(self.body, points)
        # Create a polygon shape using the corner of the rectangle
        self.shape.parent = self
        # Set some value for friction and elasticity, which defines
        # interraction in case of a colision
        self.shape.friction = 0.5
        self.shape.elasticity = 0.1

        # Add the object to the physic engine
        if(movable):
            space.add(self.body, self.shape)
        else:
            space.add(self.shape)

    def screen_position(self):
        """ Converts the body's position in the physics engine
            to screen coordinates. """
        return physics_to_display(self.body.position)

    def screen_orientation(self):
        """ Angles are reversed from the engine to the display. """
        return -math.degrees(self.body.angle)

    def update_screen(self, screen):
        super().update_screen(screen)
        # debug draw
        if DEBUG:
            ps = [self.body.position+p for p in self.points]

            ps = [physics_to_display(p) for p in ps]
            ps += [ps[0]]
            pygame.draw.lines(screen, pygame.color.THECOLORS["red"],
                              False, ps, 1)


def clamp(minval, val, maxval):
    """ Convenient helper function to bound a value to a specific interval."""
    if val < minval:
        return minval
    if val > maxval:
        return maxval
    return val


class Bullet(GamePhysicsObject):
    """
        Extends GamePhysicsObject and handles aspects which are
        specific to our bullets.
    """

    def __init__(self, x, y, orientation, sprite, space):
        super().__init__(x, y, orientation, sprite, space, True)
        self.shape.collision_type = 1
        self.bullet_velocity      = 3.0
        self.bullet_acceleration  = 0.0
        self.body.velocity = pymunk.Vec2d(self.bullet_velocity, 0)
        self.shooting_angle = orientation

    ACCELERATION = 0.0
    MAX_SPEED = 8.0

    def update(self):
        """
            A function to update the bullet position. Gets called at every
            tick of the game.
        """
        if(math.fabs(self.bullet_velocity) > 0):
            self.bullet_velocity *= self.body.velocity.length / \
                 math.fabs(self.bullet_velocity)
        self.body.velocity = \
            pymunk.Vec2d(0, self.bullet_velocity).rotated(self.shooting_angle)
        self.body.position += 0.01 * self.body.velocity


class Tank(GamePhysicsObject):
    """
        Extends GamePhysicsObject and handles aspects
        which are specific to our tanks.
    """

    # Constant values for the tank, acessed like: Tank.ACCELERATION
    ACCELERATION = 0.4
    NORMAL_MAX_SPEED = 2.0
    FLAG_MAX_SPEED = NORMAL_MAX_SPEED * 0.5

    def __init__(self, x, y, orientation, sprite, space):
        super().__init__(x, y, orientation, sprite, space, True)
        # Define variable used to apply motion to the tanks
        self.acceleration         = 0.0
        self.velocity             = 0.0
        self.angular_acceleration = 0.0
        self.angular_velocity     = 0.0
        self.flag                 = None
        self.hp                   = 2
        # This variable is used to access the flag object, if
        # the current tank is carrying the flag
        self.maximum_speed        = Tank.NORMAL_MAX_SPEED
        # Impose a maximum speed to the tank
        self.start_position       = pymunk.Vec2d(x, y)
        # Define the start position, which is also the position where
        # the tank has to return with the flag
        self.shape.collision_type = 2
        self.length = 2 * self.half_width
        self.cooldown = 0
        self.respawn_cooldown = 0

    def accelerate(self):
        """ Call this function to make the tank move forward. """
        self.acceleration = Tank.ACCELERATION

    def decelerate(self):
        """ Call this function to make the tank move backward. """
        self.acceleration = -Tank.ACCELERATION

    def turn_left(self):
        """ Makes the tank turn left (counter clock-wise). """
        self.angular_acceleration = -Tank.ACCELERATION

    def turn_right(self):
        """ Makes the tank turn right (clock-wise). """
        self.angular_acceleration = Tank.ACCELERATION

    def update(self):
        """
            A function to update the objects coordinates. Gets called at
            every tick of the game.
        """
        if self.cooldown >= 1:
            self.cooldown -= 1
        if self.respawn_cooldown >= 1:
            self.respawn_cooldown -= 1
        # Update the velocity of the tank in function of the physic
        # simulation (in case of colision, the physic simulation
        # will change the speed of the tank)
        if(math.fabs(self.velocity) > 0):
            self.velocity *= self.body.velocity.length / \
                math.fabs(self.velocity)
        if(math.fabs(self.angular_velocity) > 0):
            self.angular_velocity *= math.fabs(self.body.angular_velocity
                                               / self.angular_velocity)

        # Update the velocity in function of the acceleration
        self.velocity         += self.acceleration
        self.angular_velocity += self.angular_acceleration

        # Make sure the velocity is not larger than a maximum speed
        self.velocity         = clamp(-self.maximum_speed, self.velocity,
                                      self.maximum_speed)
        self.angular_velocity = clamp(-self.maximum_speed,
                                      self.angular_velocity,
                                      self.maximum_speed)

        # Update the physic velocity
        self.body.velocity =\
            pymunk.Vec2d((0, self.velocity)).rotated(self.body.angle)
        self.body.angular_velocity = self.angular_velocity

    def stop_moving(self):
        """ Call this function to make the tank stop moving. """
        self.velocity     = 0
        self.acceleration = 0

    def stop_turning(self):
        """ Call this function to make the tank stop turning. """
        self.angular_velocity     = 0
        self.angular_acceleration = 0

    def post_update(self):
        # If the tank carries the flag, then update the positon of the flag
        if(self.flag is not None):
            self.flag.x           = self.body.position[0]
            self.flag.y           = self.body.position[1]
            self.flag.orientation = -math.degrees(self.body.angle)
        # Else ensure that the tank has its normal max speed
        else:
            self.maximum_speed = Tank.NORMAL_MAX_SPEED

    def try_grab_flag(self, flag):
        """
            Call this function to try to grab the flag, if the flag is not on
            other tank and it is close to the current tank, then the current
            tank will grab the flag.
        """
        # Check that the flag is not on other tank
        if(not flag.is_on_tank):
            # Check if the tank is close to the flag
            flag_pos = pymunk.Vec2d(flag.x, flag.y)
            if((flag_pos - self.body.position).length < 0.5):
                # Grab the flag !
                self.flag           = flag
                self.is_on_tank     = True
                self.maximum_speed  = Tank.FLAG_MAX_SPEED

    def has_won(self):
        """
            Check if the current tank has won (if it is has the flag and it is
            close to its start position).
        """
        return self.flag is not None and (self.start_position
                                          - self.body.position).length < 0.2

    def shoot(self, space):
        """ Creates a bullet. """
        if self.cooldown == 0:
            bullet = Bullet(self.body.position[0] - 0.6
                            * math.sin(self.body.angle),
                            self.body.position[1] + 0.6
                            * math.cos(self.body.angle),
                            self.body.angle,
                            pygame.transform.rotate(images.bullet,
                                              math.degrees(-self.body.angle)),
                            space)
            sound.shoot.set_volume(0.2)
            sound.shoot.play()
            self.cooldown = 20
            return bullet


class Box(GamePhysicsObject):
    """ This class extends the GamePhysicsObject to handle box objects. """

    def __init__(self, x, y, boxmodel, space):
        """
            It takes as arguments the coordinate of the starting position of
            the box (x,y) and the box model (boxmodel).
        """
        super().__init__(x, y, 0, boxmodel.sprite, space, boxmodel.movable)
        self.boxmodel = boxmodel
        self.hp = 2
        if boxmodel.destructable is True:
            self.shape.collision_type = 3
        else:
            self.shape.collision_type = 4


class GameVisibleObject(GameObject):
    """
        This class extends GameObject for object that are visible on screen
        but have no physical representation (bases and flag)
    """

    def __init__(self, x, y, sprite):
        """ It takes argument the coordinates (x,y) and the sprite. """
        self.x            = x
        self.y            = y
        self.orientation  = 0
        super().__init__(sprite)

    def screen_position(self):
        return physics_to_display(pymunk.Vec2d(self.x, self.y))

    def screen_orientation(self):
        return self.orientation


class Explosion(GameVisibleObject):
    """ This class extends GameVisibleObject for representing exposions."""

    def __init__(self, x, y, orientation, sprite, space):
        super().__init__(x, y, sprite)
        self.exp_cooldown           = 0

    def update(self):
        """
            A function to update the expolsion cooldown. Gets called at every
            tick of the game.
        """
        if self.exp_cooldown >= 1:
            self.exp_cooldown -= 1


class Flag(GameVisibleObject):
    """ This class extends GameVisibleObject for representing flags."""

    def __init__(self, x, y):
        self.is_on_tank   = False
        super().__init__(x, y,  images.flag)
