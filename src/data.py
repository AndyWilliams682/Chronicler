from dataclasses import dataclass, field
import tkinter as tk
import os
import keyboard as kb


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
