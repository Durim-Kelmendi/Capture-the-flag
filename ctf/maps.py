"""
   The file contains one map class with functions and three maps. The class is
   an instance blueprint for how the game map will look.
"""

import images
import pygame
import pymunk


class Map:
    """ An instance of Map is a blueprint for how the game map will look. """

    def __init__(self,  width,  height,  boxes,  start_positions,
                 flag_position):
        """
            Takes as argument the size of the map (width, height),
            an array with the boxes type, the start position of tanks
            (start_positions) and the position of the
            flag (flag_position).
        """
        self.width              = width
        self.height             = height
        self.boxes              = boxes
        self.start_positions    = start_positions
        self.flag_position      = flag_position

    def rect(self):
        """Draws window size to. """
        return pygame.Rect(0, 0, images.TILE_SIZE*self.width,
                           images.TILE_SIZE*self.height)

    def boxAt(self, x, y):
        """ Return the type of the box at coordinates (x, y). """
        return self.boxes[y][x]


def readmap(file):
    """A function that reads a map from a text file."""
    map_list = []
    tank_list = []

    with open(file, 'r') as file_handle:
        line = file_handle.readline()
        lstr = line.split()
        width = int(lstr[0])
        height = int(lstr[1])
        for i in range(height):
            line = file_handle.readline()
            lstr = line.split()
            lint = [int(elem) for elem in lstr]
            map_list.append(lint)
        while True:
            line = file_handle.readline()
            lstr = line.split()
            flag_list = []
            if len(lstr) == 2:
                flag_list = [float(elem) for elem in lstr]
                break
            lint = [float(elem) for elem in lstr]
            tank_list.append(lint)
    map = Map(width, height, map_list, tank_list, flag_list)
    return map


map0 = readmap("map0.txt")
map1 = readmap("map1.txt")
map2 = readmap("map2.txt")
