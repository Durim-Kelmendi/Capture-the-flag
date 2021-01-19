"""The file contains a while loop that runs the game and different setups."""

import pygame
from pygame.locals import *
from pygame.color import *
import pymunk

# ----- Initialisation -----#

# -- Initialise the display
pygame.init()
pygame.display.set_mode()

# -- Initialise the clock
clock = pygame.time.Clock()

# -- Initialise the physics engine
space = pymunk.Space()
space.gravity = (0.0,  0.0)

# -- Import from the ctf framework
import ai
import boxmodels
import images
import gameobjects
import maps
import sys
import sound
import math

player_mode = ""

if sys.argv[1] == "--singleplayer":
    player_mode = "singleplayer"
elif sys.argv[1] == "--hot--multiplayer":
    player_mode = "hot multiplayer"

# -- Constants
FRAMERATE = 50

# pygame.mixer.Sound.play(sound.b_music)

# -- Variables
#   Define the current level
current_map         = maps.map0

#   List of all game objects
game_objects_list   = []
tanks_list          = []

ai_list = []
game_score = []

# -- Resize the screen to the size of the current level
screen = pygame.display.set_mode(current_map.rect().size)

# -- Generate the background
background = pygame.Surface(screen.get_size())

# Collision types on objects
collision_type = {"bullet": 1, "tank": 2, "boxes": 3, "Indestrucatble_box": 4}

#   Copy the grass tile all over the level area
for x in range(0, current_map.width):
    for y in range(0,  current_map.height):
        background.blit(images.grass,  (x*images.TILE_SIZE,
                                        y*images.TILE_SIZE))

# -- Create the boxes
box_list = []


def create_boxes():
    """A function that creates boxes."""
    box_list.clear()
    for x in range(0, current_map.width):
        for y in range(0,  current_map.height):
            # Get the type of boxes
            box_type = current_map.boxAt(x, y)
            box_model = boxmodels.get_model(box_type)
            # If the box model is non null, create a box
            if(box_model is not None):
                # Create a "Box" using the model "box_model" at the
                # coordinate (x,y) (an offset of 0.5 is added since
                # the constructor of the Box object expects to know
                # the centre of the box, have a look at the coordinate
                # systems section for more explanations).
                box = gameobjects.Box(x + 0.5, y + 0.5, box_model, space)
                game_objects_list.append(box)
                box_list.append(box)


create_boxes()

# Barrier
static_body = space.static_body
static_lines = [pymunk.Segment(static_body, (0, 0), (0, current_map.height),
                               0.1), pymunk.Segment(static_body, (0, 0),
                                                    (current_map.width, 0),
                                                    0.1),
                pymunk.Segment(static_body, (0, current_map.height),
                               (current_map.width, current_map.height), 0.1),
                pymunk.Segment(static_body, (current_map.width, 0),
                               (current_map.width, current_map.height), 0.1)]

for line in static_lines:
    line.elasticity = 0.2
    line.friction = 0.4

space.add(static_lines)

# -- Create the tanks
player_tank = None
scnd_player_tank = ""
for i in range(0, len(current_map.start_positions)):
    # Get the starting position of the tank "i"
    pos = current_map.start_positions[i]
    # Create the tank, images.tanks contains the image representing the tank
    tank = gameobjects.Tank(pos[0], pos[1], pos[2], images.tanks[i], space)
    if i == 0:
        player_tank = tank
    elif i == 1 and player_mode == "hot multiplayer":
        scnd_player_tank = tank
    else:
        ai_tank = ai.Ai(tank, game_objects_list, tanks_list, space,
                        current_map)
        ai_list.append(ai_tank)
    base = gameobjects.GameVisibleObject(current_map.start_positions[i][0],
                                         current_map.start_positions[i][1],
                                         images.bases[i])
    game_objects_list.append(base)
    # Add the tank to the list of objects to display
    game_objects_list.append(tank)
    # Add the tank to the list of tanks
    tanks_list.append(tank)

for i in tanks_list:
    game_score.append(0)

# Create the flag, images.flag contains the image representing the flag
flag = gameobjects.Flag(current_map.flag_position[0],
                        current_map.flag_position[1])
# Add the flag to the list of objects to display
game_objects_list.append(flag)
respawn_cooldown = 0


def collision_bullet_tank(arb, space, data):
    """A function that handels collisions between a bullet and a tank."""
    if(arb.shapes[0].parent in game_objects_list):
        game_objects_list.remove(arb.shapes[0].parent)
    space.remove(arb.shapes[0], arb.shapes[0].body)
    tank = arb.shapes[1]
    if tank.parent.respawn_cooldown == 0:
        damaged_tank(tank)
    return False


def damaged_tank(tank):
    """A function that handles events when a tank is damaged"""
    if tank.parent.hp > 0:
        tank.parent.hp -= 1
    else:
        if tank.parent.flag is not None:
            tank.parent.flag = None
            flag.is_on_tank = False
        tank.parent.hp = 2
        tank.parent.body.position = tank.parent.start_position
        tank.parent.respawn_cooldown = 300
        explosion = gameobjects.Explosion(tank.parent.body.position[0],
                                          tank.parent.body.position[1],
                                          tank.parent.body.angle,
                                          images.explosion, space)
        game_objects_list.append(explosion)
        explosion.exp_cooldown = 2


def collision_bullet(arb, space, data):
    """A function that handels collisions between a bullet and other things."""
    game_objects_list.remove(arb.shapes[0].parent)
    space.remove(arb.shapes[0], arb.shapes[0].body)
    return False


def collision_bullet_woodbox(arb, space, data):
    """A function that handels collisions between a bullet and a woodbox."""
    if arb.shapes[0].parent in game_objects_list:
        game_objects_list.remove(arb.shapes[0].parent)
    space.remove(arb.shapes[0], arb.shapes[0].body)
    box = arb.shapes[1]
    damaged_woodbox(box)
    return False


def damaged_woodbox(box):
    """A function that handles events when a woodbox is damaged"""
    if box.parent.hp > 0:
        box.parent.hp -= 1
    else:
        box.parent.hp = 2
        box_list.remove(box.parent)
        game_objects_list.remove(box.parent)
        space.remove(box, box.body)
        explosion = gameobjects.Explosion(box.parent.body.position[0],
                                          box.parent.body.position[1],
                                          box.parent.body.angle,
                                          images.explosion, space)
        game_objects_list.append(explosion)
        explosion.exp_cooldown = 2
        sound.wood_destruction.set_volume(0.2)
        sound.wood_destruction.play()
        return explosion


def collision_bullet_box(arb, space, data):
    """
       A function that handels collision between boxes that are
       not a wooden box and a bullet.
    """
    if(arb.shapes[0].parent in game_objects_list):
        game_objects_list.remove(arb.shapes[0].parent)
    space.remove(arb.shapes[0], arb.shapes[0].body)
    return True

handler = space.add_collision_handler(1, 0)
handler.pre_solve = collision_bullet

handler = space.add_collision_handler(1, 2)
handler.pre_solve = collision_bullet_tank

handler = space.add_collision_handler(1, 3)
handler.pre_solve = collision_bullet_woodbox

handler = space.add_collision_handler(1, 4)
handler.pre_solve = collision_bullet_box


def score(flag, game_score, player_tank, game_objects_list, tanks_list,
          current_map, index):
    """A function that displays the score on the console."""
    game_score[index] += 1
    player_tank.flag = None
    sound.victory.set_volume(0.2)
    sound.victory.play()
    score_str = []
    score_str.append("Current score: ")
    print("Current score: ")
    for i in range(len(tanks_list)):
        score_str.append("Player " + str(i + 1) + ": " + str(game_score[i]))
        print("Player ", str(i + 1), ": ", game_score[i])
    print(" ")
    display_score(score_str, player_tank)
    for tank in tanks_list:
        tank.body.position = tank.start_position
    for elm in box_list:
        game_objects_list.remove(elm)
    create_boxes()


def display_score(score_str, tank):
    """A function that displays the score on the pygame window."""
    score_str.append("Press h to continue...")
    pygame.display.set_caption('Score of the Players')
    font = pygame.font.Font('freesansbold.ttf', 16)
    blue = (0, 0, 128)
    white = (255, 255, 255)
    running = True
    while running:
        screen.fill(white)
        for i in range(len(score_str)):
            text = font.render(score_str[i], True, blue)
            textRect = text.get_rect()
            textRect.center = (150, (60 + i * 20))
            screen.blit(text, textRect)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_h:
                running = False
    pygame.display.set_caption('pygame window')
    pygame.display.update()


# ----- Main Loop -----#
def play():
    """A function that runs the game."""
    # -- Control whether the game run
    running = True
    skip_update = 0
    index = []
    while running:
        # -- Handle the events
        for event in pygame.event.get():
            # Check if we receive a QUIT event (for instance, if the user press
            # the close button of the window) or if the user press the escape
            # key.
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
            if event.type == KEYDOWN and event.key == K_UP:
                player_tank.accelerate()
            if event.type == KEYUP and event.key == K_UP:
                player_tank.stop_moving()
            if event.type == KEYDOWN and event.key == K_DOWN:
                player_tank.decelerate()
            if event.type == KEYUP and event.key == K_DOWN:
                player_tank.stop_moving()
            if event.type == KEYDOWN and event.key == K_LEFT:
                player_tank.turn_left()
            if event.type == KEYUP and event.key == K_LEFT:
                player_tank.stop_turning()
            if event.type == KEYDOWN and event.key == K_RIGHT:
                player_tank.turn_right()
            if event.type == KEYUP and event.key == K_RIGHT:
                player_tank.stop_turning()
            if event.type == KEYDOWN and event.key == K_SPACE:
                bullet = player_tank.shoot(space)
                if bullet is not None:
                    game_objects_list.append(bullet)

            if player_mode == "hot multiplayer":
                if event.type == KEYDOWN and event.key == K_w:
                    scnd_player_tank.accelerate()
                if event.type == KEYUP and event.key == K_w:
                    scnd_player_tank.stop_moving()
                if event.type == KEYDOWN and event.key == K_s:
                    scnd_player_tank.decelerate()
                if event.type == KEYUP and event.key == K_s:
                    scnd_player_tank.stop_moving()
                if event.type == KEYDOWN and event.key == K_a:
                    scnd_player_tank.turn_left()
                if event.type == KEYUP and event.key == K_a:
                    scnd_player_tank.stop_turning()
                if event.type == KEYDOWN and event.key == K_d:
                    scnd_player_tank.turn_right()
                if event.type == KEYUP and event.key == K_d:
                    scnd_player_tank.stop_turning()
                if event.type == KEYDOWN and event.key == K_x:
                    bullet = scnd_player_tank.shoot(space)
                    if bullet != None:
                        game_objects_list.append(bullet)

        for i in range(len(ai_list)):
            ai_list[i].tank.try_grab_flag(flag)
            if ai_list[i].tank.has_won():
                ai_list[i].tank.flag = None
                ai_list[i].flag = None
                flag.is_on_tank = False
                flag.x = current_map.flag_position[0]
                flag.y = current_map.flag_position[1]
                flag.orientation = 0
                if player_mode == "hot multiplayer":
                    score(flag, game_score, ai_tank, game_objects_list,
                          tanks_list, current_map, 2 + i)
                else:
                    score(flag, game_score, ai_tank, game_objects_list,
                          tanks_list, current_map, 1 + i)

        player_tank.try_grab_flag(flag)
        if player_mode == "hot multiplayer":
            scnd_player_tank.try_grab_flag(flag)
        # -- Update physicsupdate
        if skip_update == 0:
            # Loop over all the game objects and update their speed in function
            # of their acceleration.
            for i in range(len(game_objects_list)):
                game_objects_list[i].update()
            skip_update = 2
        else:
            skip_update -= 1

        for i in range(len(game_objects_list)):
            if isinstance(game_objects_list[i], gameobjects.Explosion):
                if game_objects_list[i].exp_cooldown == 0:
                    index.append(game_objects_list[i])

        for elm in index:
            if elm is not None:
                game_objects_list.remove(elm)
        index.clear()

        #   Check collisions and update the objects position
        space.step(1 / FRAMERATE)

        #  Update object that depends on an other object position
        # (for instance a flag)
        for obj in game_objects_list:
            obj.post_update()

        for tank in ai_list:
            tank.decide()

        # -- Update Display
        # Display the background on the screen
        screen.blit(background, (0, 0))

        # Update the display of the game objects on the screen
        for obj in game_objects_list:
            obj.update_screen(screen)

        #   Redisplay the entire screen (see double buffer technique)
        pygame.display.flip()

        #  Control the game framerate
        clock.tick(FRAMERATE)

        if player_tank.has_won():
            tank.flag = None
            flag.is_on_tank = False
            flag.x = current_map.flag_position[0]
            flag.y = current_map.flag_position[1]
            flag.orientation = 0
            score(flag, game_score, player_tank, game_objects_list,
                  tanks_list, current_map, 0)
        elif player_mode == "hot multiplayer" and scnd_player_tank.has_won():
            tank.flag = None
            flag.is_on_tank = False
            flag.x = current_map.flag_position[0]
            flag.y = current_map.flag_position[1]
            flag.orientation = 0
            score(flag, game_score, scnd_player_tank, game_objects_list,
                  tanks_list, current_map, 1)


play()
