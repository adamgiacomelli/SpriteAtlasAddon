def GetActionFrameCount(action, step=1):
    print("FC_s: ", action.frame_range[0])
    frame_start = int(action.frame_range[0])
    print("FC_e: ", action.frame_range[1])
    frame_end = int(action.frame_range[1])
    return ((frame_end - frame_start) // step) + 1

def GetTilePos(tile_width, tile_height, sheet_width, sheet_height, index):
    tiles_per_row = sheet_width // tile_width
    posX = (index % tiles_per_row) * tile_width
    posY = (index // tiles_per_row) * tile_height
    return (posX, posY)

def AutoImageSize(frame_width, frame_height, animations, rotations, step=1):
    # Find the longest animation by the number of frames
    max_frames = max(GetActionFrameCount(anim['action'], step) for anim in animations)
    # Calculate the width as the product of the longest animation length and frame width
    sheet_width = frame_width * max_frames
    # Calculate the height as the product of the number of rotations and frame height
    sheet_height = frame_height * rotations * len(animations)

    return (sheet_width, sheet_height)
