"""
    The file contains one Ai class, which contains different ai functions,
    and two other functions.
    One converts an angle from cartesian to perpendicular and the other
    calculates the periodic difference between two angles.
"""

import math
import pymunk
from pymunk import Vec2d
import gameobjects
from collections import defaultdict, deque

MIN_ANGLE_DIF = math.radians(5)


def angle_between_vectors(vec1, vec2):
    """
        Since Vec2d operates in a cartesian coordinate space we have to
        convert the resulting vector to get the correct angle for our space.
    """
    vec = vec1 - vec2
    vec = vec.perpendicular()
    return vec.angle


def periodic_difference_of_angles(angle1, angle2):
    return (angle1 % (2*math.pi)) - (angle2 % (2*math.pi))


class Ai:
    """
        A simple ai that finds the shortest path to the target using
        a breadth first search. Also capable of shooting other tanks and or
        wooden boxes.
    """

    def __init__(self, tank,  game_objects_list, tanks_list, space, currentmap):
        self.tank               = tank
        self.game_objects_list  = game_objects_list
        self.tanks_list         = tanks_list
        self.space              = space
        self.currentmap         = currentmap
        self.flag = None
        self.MAX_X = currentmap.width - 1
        self.MAX_Y = currentmap.height - 1
        self.last_distance = 1

        self.path = deque()
        self.move_cycle = self.move_cycle_gen()
        self.update_grid_pos()

    def update_grid_pos(self):
        """
            This should only be called in the beginning, or at the
            end of a move_cycle.
        """
        self.grid_pos = self.get_tile_of_position(self.tank.body.position)

    def decide(self):
        """
            Main decision function that gets called on every
            tick of the game.
        """
        self.maybe_shoot()
        next(self.move_cycle)

        pass

    def maybe_shoot(self):
        """
            Makes a raycast query in front of the tank. If another tank
            or a wooden box is found, then we shoot.
        """
        res = self.space.segment_query_first((self.tank.body.position[0] - \
              0.6 * math.sin(self.tank.body.angle), self.tank.body.position[1] +\
              0.6 * math.cos(self.tank.body.angle)), (self.tank.body.position[0] -\
              10*math.sin(self.tank.body.angle), self.tank.body.position[1] + \
              10*math.cos(self.tank.body.angle)), 0, pymunk.ShapeFilter())
        if res is not None:
            try:
                if hasattr(res, 'shape'):
                    if isinstance(res.shape.parent, gameobjects.Tank):
                        bullet = self.tank.shoot(self.space)
                        if bullet is not None:
                            self.game_objects_list.append(bullet)
                    elif isinstance(res.shape.parent, gameobjects.Box):
                        if res.shape.parent.boxmodel.destructable is True:
                            bullet = self.tank.shoot(self.space)
                            if bullet is not None:
                                self.game_objects_list.append(bullet)
            except:
                pass

    def move_cycle_gen(self):
        """
            A generator that iteratively goes through all the required
            steps to move to our goal.
        """
        while True:
            self.update_grid_pos()
            path = self.find_shortest_path("without_metalbox")
            if not path:
                path = self.find_shortest_path("metalbox")
                yield
                if not path:
                    continue
            next_coord = path.pop()
            next_coord += Vec2d(0.5, 0.5)
            yield
            target_angle = \
            angle_between_vectors(Vec2d(self.tank.body.position), next_coord)
            angle_tank = self.tank.body.angle
            self.turn(angle_tank, target_angle)
            while not self.correct_angle(angle_tank, target_angle):
                angle_tank = self.tank.body.angle
                target_angle = \
                angle_between_vectors(Vec2d(self.tank.body.position),
                                      next_coord)
                yield
            self.tank.accelerate()
            while not self.correct_pos(next_coord, self.last_distance):
                yield
            yield

    def correct_pos(self, target_pos, last_distance):
        """
            Checks if the tank is on the correct position, compared from the
            last one.
        """
        tank_pos = Vec2d(self.tank.body.position)
        current_distance = target_pos.get_distance(tank_pos)
        self.last_distance = current_distance
        if last_distance < current_distance:
            return True
        else:
            return False

    def turn(self, tank_angle, target_angle):
        """
            Finds the angle closest to next tile, and turns accordingly.
            WIP: Sometimes it turns to the other side.
        """
        angle_diff = periodic_difference_of_angles(tank_angle, target_angle)
        if ((angle_diff + 2 * math.pi) % 2
           * math.pi >= math.pi and abs(angle_diff) > MIN_ANGLE_DIF):
            self.tank.stop_moving()
            self.tank.turn_left()
        elif ((angle_diff + 2 * math.pi) % 2 * math.pi
              < math.pi and abs(angle_diff) > MIN_ANGLE_DIF):
            self.tank.stop_moving()
            self.tank.turn_right()

    def correct_angle(self, tank_angle, target_angle):
        """
            If the tank has the correct angle to the next tile; stop turning.
        """
        angle_diff = periodic_difference_of_angles(target_angle, tank_angle)
        if abs(angle_diff) <= MIN_ANGLE_DIF:
            self.tank.stop_turning()
            return True
        else:
            return False

    def find_shortest_path(self, box_indicator):
        """
            A simple Breadth First Search using integer coordinates as our
            nodes. Edges are calculated as we go, using an external function.
        """
        # To be implemented
        dict = {}
        shortest_path = []
        visited = set()
        queue = deque()
        queue.append(self.grid_pos)
        goal_node = None
        while queue:
            node = Vec2d(queue.popleft())
            if node == self.get_target_tile().int_tuple:
                goal_node = node.int_tuple
                break
            for neighbor in self.get_tile_neighbors(node, box_indicator):
                neighbor = neighbor.int_tuple
                if neighbor not in visited:
                    queue.append(neighbor)
                    visited.add(neighbor)
                    dict[neighbor] = node.int_tuple
        if goal_node is None:
            return deque([])
        else:
            key = goal_node
            while key != self.grid_pos.int_tuple:
                shortest_path.append(Vec2d(key))
                parent_node = dict[key]
                key = parent_node
            return deque(shortest_path)

    def get_target_tile(self):
        """
            Returns position of the flag if we don't have it. If we
            do have the flag, return the position of our home base.
        """
        if self.tank.flag is not None:
            x, y = self.tank.start_position
        else:
            self.get_flag()   # Ensure that we have initialized it.
            x, y = self.flag.x, self.flag.y
        return Vec2d(int(x), int(y))

    def get_flag(self):
        """
            This has to be called to get the flag, since we don't know
            where it is when the Ai object is initialized.
        """
        if self.flag is None:
            # Find the flag in the game objects list
            for obj in self.game_objects_list:
                if isinstance(obj, gameobjects.Flag):
                    self.flag = obj
                    break
        return self.flag

    def get_tile_of_position(self, position_vector):
        """
            Converts and returns the float position of our tank to an
            integer position.
        """
        x, y = position_vector
        return Vec2d(int(x), int(y))

    def get_tile_neighbors(self, coord_vec, box_indicator):
        """
            Returns all bordering grid squares of the input coordinate.
            A bordering square is only considered accessible if it is grass
            or a wooden box.
        """
        neighbors = []   # Find the coordinates of the tiles' four neighbors
        neighbors.append(coord_vec + Vec2d(1, 0))
        neighbors.append(coord_vec + Vec2d(-1, 0))
        neighbors.append(coord_vec + Vec2d(0, 1))
        neighbors.append(coord_vec + Vec2d(0, -1))
        if box_indicator == "without_metalbox":
            return filter(self.filter_tile_neighbors, neighbors)
        else:
            return filter(self.filter_tile_neighbors_metalbox, neighbors)

    def filter_tile_neighbors(self, coord):
        """
            Filter for all the tiles around the tank. This filter removes
            the immovable stones so we don't count those tiles to find the
            shortest path.
        """
        coord = coord.int_tuple
        if coord[1] <= self.MAX_Y and coord[0] <= self.MAX_X and coord[1] >= \
           0 and coord[0] >=\
           0 and (self.currentmap.boxAt(coord[0], coord[1])
                  == 0 or self.currentmap.boxAt(coord[0], coord[1]) == 2):
            return True
        return False

    def filter_tile_neighbors_metalbox(self, coord):
        """
            Filter for all the tiles around the tank, metalboxes included.  This
            filter removes the immovable stones so we don't count those tiles to
            find the shortest path.
        """
        coord = coord.int_tuple
        if coord[1] <= self.MAX_Y and coord[0] <= self.MAX_X and coord[1] >=\
           0 and coord[0] >= 0 and (self.currentmap.boxAt(coord[0], coord[1])
                                    == 0 or self.currentmap.boxAt(coord[0],
                                                                  coord[1])
                                    == 2 or self.currentmap.boxAt(coord[0],
                                                                  coord[1])
                                    == 3):
            return True
        return False

SimpleAi = Ai # Legacy
