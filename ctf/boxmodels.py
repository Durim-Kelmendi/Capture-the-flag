"""
   The file contains a boxmodel class with two functions. One function contains
   information about the type of box, whether it can be moved, destroyed and
   the sprite. The other selects the model of a box.
"""

import images


class BoxModel:
    """
        This class defines a model of the box, it contains information on
        the type of box, whether it can be moved, destroyed and the sprite.
    """

    def __init__(self, sprite, movable, destructable):
        self.sprite         = sprite
        self.movable        = movable
        self.destructable   = destructable


woodbox  = BoxModel(images.woodbox,  movable=True, destructable=True)

metalbox = BoxModel(images.metalbox, movable=True, destructable=False)

rockbox  = BoxModel(images.rockbox, movable=False, destructable=False)


def get_model(type):
    """
        This function is used to select the model of a box in function of a
        number. It is mostly used when initializing the boxes from the
        information contained in the map.
    """
    if(type == 1):
        return rockbox
    elif(type == 2):
        return woodbox
    elif(type == 3):
        return metalbox
    else:
        return None
