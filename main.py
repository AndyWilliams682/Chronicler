from os import listdir, path, stat
import cv2
import matplotlib.pyplot as plt
from math import floor, ceil
from Temple import Temple
import mss
import numpy as np
import keyboard as kb
import time


# Assumes the menu takes up the same amount of space independent of resolution
MENU_LEFT_PERCENTAGE = 383 / 2560
MENU_RIGHT_PERCENTAGE = 2210 / 2560 # Subtract 35 from numerator for just the main menu
MENU_TOP_PERCENTAGE = 71 / 1440
MENU_BOTTOM_PERCENTAGE = 1183 / 1440

CLIENT_TXT = r'C:\Program Files (x86)\Steam\steamapps\common\Path of Exile\logs\Client.txt'
INCURSION_KEYBIND = 'v'

# Assumes English, need support for other languages as well
ALVA_OPENING_INCURSION_QUOTES = [
    r"Alva, Master Explorer: Let's go.",
    r"Alva, Master Explorer: Time to go.",
    r"Alva, Master Explorer: It's time!"
]
ALVA_FINISHED_INCURSION_QUOTE = r"Alva, Master Explorer: Good job, exile."


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


class IncursionApp():
    def __init__(self):
        # Need to read from a config file
        self.path_to_client_txt = CLIENT_TXT
        self.incursion_keybind = INCURSION_KEYBIND
        
        self.last_file_change = 0
        self.sct = None
        self.f = None
    
    def run(self):
        # Setting up screenshotting
        with mss.mss() as self.sct:
            self.watch_client_txt()
    
    def watch_client_txt(self):
        """
        Monitoring client.txt for any changes
        """
        while True:
            latest_change = stat(self.path_to_client_txt).st_mtime
            if self.last_file_change != latest_change:
                self.last_file_change = latest_change
                self.read_client_txt()
    
    def read_client_txt(self):
        """
        Reading client.txt to check for Alva opening an Incursion.
        """
        with open(self.path_to_client_txt, 'rb') as self.f:
            last_line = str(self.f.readlines()[-1])
            # May break if Client.txt does not track datetime with the setting turned off
            if any(quote in last_line for quote in ALVA_OPENING_INCURSION_QUOTES) and last_line.count(':') == 3:
                self.wait_for_keybind()
            f.close()
    
    def wait_for_keybind(self):
        """
        Once the Incursion is open, watching for the relevant keybind that opens the Incursion menu, then a screenshot is taken.
        """
        while True: # Replace with reading the last line of the file for Alva End quote?
            if kb.is_pressed(self.incursion_keybind):
                time.sleep(0.25)
                monitor = self.sct.monitors[2]
                screenshot = np.array(self.sct.grab(monitor))[..., :-1] # Remove alpha channel
                screenshot = screenshot[..., ::-1] # BGR to RGB
                screenshot = crop_to_incursion_menu(screenshot)
                hsv_image = cv2.cvtColor(screenshot, cv2.COLOR_RGB2HSV)
                test = Temple(hsv_image)
                print(test)
                print()
                break


if __name__ == '__main__':
    client = IncursionApp()
    client.run()
    exit()

    # Batch testing
    # count = 0
    # folder_dir = r'Images\1440pNvidia'
    # for filename in listdir(folder_dir):
    #     count += 1
    #     print(filename, count)
    #     path_to_image = path.join(folder_dir, filename)
    #     image = cv2.imread(path_to_image)[..., ::-1] # RGB
    #     image = crop_to_incursion_menu(image)
    #     hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    #     test = Temple(hsv_image)
    #     # print(test)
    #     print()
