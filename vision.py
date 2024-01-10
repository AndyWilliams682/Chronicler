import numpy as np
import cv2
from math import floor, ceil
import pytesseract
from pathlib import Path
import matplotlib.pyplot as plt
import difflib


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
SUBMENU_TEXT_RANGE = ((0, 0, 53), (30, 17, 127))
INC_REM_TEXT_RANGE = ((0, 0, 104), (0, 4, 254))
ROOM_TEXT_RANGE = ((58, 64, 41), (74, 112, 228))
CONNECTION_RANGE = ((30, 43, 120), (30, 140, 255))

TESS_CONFIG = '-c tessedit_char_whitelist="01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz"'

with open("words.txt") as f:
    WORDS = f.read().split('\n')


def post_ocr_correction(raw_ocr):
    """
    Treating OCR output as raw data, requires some simple corrections
    """
    output = raw_ocr.upper()
    output = output.replace('\n', ' ') # Removing newlines between room words
    output = output.replace(')', '') # Removing closing ) from incursion submenu
    output = difflib.get_close_matches(output, WORDS, n=1)[0] # Spellcheck, may want to cache results
    return output


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
    # Assuming no contour will be larger than the rooms
    room_w_cutoff = 0.8 * max(box[2] for box in boundingBoxes)
    room_h_cuttof = 0.8 * max(box[3] for box in boundingBoxes)
    for bounding_box in boundingBoxes:
        idx += 1
        # Hard-coded values here may cause issues with smaller resolutions
        if bounding_box[2] < room_w_cutoff or bounding_box[3] < room_h_cuttof or hierarchy[0, idx, 3] != -1:
            continue
        room_boxes.append(bounding_box)

    return room_boxes


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
    left_region = get_text_mask(hsv_incursion_submenu[:, :floor(len(hsv_incursion_submenu[0]) / 2)], SUBMENU_TEXT_RANGE)
    right_region = get_text_mask(hsv_incursion_submenu[:, floor(len(hsv_incursion_submenu[0]) / 2):], SUBMENU_TEXT_RANGE)

    # Split by 'E TO ' to capture both 'CHANGE TO ' and 'UPGRADE TO '
    left_ocr = pytesseract.image_to_string(left_region, config='-c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz()\'" --psm 6')
    left_ocr = left_ocr.strip().replace('\n', ' ').split('E TO ')[1]
    right_ocr = pytesseract.image_to_string(right_region, config='-c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz()\'"--psm 6')
    right_ocr = right_ocr.strip().replace('\n', ' ').split('E TO ')[1]
    left_output = post_ocr_correction(left_ocr)
    right_output = post_ocr_correction(right_ocr)
    return  (left_output, right_output)


def read_incursions_remaining(hsv_incursions_remaining):
    """
    Reading X from "X Incursions Remaining"
    """
    text_mask = get_text_mask(hsv_incursions_remaining, INC_REM_TEXT_RANGE)
    inc_rem = pytesseract.image_to_string(text_mask, config='-c tessedit_char_whitelist="0123456789ACEGIMNORSU acegimnorsu" --psm 7').split(' ')[0]
    return int(post_ocr_correction(inc_rem))


def read_room_text(hsv_room, debug=False):
    text_mask = get_text_mask(hsv_room, ROOM_TEXT_RANGE, reduce_noise=True, debug=debug)

    ocr = pytesseract.image_to_string(text_mask, config='-c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz()\'" --psm 6 --user-words "C:\\Users\\andyw\\Documents\\Python Scripts\\IncursionReader\\TessConfig\\eng.user-words" --user-patterns "C:\\Users\\andyw\\Documents\\Python Scripts\\IncursionReader\\TessConfig\\eng.user-patterns"').strip()
    output = post_ocr_correction(ocr)

    if output == '':
        plt.imshow(text_mask)
        plt.show()

    return output


def connection_present(connection_hsv):
    connection_mask = cv2.inRange(connection_hsv, CONNECTION_RANGE[0], CONNECTION_RANGE[1])
    return 255 in connection_mask
