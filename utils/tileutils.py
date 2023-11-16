import bpy
import os
import math
from .helpers import GetActionFrameCount, GetTilePos

def CeilToMultiple(number, multiple):
    return multiple * math.ceil(float(number) / float(multiple))

def PasteImage(target, source, posx, posy, spritesheet_height):
    target_pixels = list(target.pixels)
    source_pixels = list(source.pixels)
    width = source.size[0]
    height = source.size[1]

    # Adjust posy to start from the bottom of the target image
    posy = spritesheet_height - posy - height

    if posy < 0 or posx + width > target.size[0] or posy + height > target.size[1]:
        raise ValueError("Attempting to paste image out of the bounds of the target spritesheet.")

    for Y in range(height):
        for X in range(width):
            sp = (X + Y * width) * source.channels
            tp = ((X + posx) + (Y + posy) * target.size[0]) * target.channels

            for C in range(min(source.channels, target.channels)):
                target_pixels[tp + C] = source_pixels[sp + C]

    target.pixels = target_pixels
    target.update()

def TilePathsIntoImage(spritesheet_name_string, image_path_list, width, height):
    # create spritesheet image
    spritesheet = None


    print("Building pritesheet: %s" % spritesheet_name_string)
    # check if sprite sheet exists
    if spritesheet_name_string in bpy.data.images:
        spritesheet = bpy.data.images[spritesheet_name_string]

        print("Existing pritesheet res: %s %s" % (spritesheet.resolution[0],spritesheet.resolution[1]))
        if spritesheet.resolution[0] != width or spritesheet.resolution[1] != height:
            print("Spritesheet resolution changed, re-creating") 
            bpy.data.images.remove(spritesheet)
            spritesheet = bpy.data.images.new(spritesheet_name_string, width, height, alpha=True)

    else:
        # else create it

        print("Creating new spritesheet: %s" % spritesheet_name_string)
        spritesheet = bpy.data.images.new(spritesheet_name_string, width, height, alpha=True)

    # load sprites and append into sheet

    print("Spritesheet res: %s %s" % (spritesheet.resolution[0],spritesheet.resolution[1]))
    for i in range(len(image_path_list)):

        # locals
        path = image_path_list[i]
        img = None

        # try to load image into blender
        try:
            img = bpy.data.images.load(path)
        except:
            raise NameError("Cannot load image %s" % path)

        posX, posY = GetTilePos(img.size[0], img.size[1], spritesheet.size[0], spritesheet.size[1], i)
        PasteImage(spritesheet, img, posX, posY, spritesheet.size[1])

        bpy.data.images.remove(img)

    return spritesheet
