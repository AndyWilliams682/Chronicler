from dataclasses import dataclass, field
import tkinter as tk
import os
import keyboard as kb

from src.incursion import Incursion
from src.temple import Temple

@dataclass
class Settings:
    cached: bool = False
    language: str = "english"
    client_txt_path: str = ""
    tesseract_exe_path: str = ""
    show_tips: bool = True
    screenshot_method_is_manual: bool = False
    screenshot_keybind: str = "v"
    immersive_ui: bool = True
    show_settings_on_startup: bool = True
    rooms: dict = field(default_factory=lambda: {
            "Apex of Atzoatl": True,
            "Locus of Corruption": True,
            "Doryani's Institute": True,
            "Apex of Ascension": False,
            "Chamber of Iron": False,
            "Glittering Halls": False,
            "Hall of War": False,
            "Hybridisation Chamber": False,
            "Wealth of the Vaal": False,
            "Sanctum of Immortality": False,
            "Shrine of Unmaking": False,
            "Factory": False,
            "Museum Of Artefacts": False,
            "Defense Research Lab": False,
            "Hall of Legends": False,
            "Crucible of Flame": False,
            "Temple Nexus": False,
            "Toxic Grove": False,
            "Hall of Champions": False,
            "Storm of Corruption": False,
            "Sadist's Den": False,
            "Atlas of Worlds": False,
            "Throne of Atziri": False,
            "Conduit of Lightning": False,
            "Court of Sealed Death": False,
            "House of the Others": False
        })
   
    def from_dict(input_settings: dict):
        cls = Settings(**input_settings)
        # If it isn't cached, then invalid placeholder values can exist
        if cls.cached is True:
            cls.validate()
        return cls
   
    def from_tk_vars(input_tk_vars: dict):
        input_settings = iterate_through_dict(input_tk_vars, to_tk_vars=False)
        cls = Settings(**input_settings)
        cls.validate()
        return cls
   
    def to_tk_vars(self):
        return iterate_through_dict(self.__dict__, to_tk_vars=True)
   
    # Rewrite into a creator method that handles validation and put this in the main code
    def validate(self):
        # Check if the language was set
        if self.language == "language":
            raise ValueError(f"Language is not supported, got {self.language}")
       
        # Check if paths exist
        if not os.path.exists(self.client_txt_path):
            raise ValueError(f"client.txt was not found in path, got {repr(self.client_txt_path)}")
       
        if not os.path.exists(self.tesseract_exe_path):
            raise ValueError(f"tesseract.exe was not found in path, got {repr(self.tesseract_exe_path)}")
   
        try: # Check if screenshot_keybind is valid
            kb.parse_hotkey(self.screenshot_keybind)
        except ValueError:
            raise ValueError(f"Keybind was not recognized as valid, got {self.screenshot_keybind}")


def iterate_through_dict(input_dict: dict, to_tk_vars: bool):
    output = {}
    var_types = {bool: tk.BooleanVar, str: tk.StringVar}
    for key, value in input_dict.items():
        if key == "rooms": # Another depth here
            output["rooms"] = {}
            for room, valuable in value.items():
                if to_tk_vars:
                    output["rooms"][room] = tk.BooleanVar(value=valuable)
                else:
                    output["rooms"][room] = valuable.get()
            continue
        if to_tk_vars:
            output[key] = var_types[type(value)](value=value)
        else:
            output[key] = value.get()
    return output


@dataclass
class ImageParams:
    cached: bool = False
    room_details: dict = field(default_factory=lambda: {
        "room_width": 0,
        "room_height": 0,
        "horizontal_gap": 0,
        "vertical_gap": 0
    })
    slots_to_xy: dict = field(default_factory=lambda: {
        "0F1": {
            "x": 0,
            "y": 0
        },
        "0F2": {
            "x": 0,
            "y": 0
        },
        "0F3": {
            "x": 0,
            "y": 0
        },
        "1F0": {
            "x": 0,
            "y": 0
        },
        "1F1": {
            "x": 0,
            "y": 0
        },
        "1F2": {
            "x": 0,
            "y": 0
        },
        "1F3": {
            "x": 0,
            "y": 0
        },
        "2F0": {
            "x": 0,
            "y": 0
        },
        "2F1": {
            "x": 0,
            "y": 0
        },
        "2F2": {
            "x": 0,
            "y": 0
        },
        "3F0": {
            "x": 0,
            "y": 0
        },
        "3F1": {
            "x": 0,
            "y": 0
        },
        "4F0": {
            "x": 0,
            "y": 0
        }
    })
    incursion_menu_rect: dict = field(default_factory=lambda: {
        "x": 0,
        "y": 0,
        "w": 0,
        "h": 0
    })
    incursions_remaining_rect: dict = field(default_factory=lambda: {
        "x": 0,
        "y": 0,
        "w": 0,
        "h": 0
    })

    def from_dict(input_dict: dict):
        cls = ImageParams(**input_dict)
        return cls


@dataclass
class Metrics:
    total_incursion_time: int = 0
    total_incursions: int = 0
    average_incursion_time: float = 0
    total_temples: int = 0
    average_time_per_temple: float = 0
    total_stones_used: int = 0
    average_stones_per_temple: float = 0
    resource_reallocation_tiers: int = 0
    contested_development_tiers: int = 0
    architect_appearances: dict = field(default_factory=lambda: {
        "UN": 0,
        "AR": 0,
        "IR": 0,
        "PS": 0,
        "MN": 0,
        "$$": 0,
        "RG": 0,
        "EX": 0,
        "LF": 0,
        "IT": 0,
        "TR": 0,
        "LG": 0,
        "CR": 0,
        "FR": 0,
        "UP": 0,
        "PP": 0,
        "WP": 0,
        "TM": 0,
        "TS": 0,
        "MP": 0,
        "MM": 0,
        "LN": 0,
        "GM": 0,
        "SB": 0,
        "BR": 0
    })
    new_doors: int = 0
    new_tier_1_rooms: int = 0

    def from_dict(input_dict: dict):
        cls = Metrics(**input_dict)
        return cls

    def record_incursion_time(self, time: int):
        # Triggers when leaving an incursion
        self.total_incursion_time += time
        self.calc_average_time_per_incursion()
        self.calc_average_time_per_temple()

    def record_incursion(self, incursion: Incursion):
        # Triggers when looking at a new incursion screen
        self.total_incursions += 1

        self.architect_appearances[incursion.left_option.architect] += 1
        if incursion.room.tier == 0:
            self.architect_appearances[incursion.right_option.architect] += 1
   
    def record_new_temple(self, temple: Temple):
        # Triggers when looking at a new incursion screen and incursions_remaining = 12
        # Need to count number of open doors and number of T1 rooms, and which architects appear
        self.total_temples += 1
        self.calc_average_stones_per_temple()
        self.calc_average_time_per_temple()
        self.new_doors = temple.layout.count_open_doors()
        self.new_tier_1_rooms = temple.layout.count_tier_x_rooms(1)
        for architect in temple.layout.get_architects():
            self.architect_appearances[architect] += 1
       
    def record_temple_updates(self, doors_opened: int, was_swapped: bool, tiers_added: int):
        self.total_stones_used += int(doors_opened)
        self.calc_average_stones_per_temple()
        if was_swapped:
            self.contested_development_tiers += int(tiers_added) - 1
        else:
            self.resource_reallocation_tiers += int(tiers_added) - 1
   
    def calc_average_stones_per_temple(self):
        self.average_stones_per_temple = self.total_stones_used / self.total_temples
   
    def calc_average_time_per_incursion(self):
        self.average_incursion_time = self.total_incursion_time / self.total_incursions
   
    def calc_average_time_per_temple(self):
        self.average_time_per_temple = self.total_incursion_time / self.total_temples
    
    def __str__(self):
        output = ""
        output += f"Total Incursion Time: {self.total_incursion_time}\n"
        output += f"Total Incursions: {self.total_incursions}\n"
        output += f"Average Time per Incursion: {self.average_incursion_time}\n"
        output += f"Total Temples: {self.total_temples}\n"
        output += f"Average Time per Temple: {self.average_time_per_temple}\n"
        output += f"Total Stones of Passage Used: {self.total_stones_used}\n"
        output += f"Average Stones Used per Temple: {self.average_stones_per_temple}\n"
        output += f"Total Resource Reallocation Tiers: {self.resource_reallocation_tiers}\n"
        output += f"Total Contested Development Tiers: {self.contested_development_tiers}\n"
        return output


if __name__ == "__main__":
    import json
    with open(r"Chronicler/src/config.json") as f:
        data = json.load(f)
        data = data["metrics"]
   
    data = Settings()
    print(data)