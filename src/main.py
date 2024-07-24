from os import listdir, path, stat
import cv2
from math import ceil
import mss
import numpy as np
import pandas as pd
import keyboard as kb
import time
import tkinter as tk
import tkinter.filedialog as fd
import threading
import json
import pygetwindow as gw
import random
import pytesseract
import os

from src.temple import Temple
from src.vision import process_screenshot
from src.constants import ROOM_DATA, ARCHITECTS
from src.decisions import TIE_BREAKERS
from src.slot import Slot
from src.data import Settings


IMMERSIVE_BG = "#17120f"
IMMERSIVE_FG = "#cc9053"
CONTRAST_BG = "#f0f0f0"
CONTRAST_FG = "#000000"
BG_OPTIONS = {True: IMMERSIVE_BG, False: CONTRAST_BG}
FG_OPTIONS = {True: IMMERSIVE_FG, False: CONTRAST_FG}

with open(r"src\program_data.json") as f:
    SUPPORTED_LANGUAGES = list(json.load(f).keys())


class IncursionApp():
    def __init__(self):
        # Need to read from a config file

        with open(r"src\config.json") as f:
            self.config = json.load(f)
        
        self.settings = Settings.from_dict(self.config["settings"])
        
        # Get poe window info here
        self.configure_root()
        self.ui_vars = self.settings.to_tk_vars()

        self.last_file_change = None
        self.open_incursion = False
        self.previous_incursion = None
        self.show_settings_in_hideout = tk.BooleanVar(value=False)
        self.thread_running = False

        kb.add_hotkey(self.settings.screenshot_keybind, self.screenshot_keybind_pressed)
        self.program_data = load_program_data(self.settings.language)
        pytesseract.pytesseract.tesseract_cmd = self.settings.tesseract_exe_path
        
        if self.settings.show_settings_on_startup:
            self.create_settings_frame()
        
    def run(self):
        self.start_backend_thread()
        self.root.mainloop()
    
    def start_backend_thread(self):
        if self.settings.client_txt_path != "":
            self.thread_running = True
            self.backend_thread = threading.Thread(target=self.watch_client_txt)
            self.backend_thread.start()
    
    def configure_root(self):
        self.root = tk.Tk()
        self.root.configure(bg="")
        self.root.overrideredirect(True)
        self.root.wm_attributes('-topmost', True)
        self.root.withdraw()
    
    def create_settings_frame(self):
        self.root.geometry("")

        self.frame = tk.Frame(master=self.root) # TODO: IDK WHAT THE SIZE OF THIS SHOULD BE

        room_frame = tk.Frame(master=self.frame)
        room_frame.grid(row=0, column=1)

        count = 0
        col = 0
        tk.Label(master=room_frame, text=self.program_data["ui_labels"]["room_settings_text"]).grid(row=0, columnspan=2)
        for room in self.ui_vars["rooms"].keys():
            tk.Checkbutton(master=room_frame, text=room, variable=self.ui_vars["rooms"][room], onvalue=1, offvalue=0).grid(row=(count % 13) + 1, column=col, sticky="w")
            count += 1
            if count == 13:
                col += 1

        config_frame = tk.Frame(master=self.frame)
        config_frame.grid(row=0, column=0)

        exit_button = tk.Button(master=config_frame, text="EXIT PROGRAM", command=self.exit_program)
        exit_button.grid(row=0, column=0, sticky="w")

        language_dropdown = tk.OptionMenu(config_frame, self.ui_vars["language"], *SUPPORTED_LANGUAGES)
        language_dropdown.grid(row=1, columnspan=2)

        path_to_client_txt_button = tk.Button(master=config_frame, text=self.program_data["ui_labels"]["path_to_client_txt_text"], command=self.select_client_txt_path)
        path_to_client_txt_button.grid(row=2, column=0)

        path_to_tesseract_button = tk.Button(master=config_frame, text=self.program_data["ui_labels"]["path_to_tesseract_text"], command=self.select_tesseract_exe_path)
        path_to_tesseract_button.grid(row=2, column=1)

        screenshot_method_checkbox = tk.Checkbutton(master=config_frame, text=self.program_data["ui_labels"]["screenshot_method_text"], variable=self.ui_vars["screenshot_method_is_manual"], onvalue=1, offvalue=0)
        screenshot_method_checkbox.grid(row=3, columnspan=2)

        screenshot_keybind_label = tk.Label(master=config_frame, text=self.program_data["ui_labels"]["screenshot_keybind_text"])
        screenshot_keybind_label.grid(row=4, columnspan=2)

        self.screenshot_keybind_button = tk.Button(master=config_frame, text=self.ui_vars["screenshot_keybind"].get(), command=self.set_keybind_label)
        self.screenshot_keybind_button.grid(row=5, columnspan=2)

        show_tips_checkbox = tk.Checkbutton(master=config_frame, text=self.program_data["ui_labels"]["show_tips_text"], variable=self.ui_vars["show_tips"], onvalue=1, offvalue=0)
        show_tips_checkbox.grid(row=6, columnspan=2)

        show_settings_checkbox = tk.Checkbutton(master=config_frame, text=self.program_data["ui_labels"]["settings_startup_text"], variable=self.ui_vars["show_settings_on_startup"], onvalue=1, offvalue=0)
        show_settings_checkbox.grid(row=7, columnspan=2)

        save_and_close_settings_button = tk.Button(master=config_frame, text=self.program_data["ui_labels"]["save_and_close_text"], command = self.save_and_close_settings_frame)
        save_and_close_settings_button.grid(row=8, column=0)

        close_settings_button = tk.Button(master=config_frame, text=self.program_data["ui_labels"]["close_text"], command = self.close_settings_frame)
        close_settings_button.grid(row=8, column=1)

        self.frame.pack()
        self.root.deiconify()
    
    def save_and_close_settings_frame(self):
        try:
            old_keybind = self.settings.screenshot_keybind
            self.settings = Settings.from_tk_vars(self.ui_vars)
        except ValueError:
            return
        
        self.settings.cached = True
        
        if self.thread_running is False:
            self.start_backend_thread()
        
        kb.remove_hotkey(old_keybind)
        kb.add_hotkey(self.settings.screenshot_keybind, self.screenshot_keybind_pressed)
        pytesseract.pytesseract.tesseract_cmd = self.settings.tesseract_exe_path

        room_settings = pd.Series(self.settings.rooms)
        room_settings.index = room_settings.index.str.upper()
        ROOM_DATA["Valuable"] = room_settings
        with pd.option_context("future.no_silent_downcasting", True):
            ROOM_DATA["Valuable"] = ROOM_DATA["Valuable"].fillna(False).astype(bool)
            ARCHITECTS["Valuable"] = ROOM_DATA[["Theme", "Valuable"]][ROOM_DATA["Tier"] == 3].set_index("Theme")
        
        if TIE_BREAKERS[Slot(0, 4)] > 100 and self.settings.rooms["Apex of Atzoatl"]:
            TIE_BREAKERS[Slot(0, 4)] -= 100
        elif TIE_BREAKERS[Slot(0, 4)] < 100 and not self.settings.rooms["Apex of Atzoatl"]:
            TIE_BREAKERS[Slot(0, 4)] += 100

        self.config["settings"] = self.settings.__dict__
        save_config(self.config)
        self.program_data = load_program_data(self.settings.language)
        self.close_settings_frame()
    
    def close_settings_frame(self):
        self.frame.forget()
        self.root.withdraw()
    
    def select_client_txt_path(self):
        self.ui_vars["client_txt_path"].set(fd.askdirectory(mustexist=True) + "/client.txt")
    
    def select_tesseract_exe_path(self):
        self.ui_vars["tesseract_exe_path"].set(fd.askdirectory(mustexist=True) + "/tesseract.exe")
    
    def set_keybind_label(self):
        keybind = kb.read_hotkey()
        kb.stash_state()
        self.screenshot_keybind_button.config(text=keybind)
        self.ui_vars["screenshot_keybind"].set(keybind)
    
    def create_temple_frame(self, choose_left, choose_swap, leave_early, rooms_to_connect, map_area_level):
        self.label_bg = BG_OPTIONS[self.settings.immersive_ui]
        self.label_fg = FG_OPTIONS[self.settings.immersive_ui]

        self.root.geometry("")
        # need to add poe_window x, y, w, h to params. Need to use a library to get the window.
        # May need to modify the way the screenshot is taken to only get the window and not the whole monitor
        self.frame = tk.Frame(master=self.root, width=2560, height=1440, bg="", highlightbackground="white", highlightthickness=10)

        self.frame.bind("<Button>", self.exit_temple_frame) # TODO: Figure out how to close the overlay upon any interaction that closes the V menu

        self.add_incursion_choice_label(choose_left, choose_swap)
        if self.settings.show_tips:
            self.add_tip_label()
        self.add_leave_door_label(leave_early, rooms_to_connect, map_area_level)
        self.add_metrics_frame()

        self.frame.pack()
        self.root.deiconify()
   
    def add_incursion_choice_label(self, choose_left, choose_swap):
        x_div = 7

        text = self.program_data["ui_labels"]["swap_text"]
        if choose_swap is False:
            text = self.program_data["ui_labels"]["upgrade_text"]
       
        # How big should the font be?
        self.choice_label = tk.Label(master=self.frame, text=text, font=("Arial", 25), bg=self.label_bg, fg=self.label_fg) # TODO: WSTNB?

        label_y = self.config["image_params"]["incursion_menu_rect"]["y"] + self.config["image_params"]["incursion_menu_rect"]["h"] / 2 # TODO: WSTNB?
        label_y -= self.choice_label.winfo_reqheight() / 2
        label_y = ceil(label_y)

        label_x = self.config["image_params"]["incursion_menu_rect"]["x"] + self.config["image_params"]["incursion_menu_rect"]["w"] / x_div
        if choose_left is False:
            label_x += (x_div - 2) * self.config["image_params"]["incursion_menu_rect"]["w"] / x_div
        label_x -= self.choice_label.winfo_reqwidth() / 2
        label_x = ceil(label_x)

        self.choice_label.place(x=label_x, y=label_y)
   
    def add_tip_label(self):
        text = random.choice(self.program_data["tips"])
        # text = "This is a placeholder, but we will have a random set of tips in a list somewhere"
        self.tip_label = tk.Label(master=self.frame, text=text, font=("Arial", 18), bg=self.label_bg, fg=self.label_fg)
        label_x = self.config["image_params"]["incursions_remaining_rect"]["x"] + self.config["image_params"]["incursions_remaining_rect"]["w"] / 2
        label_y = self.config["image_params"]["incursions_remaining_rect"]["y"] + self.config["image_params"]["incursions_remaining_rect"]["h"]
        label_y = ceil(label_y)
        label_x -= self.tip_label.winfo_reqwidth() / 2
        label_x = ceil(label_x)
        self.tip_label.place(x=label_x, y=label_y)
   
    def add_leave_door_label(self, leave_early, rooms_to_connect, map_area_level):
        text = ""
        if len(rooms_to_connect) == 0 and leave_early is False:
            return

        if leave_early:
            text += self.program_data["ui_labels"]["skip_incursions_text"]
       
        if len(rooms_to_connect) > 0:
            if text != "":
                text += "\n\n"
            text += self.program_data["ui_labels"]["door_order_text"]
       
            count = 1
            for room in rooms_to_connect:
                text += f"\n{count}: {room}"
                count += 1
        
        text += f"\n\nIncursion Area Level must be >= {map_area_level}\n(to create a level 83 temple)"
       
        self.door_label = tk.Label(master=self.frame, text=text, font=("Arial", 14), bg=self.label_bg, fg=self.label_fg)
        label_y = self.config["image_params"]["incursion_menu_rect"]["y"] + self.config["image_params"]["incursion_menu_rect"]["h"]
        label_x = self.config["image_params"]["incursion_menu_rect"]["x"] + self.config["image_params"]["incursion_menu_rect"]["w"] / 2
        label_x = ceil(label_x)
        self.door_label.place(x=label_x, y=label_y)
    
    def add_metrics_frame(self):
        metrics_frame = tk.Frame(self.frame)
        label_y = self.config["image_params"]["incursion_menu_rect"]["y"]
        label_x = self.config["image_params"]["incursion_menu_rect"]["x"] - 2 * self.config["image_params"]["incursion_menu_rect"]["w"]
        label_x = ceil(label_x)
        metrics_frame.place(x=label_x, y=label_y)

        exit_button = tk.Button(master=metrics_frame, text="EXIT PROGRAM", command=self.exit_program)
        exit_button.pack()

        hideout_settings_checkbox = tk.Checkbutton(master=metrics_frame, text=self.program_data["ui_labels"]["settings_hideout_text"], variable=self.show_settings_in_hideout, onvalue=1, offvalue=0)
        hideout_settings_checkbox.pack()
    
    def exit_program(self):
        if self.thread_running is True:
            self.thread_running = False
            self.backend_thread.join()
        self.root.destroy()

    def exit_temple_frame(self, event):
        self.frame.forget()
        self.root.withdraw()
        win = gw.getWindowsWithTitle("Path of Exile")[0]
        win.activate()
        
    def watch_client_txt(self):
        """
        Monitoring client.txt for any changes
        """
        while self.thread_running:
            latest_change = stat(self.settings.client_txt_path).st_mtime
            if self.last_file_change != latest_change:
                self.last_file_change = latest_change
                self.read_client_txt()
    
    def read_client_txt(self):
        """
        Reading client.txt to check for Alva opening/finishing an Incursion.
        """
        with open(self.settings.client_txt_path, 'rb') as self.f:
            last_line = str(self.f.readlines()[-1])
            # May break if Client.txt does not track datetime with the setting turned off
            if any(quote in last_line for quote in self.program_data["alva_opening_incursion_quotes"]) and last_line.count(':') == 3:
                self.open_incursion = True
            elif any(quote in last_line for quote in self.program_data["alva_closing_incursion_quotes"]) and last_line.count(":") == 3:
                self.open_incursion = False
            elif self.program_data["hideout_line"] in last_line and last_line.count(":") == 2 and self.show_settings_in_hideout.get() is True:
                self.show_settings_in_hideout.set(False)
                self.create_settings_frame()
            self.f.close()
        self.f = None # Does this need to be self?
    
    def screenshot_keybind_pressed(self):
        if self.settings.screenshot_method_is_manual or self.open_incursion:
            self.take_screenshot()
    
    def take_screenshot(self):
        try:
            self.sct = mss.mss()
            monitor = self.sct.monitors[1]
            self.config["image_params"], image_output = process_screenshot(np.array(self.sct.grab(monitor)), self.config["image_params"])
            save_config(self.config)

            if self.previous_incursion is None:
                self.temple = Temple.from_vision_output(image_output)
            else:
                self.temple.update_slot_from_vision_output(image_output)

            self.previous_incursion = self.temple.get_previous_incursion()
            choose_left, choose_swap, leave_early, priority_doors, map_area_level = self.temple.make_decisions()
            self.create_temple_frame(choose_left, choose_swap, leave_early, priority_doors, map_area_level)
        except cv2.error:
            # Assume temple screen is not open
            pass


def save_config(config):
    with open(r'src\config.json', 'w') as f:
        json.dump(config, f, indent=4)

def load_program_data(language):
    with open(r"src\program_data.json") as f:
        return json.load(f)[language]


if __name__ == '__main__':
    client = IncursionApp()
    client.run()
    exit()

    # import matplotlib.pyplot as plt
    # image = cv2.imread(r"src\tests\Images\1440pNvidia\Path of Exile Screenshot 2023.12.20 - 18.03.00.67.png")
    # plt.imshow(image[56:56+506, 1563:1563+648])
    # plt.show()

    # Batch testing
    # count = 0
    # folder_dir = r'Images\Spencer'
    # for filename in listdir(folder_dir):
    #     count += 1
    #     print(filename, count)
    #     path_to_image = path.join(folder_dir, filename)
    #     image = cv2.imread(path_to_image)[..., ::-1] # RGB
    #     hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    #     test = Temple(hsv_image)
    #     print(test)
    #     print()