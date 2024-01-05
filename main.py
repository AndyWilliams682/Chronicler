from os import listdir, path
import cv2
import matplotlib.pyplot as plt
from math import floor, ceil
from Temple import Temple


# Assumes the menu takes up the same amount of space independent of resolution
MENU_LEFT_PERCENTAGE = 383 / 2560
MENU_RIGHT_PERCENTAGE = 2210 / 2560 # Subtract 35 from numerator for just the main menu
MENU_TOP_PERCENTAGE = 71 / 1440
MENU_BOTTOM_PERCENTAGE = 1183 / 1440


def crop_to_incursion_menu(image):
    """
    Function assumes that the Incursion menu takes up the same amount of relative space regardless of the image resolution.
    Crops based on hand-picked constants from 1440p resolution.
    """
    top_crop = floor(MENU_TOP_PERCENTAGE * image.shape[0])
    bottom_crop = ceil(MENU_BOTTOM_PERCENTAGE * image.shape[0])
    left_crop = floor(MENU_LEFT_PERCENTAGE * image.shape[1])
    right_crop = ceil(MENU_RIGHT_PERCENTAGE * image.shape[1])
    return image[top_crop:bottom_crop, left_crop:right_crop]


if __name__ == '__main__':
    plt_rows = 2
    plt_cols = 2
    total_plots = plt_rows * plt_cols

    folder_dir = r'Images\1440pNvidia'

    for filename in listdir(folder_dir):
        print(filename)
        path_to_image = path.join(folder_dir, filename)
        image = cv2.imread(path_to_image)[..., ::-1] # RGB
        image = crop_to_incursion_menu(image)
        hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        test = Temple(hsv_image)
        print(test)
        print()
