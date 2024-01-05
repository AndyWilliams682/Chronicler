import numpy as np
import cv2
from math import floor, ceil
import pytesseract
from pathlib import Path
import matplotlib.pyplot as plt


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
    'Chosen': ((17, 126, 242), (27, 165, 255))
}

# HSV ranges for isolating other elements in the menu
SUBMENU_TEXT_RANGE = ((0, 0, 54), (30, 9, 127))
INC_REM_TEXT_RANGE = ((0, 0, 104), (0, 4, 254))
ROOM_TEXT_RANGE = ((58, 64, 41), (73, 112, 228))
CONNECTION_RANGE = ((30, 43, 120), (30, 140, 255))


def post_ocr_correction(raw_ocr, is_number=False):
    """
    Treating OCR output as raw data, requires some simple corrections
    """
    output = raw_ocr.replace('’', '\'') # Surveyor's Study
    output = output.replace('\n', ' ') # Hybridisation Chamber / Gemcutter's Workshop
    output = output.replace('(;', 'G') # Glittering Halls
    output = output.replace(' LI', ' U') # Sanctum of Unity
    output = output.replace(' $', '\'S') # Gemcutter's Workshop / Jeweller's Workshop
    output = output.replace('I S', 'I\'S') # Doryani's Institute

    output = output.replace(')', '') # Removing closing ) from incursion submenu
    output = output.replace('}', '') # Removing closing } from incursion submenu
    output = output.replace('FALL', 'HALL') # Hall of Offerings from incursion submenu

    if is_number: # Corrections for X in "X Incursions Remaining"
        output = output.replace('17', '12')
        output = output.replace('S', '8')
        output = output.replace('b', '6')
        output = output.replace('58', '5')

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

    fig, axs = plt.subplots(1, 2)
    axs[0].imshow(hsv_menu_image)
    axs[1].imshow(mask)
    plt.show()
    exit()
    
    room_boxes = []
    idx = -1
    for bounding_box in boundingBoxes:
        idx += 1
        if bounding_box[2] < 90 or bounding_box[3] < 90 or hierarchy[0, idx, 3] != -1:
            continue
        room_boxes.append(bounding_box)

    return room_boxes


def get_text_mask(hsv_image, text_hsv_range, reduce_noise=False):
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
            x, y, w, h = cv2.boundingRect(c)
            ar = w / float(h)
            if h < 15:
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

    # For debugging / testing
    # if text_hsv_range == INC_REM_TEXT_RANGE:
    #     fig, axs = plt.subplots(2, 2, figsize=(10, 6), layout='constrained')
    #     axs[0, 0].imshow(hsv_image)
    #     axs[0, 1].imshow(opening, cmap='gray')
    #     axs[1, 0].imshow(dilation, cmap='gray')
    #     axs[1, 1].imshow(result, cmap='gray')
    #     plt.show()
    return result


def read_incursion_submenu(hsv_incursion_submenu):
    """
    The incursion submenu is the upper-right corner of the temple menu, which details the different room options for that incursion.
    Typically, going right (up) will upgrade the current room (if possible), while going left will swap to a tier 1 room of a different theme.
    """
    text_mask = get_text_mask(hsv_incursion_submenu, SUBMENU_TEXT_RANGE)
    left_region = text_mask[:, :floor(len(text_mask[0]) / 2)]
    right_region = text_mask[:, floor(len(text_mask[0]) / 2):]
    # Split by 'E TO ' to capture both 'CHANGE TO ' and 'UPGRADE TO '
    left_ocr = pytesseract.image_to_string(left_region, config='--psm 6').strip().replace('\n', ' ').split('E TO ')[1].upper()
    right_ocr = pytesseract.image_to_string(right_region, config='--psm 6').strip().replace('\n', ' ').split('E TO ')[1].upper() # May want to move .upper() to post_ocr_correction
    left_output = post_ocr_correction(left_ocr)
    right_output = post_ocr_correction(right_ocr)
    return  (left_output, right_output)


def read_incursions_remaining(hsv_incursions_remaining):
    """
    Reading X from "X Incursions Remaining"
    """
    text_mask = get_text_mask(hsv_incursions_remaining, INC_REM_TEXT_RANGE)
    inc_rem = pytesseract.image_to_string(text_mask, config='--psm 7').split(' ')[0]
    return int(post_ocr_correction(inc_rem, is_number=True))


def read_room_text(hsv_room):
    text_mask = get_text_mask(hsv_room, ROOM_TEXT_RANGE, reduce_noise=True)

    ocr = pytesseract.image_to_string(text_mask, config='--psm 6').strip()
    output = post_ocr_correction(ocr)
    return post_ocr_correction(ocr)


def connection_present(connection_hsv):
    connection_mask = cv2.inRange(connection_hsv, CONNECTION_RANGE[0], CONNECTION_RANGE[1])
    return 255 in connection_mask
