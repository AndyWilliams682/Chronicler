import numpy as np
import cv2
from math import floor, ceil
import pytesseract
from pathlib import Path
import matplotlib.pyplot as plt
import difflib
import json

from temple_layout import ROOMS_PER_LAYER
from constants import ROOM_DATA


PATH_TO_POPPLER_EXE = Path(r"C:\Program Files\poppler-0.68.0\bin")
pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

# Assumes a fixed range of colors for each of the room borders in the temple layout
ROOM_BORDER_RANGES = {
    # Old Obstructed (15, 167, 99), (15, 167, 99)
    'Obstructed': ((15, 167, 99), (15, 167, 99)), # Min / Max for each in HSV
    # Old Open ((15, 151, 204), (15, 151, 204))
    # New Open ((9, 45, 157), (66, 151, 206)), Steam screenshot compression causing issues
    'Open': ((15, 151, 204), (15, 151, 204)),
    'Chosen': ((17, 126, 240), (27, 166, 255))
}

# HSV ranges for isolating other elements in the menu
SUBMENU_OPTION_TEXT_RANGE = ((0, 0, 53), (30, 17, 127))
SUBMENU_CHOSEN_TEXT_RANGE = ((71, 81, 112), (73, 88, 228))
INC_REM_TEXT_RANGE = ((0, 0, 104), (0, 4, 254))
ROOM_TEXT_RANGE = ((58, 64, 41), (74, 112, 228))
CONNECTION_RANGE = ((30, 43, 120), (30, 140, 255))

TESS_CONFIG = '-c tessedit_char_whitelist="01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz"'

with open(r"src\words.txt") as f:
    WORDS = f.read().split('\n')


def post_ocr_correction(raw_ocr):
    """
    Treating OCR output as raw data, requires some simple corrections
    """
    output = raw_ocr.upper()
    output = output.replace('\n', ' ') # Removing newlines between room words
    output = output.replace(')', '') # Removing closing ) from incursion submenu
    output = difflib.get_close_matches(output, WORDS, n=1)[0] # Spellcheck, may want to cache results?
    return output


def process_screenshot(screenshot, image_params, previous = None, attempts = 0):
    if screenshot.shape[-1] == 4: # Alpha channel present
        screenshot = np.array(screenshot)[..., :-1] # Removing alpha channel
    hsv_image = screenshot[..., ::-1] # BGR to RGB
    # screenshot = crop_to_incursion_menu(screenshot) # Don't think this is needed anymore
    hsv_image = cv2.cvtColor(hsv_image, cv2.COLOR_RGB2HSV)
    if image_params["cached"] == 0 or attempts == 1:
        image_params = get_image_parameters(hsv_image)
    try: # If the cache fails for some reason
        return image_params, read_image_using_saved_params(hsv_image, image_params, previous)
    except ValueError: # Try from scratch
        if attempts == 1:
            raise ValueError("Failed to process screenshot.")
        return process_screenshot(screenshot, image_params, attempts = attempts + 1)


def get_room_boxes(hsv_menu_image):
    """
    Function assumes that the room border color is fixed with respect to its status (Open/Obstructed/Chosen).
    Identifies the room boundaries in the temple by checking if the colors are within range for each room status.
    Using contours, filters out boxes that are too small, or that are children of another box.
    Remaining boxes are kept and stored in a list.
    """
    mask = np.full((hsv_menu_image.shape[0], hsv_menu_image.shape[1]), 0, dtype=np.uint8)
    for room_status, border_range in ROOM_BORDER_RANGES.items():
        mask = cv2.add(mask, cv2.inRange(hsv_menu_image, border_range[0], border_range[1]))

    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    boundingBoxes = [cv2.boundingRect(contour) for contour in contours]
    
    room_boxes = []
    idx = -1
    # Assuming no contour will be larger than the rooms, we use the max
    room_w_cutoff = 0.8 * max(box[2] for box in boundingBoxes)
    room_h_cuttof = 0.8 * max(box[3] for box in boundingBoxes)
    for bounding_box in boundingBoxes:
        idx += 1
        if bounding_box[2] < room_w_cutoff or bounding_box[3] < room_h_cuttof or hierarchy[0, idx, 3] != -1:
            continue
        room_boxes.append(bounding_box)

    if len(room_boxes) != 13:
        # Add error logging stuff here
        raise ValueError(f"Expected 13 room boxes, got {len(room_boxes)}")
    
    return room_boxes


def get_image_parameters(hsv_image):
    output = {
        "room_details": {},
        "slots_to_xy": {},
        "incursion_menu_rect": {},
        "incursions_remaining_rect": {}
    }

    # Rectangles that define the outlines of each room
    room_boxes = get_room_boxes(hsv_image) # A list of (x, y, w, h) tuples
    
    # Average room dimensions (excluding the chosen room)
    average_room_height = ceil((sum(room[3] for room in room_boxes) - min(room[3] for room in room_boxes)) / (len(room_boxes) - 1))
    average_room_width = ceil((sum(room[2] for room in room_boxes) - min(room[2] for room in room_boxes)) / (len(room_boxes) - 1))

    # Average gap between normal (non-chosen) rooms
    horizontal_gap = abs(room_boxes[-3][0] - room_boxes[-2][0]) - average_room_width
    if average_room_height - room_boxes[-3][3] > 1 or average_room_height - room_boxes[-2][3] > 1: # Checking if either room in layer 3 is chosen
        horizontal_gap = abs(room_boxes[-5][0] - room_boxes[-4][0]) - average_room_width # Using rooms 2F0 and 2F1 instead of 3F0 and 3F1 for accurate gap
    vertical_gap = min(room_boxes[-2][1], room_boxes[-3][1]) - room_boxes[-1][1] - average_room_height # Provides consistency if 3F0 or 3F1 are chosen

    output["room_details"]["room_width"] = average_room_width
    output["room_details"]["room_height"] = average_room_height
    output["room_details"]["horizontal_gap"] = horizontal_gap
    output["room_details"]["vertical_gap"] = vertical_gap
    
    # Important reference points/lengths for the temple
    temple_layer_h = average_room_height + vertical_gap
    temple_apex_y = min(room[1] for room in room_boxes) - floor(vertical_gap / 2) # Apex y is the minumum y for the temple
    layer_room_w = average_room_width + horizontal_gap
    temple_leftmost_x = min(room[0] for room in room_boxes) - floor(horizontal_gap / 2) # x value of furthest left room
    layer_leftmost_x = temple_leftmost_x
    
    prev_layer = -1
    for room in room_boxes:
        x, y, w, h = room
        room_layer = 4 - round((y - temple_apex_y) / temple_layer_h)
        if room_layer == prev_layer + 1:
            prev_layer = room_layer
            layer_leftmost_x = temple_leftmost_x + (4 - ROOMS_PER_LAYER[room_layer]) * (1 / 2) * (average_room_width + horizontal_gap)

        room_diag = ROOMS_PER_LAYER[room_layer] - round((x - layer_leftmost_x) / layer_room_w) - 1 + (room_layer == 0)
        room_slot = f"{room_layer}F{room_diag}"
        
        # The chosen room has a smaller box than the typical room, so it is easy to catch here
        if average_room_height - h > 1:
            y -= ceil((average_room_height - h) / 2)
            # x -= ceil((average_room_width - w) / 2) # Assume this is not needed
        
        output["slots_to_xy"][room_slot] = {}
        output["slots_to_xy"][room_slot]["x"] = x
        output["slots_to_xy"][room_slot]["y"] = y 

    # Reference points/lengths for the incursion submenu (top right corner of Temple screen)
    output["incursion_menu_rect"]["x"] = floor(room_boxes[-1][0] + (3 / 2) * average_room_width + horizontal_gap) # Fixed distance from Apex x
    output["incursion_menu_rect"]["y"] = ceil(average_room_height / 2)
    output["incursion_menu_rect"]["w"] = floor(0.65 * (len(hsv_image[0]) - output["incursion_menu_rect"]["x"])) # Difference from max x and submenu x
    output["incursion_menu_rect"]["h"] = room_boxes[-1][1] + ceil((3 / 2) * average_room_height) + vertical_gap # Fixed distance from Apex y, since this starts at y = 0

    # Reference points/lengths for the incursions remaining (near the bottom of the Temple screen)
    output["incursions_remaining_rect"]["x"] = room_boxes[-1][0] - horizontal_gap
    output["incursions_remaining_rect"]["y"] = room_boxes[-1][1] + 5 * (average_room_height + vertical_gap)
    output["incursions_remaining_rect"]["w"] = 2 * horizontal_gap + average_room_width
    output["incursions_remaining_rect"]["h"] = average_room_height

    output["cached"] = 1

    return output


def reset_saved_params():
    with open(r'src\image_params.json', 'w') as f:
        json.dump({"cached": 0}, f, indent=4)


def read_image_using_saved_params(hsv_image, cache, previous = None):
    # TODO: Image may not contain this, what to do then?
    remaining_x = cache["incursions_remaining_rect"]["x"]
    remaining_y = cache["incursions_remaining_rect"]["y"]
    remaining_w = cache["incursions_remaining_rect"]["w"]
    remaining_h = cache["incursions_remaining_rect"]["h"]
    incursions_remaining_hsv = hsv_image[remaining_y:remaining_y + remaining_h, remaining_x:remaining_x + remaining_w]
    incursions_remaining = read_incursions_remaining(incursions_remaining_hsv)
    
    continuous = False
    if previous is not None:
        continuous = (previous["remaining"] - incursions_remaining) == 1

    # TODO: What if the image doesn't have these?
    incursion_x = cache["incursion_menu_rect"]["x"]
    incursion_y = cache["incursion_menu_rect"]["y"]
    incursion_w = cache["incursion_menu_rect"]["w"]
    incursion_h = cache["incursion_menu_rect"]["h"]
    incursion_menu_hsv = hsv_image[incursion_y:incursion_y + incursion_h, incursion_x:incursion_x + incursion_w]
    incursion_data = read_incursion_submenu(incursion_menu_hsv)

    average_room_width = cache["room_details"]["room_width"]
    average_room_height = cache["room_details"]["room_height"]
    horizontal_gap = cache["room_details"]["horizontal_gap"]
    vertical_gap = cache["room_details"]["vertical_gap"]
    directions = {-1: "/", 0: "—", 1: "\\"}
    
    layout_data = {}
    for slot in cache["slots_to_xy"]:
        if continuous and slot != previous["slot"]:
            continue
        layout_data[slot] = {"Name": None, "Connections": []}
        layer = int(slot[0])
        diag = int(slot[-1])
        x = cache["slots_to_xy"][slot]["x"]
        y = cache["slots_to_xy"][slot]["y"]
        room_image = hsv_image[y + round(0.4 * average_room_height):y + average_room_height, x:x + average_room_width]
        layout_data[slot]["Name"] = read_room_text(room_image)
        
        # Only checks for connections on the left-side of the room. This ensures each connection is only read once.
        left_connection_hsv = hsv_image[y - vertical_gap:y + average_room_height + vertical_gap, x - horizontal_gap:x + round(average_room_width / 2)]
        left_connection_hsv[vertical_gap:average_room_height + vertical_gap, horizontal_gap:round(average_room_width / 2) + horizontal_gap] = (0, 0, 0)
        connection_ys = [0, vertical_gap, average_room_height + vertical_gap, average_room_height + 2 * vertical_gap]
        direction = -2
        for region_idx in range(len(connection_ys) - 1):
            region_idx = len(connection_ys) - region_idx - 1
            direction += 1
            if connection_present(left_connection_hsv[connection_ys[region_idx - 1]:connection_ys[region_idx]]):
                layout_data[slot]["Connections"].append(directions[direction])
        
        # Need to check the right side if only reading one slot
        if continuous:
            right_connection_hsv = hsv_image[y - vertical_gap:y + average_room_height + vertical_gap, x + round(average_room_width / 2):x + average_room_width + horizontal_gap]
            right_connection_hsv[vertical_gap:average_room_height + vertical_gap, horizontal_gap:round(average_room_width / 2) + horizontal_gap] = (0, 0, 0)
            connection_ys = [0, vertical_gap, average_room_height + vertical_gap, average_room_height + 2 * vertical_gap]
            direction = -2
            for region_idx in range(len(connection_ys) - 1):
                region_idx = len(connection_ys) - region_idx - 1
                direction += 1
                if connection_present(right_connection_hsv[connection_ys[region_idx - 1]:connection_ys[region_idx]]):
                    layout_data[slot]["Connections"].append("r" + directions[direction])

    output = {"layout": layout_data, "incursion": incursion_data, "remaining": incursions_remaining}
    
    return output


def get_text_mask(hsv_image, text_hsv_range, reduce_noise=False, debug=False):
    """
    Using a text_hsv_range, isolates text in the image. Performs morphological operations to enhance readability and reduce noise.
    """
    
    font_mask = cv2.inRange(hsv_image, text_hsv_range[0], text_hsv_range[1])
    x, y, w, h = cv2.boundingRect(font_mask)
    font_mask = font_mask[y:y+h, x:x+w]
    # Some rooms have the font colors in their art, which appear as noise
    # Opening reduces the severity of that noise
    opening_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    opening = cv2.morphologyEx(font_mask, cv2.MORPH_OPEN, opening_kernel)
    
    # Dilation along this kernel blends the text together into blobs
    dilation_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    dilation = cv2.dilate(opening, dilation_kernel, iterations=2)

    # For debugging / testing
    # fig, axs = plt.subplots(2, 2, figsize=(10, 6), layout='constrained')
    # axs[0, 1].imshow(dilation, cmap='gray')

    # Trimming some blobs that are obviously too small for any text
    # May not ultimately be needed with the following step
    if reduce_noise is True:
        cnts, H = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            box_x, box_y, box_w, box_h = cv2.boundingRect(c)
            ar = box_w / float(box_h)
            # Could also do an aspect ratio check (smallest acceptable would be PITS)
            if box_h < 0.2 * h:
                cv2.drawContours(dilation, [c], -1, (0, 0, 0), -1)
    
    # Scanning from the bottom of the region until a cutoff is reached
    # Scanning will stop after both conditions are met:
    # 1) Reaching an empty row (This assumes noise blobs do not touch the text blob)
    # 2) Accounting for 70% of the white pixels in the region (This assumes the text is primarily at the bottom)
    running_total = 0
    all_pixels = np.sum(dilation / 255)
    for row_cutoff in range(len(dilation)):
        row_cutoff = len(dilation) - row_cutoff - 1
        row_sum = np.sum(dilation[row_cutoff] / 255)
        running_total += row_sum
        if row_sum == 0 and running_total >= 0.7 * all_pixels:
            break
    
    # Only keep original text within the blobs in the cutoff region
    result = 255 - cv2.bitwise_and(dilation[row_cutoff:], font_mask[row_cutoff:])
    
    # Padding the text with empty space helps remove some edge-errors
    border_size = 10
    result = cv2.copyMakeBorder(
        result,
        top=border_size,
        bottom=border_size,
        left=border_size,
        right=border_size,
        borderType=cv2.BORDER_CONSTANT,
        value=[255, 255, 255]
    )

    result = cv2.resize(result, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)

    # For debugging / testing
    if debug:
        fig, axs = plt.subplots(2, 2, figsize=(10, 6), layout='constrained')
        axs[0, 0].imshow(hsv_image)
        axs[0, 1].imshow(opening, cmap='gray')
        axs[1, 0].imshow(dilation, cmap='gray')
        axs[1, 1].imshow(result, cmap='gray')
        plt.show()
    return result


def read_incursion_submenu(hsv_incursion_submenu):
    """
    The incursion submenu is the upper-right corner of the temple menu, which details the different room options for that incursion.
    Typically, going right (up) will upgrade the current room (if possible), while going left will swap to a tier 1 room of a different theme.
    """
    left_region = get_text_mask(hsv_incursion_submenu[:, :floor(len(hsv_incursion_submenu[0]) / 2)], SUBMENU_OPTION_TEXT_RANGE)
    right_region = get_text_mask(hsv_incursion_submenu[:, floor(len(hsv_incursion_submenu[0]) / 2):], SUBMENU_OPTION_TEXT_RANGE)
    top_region = get_text_mask(hsv_incursion_submenu[:floor(len(hsv_incursion_submenu) / 5), :], SUBMENU_CHOSEN_TEXT_RANGE)

    # Split by 'E TO ' to capture both 'CHANGE TO ' and 'UPGRADE TO '
    left_ocr = pytesseract.image_to_string(left_region, config='-c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz()\'" --psm 6')
    left_ocr = left_ocr.strip().replace('\n', ' ').split('E TO ')[1]
    left_output = post_ocr_correction(left_ocr)

    right_ocr = pytesseract.image_to_string(right_region, config='-c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz()\'"--psm 6')
    right_ocr = right_ocr.strip().replace('\n', ' ').split('E TO ')[1]
    right_output = post_ocr_correction(right_ocr)

    top_ocr = pytesseract.image_to_string(top_region, config='-c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz()\'"--psm 6')
    top_ocr = top_ocr.strip().replace('\n', ' ')
    top_output = post_ocr_correction(top_ocr)

    return  {"room": top_output, "left_option": left_output, "right_option": right_output}


def read_incursions_remaining(hsv_incursions_remaining):
    """
    Reading X from "X Incursions Remaining"
    """
    text_mask = get_text_mask(hsv_incursions_remaining, INC_REM_TEXT_RANGE)
    inc_rem = pytesseract.image_to_string(text_mask, config='-c tessedit_char_whitelist="0123456789ACEGIMNORSU acegimnorsu" --psm 7').split(' ')[0]
    
    inc_rem = post_ocr_correction(inc_rem)
    
    try:
        return int(inc_rem)
    except ValueError:
        # Add logging here
        raise ValueError(f"Incursions remaining was not an integer, got {inc_rem}")


def read_room_text(hsv_room, debug=False):
    text_mask = get_text_mask(hsv_room, ROOM_TEXT_RANGE, reduce_noise=True, debug=False)

    ocr = pytesseract.image_to_string(text_mask, config='-c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz()\'" --psm 6 --user-words "C:\\Users\\andyw\\Documents\\Python Scripts\\IncursionReader\\TessConfig\\eng.user-words" --user-patterns "C:\\Users\\andyw\\Documents\\Python Scripts\\IncursionReader\\TessConfig\\eng.user-patterns"').strip()
    output = post_ocr_correction(ocr)

    if output == '':
        plt.imshow(text_mask)
        plt.show()
    
    if output not in ROOM_DATA.index:
        # read_room_text(hsv_room, debug=True)
        # Add logging here
        raise ValueError(f"Room not found, got {output} instead")

    return output


def connection_present(connection_hsv):
    connection_mask = cv2.inRange(connection_hsv, CONNECTION_RANGE[0], CONNECTION_RANGE[1])
    return 255 in connection_mask


def shortcut(screenshot, slot):
    with open(r"src\image_params.json") as f:
        cache = json.load(f)
    
    slot_data = {"Name": "", "Connections": []}
    layer = int(slot[0])
    diag = int(slot[-1])
    directions = {-1: "/", 0: "—", 1: "\\"}
    
    if screenshot.shape[-1] == 4: # Alpha channel present
        screenshot = np.array(screenshot)[..., :-1] # Removing alpha channel
    screenshot = screenshot[..., ::-1] # BGR to RGB
    # screenshot = crop_to_incursion_menu(screenshot) # Don't think this is needed anymore
    hsv_image = cv2.cvtColor(screenshot, cv2.COLOR_RGB2HSV)
    # Need to make it read the room text and check connections twice and read the submenu and remaining
    average_room_width = cache["room_details"]["room_width"]
    average_room_height = cache["room_details"]["room_height"]
    horizontal_gap = cache["room_details"]["horizontal_gap"]
    vertical_gap = cache["room_details"]["vertical_gap"]
    x = cache["slots_to_xy"][slot]["x"]
    y = cache["slots_to_xy"][slot]["y"]
    room_image = hsv_image[y + round(0.4 * average_room_height):y + average_room_height, x:x + average_room_width]
    slot_data["Name"] = read_room_text(room_image)

    room_connection_hsv = hsv_image[y - vertical_gap:y + average_room_height + vertical_gap, x - horizontal_gap:x + round(average_room_width / 2)]
    room_connection_hsv[vertical_gap:average_room_height + vertical_gap, horizontal_gap:round(average_room_width / 2) + horizontal_gap] = (0, 0, 0)
    connection_ys = [0, vertical_gap, average_room_height + vertical_gap, average_room_height + 2 * vertical_gap]
    direction = -2
    for region_idx in range(len(connection_ys) - 1):
        region_idx = len(connection_ys) - region_idx - 1
        direction += 1
        # Only checks for a connection if there is another room to connect to in that direction from the current room
        # Ex: There cannot be rooms below the lowest layer, so that direction is not checked for layer 0
        if ((direction == -1 and layer > 0 and diag < 3) or \
            (direction == 0 and diag < ROOMS_PER_LAYER[layer] - 1 + (layer == 0)) or \
            (direction == 1 and (layer == 0 or diag < ROOMS_PER_LAYER[layer] - 1))) and \
            connection_present(room_connection_hsv[connection_ys[region_idx - 1]:connection_ys[region_idx]]):
                slot_data["Connections"].append(directions[direction])

    for region_idx in range(len(connection_ys) - 1):
        region_idx = len(connection_ys) - region_idx - 1
        direction += 1
        # Only checks for a connection if there is another room to connect to in that direction from the current room
        # Ex: There cannot be rooms below the lowest layer, so that direction is not checked for layer 0
        if ((direction == -1 and layer > 0 and diag < 3) or \
            (direction == 0 and diag < ROOMS_PER_LAYER[layer] - 1 + (layer == 0)) or \
            (direction == 1 and (layer == 0 or diag < ROOMS_PER_LAYER[layer] - 1))) and \
            connection_present(room_connection_hsv[connection_ys[region_idx - 1]:connection_ys[region_idx]]):
                slot_data["Connections"].append(directions[direction])
    
    # TODO: What if the image doesn't have these?
    incursion_x = cache["incursion_menu_rect"]["x"]
    incursion_y = cache["incursion_menu_rect"]["y"]
    incursion_w = cache["incursion_menu_rect"]["w"]
    incursion_h = cache["incursion_menu_rect"]["h"]
    incursion_menu_hsv = hsv_image[incursion_y:incursion_y + incursion_h, incursion_x:incursion_x + incursion_w]
    incursion_data = read_incursion_submenu(incursion_menu_hsv)

    # TODO: Or these?
    remaining_x = cache["incursions_remaining_rect"]["x"]
    remaining_y = cache["incursions_remaining_rect"]["y"]
    remaining_w = cache["incursions_remaining_rect"]["w"]
    remaining_h = cache["incursions_remaining_rect"]["h"]
    incursions_remaining_hsv = hsv_image[remaining_y:remaining_y + remaining_h, remaining_x:remaining_x + remaining_w]
    incursions_remaining = read_incursions_remaining(incursions_remaining_hsv)

    output = {"slot": slot_data, "incursion": incursion_data, "remaining": incursions_remaining}


if __name__ == "__main__":
    # reset_saved_params()
    import time
    image = cv2.imread(r"tests\Images\CompleteTemple.png")
    start = time.time()
    output = process_screenshot(image)
    end = time.time()
    print(end - start)
    print(output)
    start = time.time()
    slot = "0F1"
    output = process_screenshot(image, {"slot": "0F1", "remaining": 2})
    end = time.time()
    print(end - start)
    print(output)
