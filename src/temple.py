import pandas as pd
from math import ceil, floor

from src.constants import ROOM_DATA, ARCHITECTS, SCARABS
from src.temple_layout import TempleLayout
from src.slot import Slot, chronicle_key
from src.room import Room
from src.incursion import Incursion
from src.decisions import choose_incursion_room, choose_which_doors_to_open, choose_to_leave_map_early


class Temple:
    # Current temple layout, incursion, and where all the architects are
    layout: TempleLayout
    incursion: Incursion
    architects: pd.DataFrame

    slots_selected_in_map: list # of Slots
    current_area_level: int # Might need to move to the client?
    total_incursion_area_levels: int
    highest_incursion_area_level: int
    incursions_remaining: int

    # These are the outputs the player needs to know from the tool
    selected_option: Room
    leave_map_early: bool
    priority_doors: list # of Slots
    
    def __init__(self):
        self.layout = None
        self.incursion = Incursion()
        self.incursions_remaining = 12
        self.architects = pd.Series(["Waiting"] * len(ARCHITECTS), index=ARCHITECTS.index, dtype=str)

        self.slots_selected_in_map = []
        self.current_area_level = 0
        self.total_incursion_area_levels = 0
        self.highest_incursion_area_level = 0

        self.selected_option = None
        self.leave_map_early = False
        self.priority_doors = []
    
    def generate():
        cls = Temple()
        cls.layout = TempleLayout.generate()
        cls.update_architects_in_temple()
        return cls
    
    def from_vision_output(vision_output):
        cls = Temple()
        cls.layout = TempleLayout.from_dict(vision_output["layout"])
        cls.incursion = Incursion.new(**vision_output["incursion"])
        cls.incursions_remaining = vision_output["remaining"]
        cls.update_architects_in_temple()
        return cls
    
    # This will be used when reading in Incursions from the menu to keep track of where architects are
    def update_architects_in_temple(self):
        for architect in self.architects.index:
            location = self.layout.get_slot_with(architect)
            if location is not None:
                self.architects[architect] = "Resident"
            elif self.architects[architect] == "Resident" or self.architects[architect] == "Non-Resident":
                self.architects[architect] = "Dead"
    
    def get_previous_incursion(self):
        return {"remaining": self.incursions_remaining, "slot": self.layout.get_slot_with(self.incursion.room)}
    
    def update_slot_from_vision_output(self, vision_output):
        slot_str = list(vision_output["layout"].keys())[0]
        self.incursions_remaining = vision_output["remaining"]
        old_tier = self.incursion.room.tier
        old_architect = self.incursion.room.architect
        old_doors = (self.layout.connection_map[Slot.from_str(slot_str)] == 1).sum()
        self.incursion = Incursion.new(**vision_output["incursion"])
        self.layout.update_slot_from_vision_output(slot_str, vision_output["layout"][slot_str])
        tiers_added = self.layout.slot_map["Room"][Slot.from_str(slot_str)].tier - old_tier

        was_swapped = True
        if old_architect == self.layout.slot_map["Room"][Slot.from_str(slot_str)].architect:
            was_swapped = False
        
        new_doors = (self.layout.connection_map[Slot.from_str(slot_str)] == 1).sum() - old_doors

        return new_doors, was_swapped, tiers_added
    
    def make_decisions(self):
        self.selected_option = choose_incursion_room(self.incursion)
        self.leave_map_early = choose_to_leave_map_early(self.selected_option)
        self.priority_doors = choose_which_doors_to_open(self.incursion.room, self.layout)

        choose_left = True
        if self.selected_option == self.incursion.right_option:
            choose_left = False
        
        choose_swap = True
        if self.selected_option.architect == self.incursion.room.architect:
            choose_swap = False
        
        ui_rooms = [self.layout.slot_map["Room"][slot].full_name for slot in self.priority_doors]

        return choose_left, choose_swap, self.leave_map_early, ui_rooms, self.calc_minimum_area_level_for_max()
    
    def reset_decisions(self):
        self.selected_option = None
        self.leave_map_early = False
        self.priority_doors = []
    
    # This is used when finishing a temple?
    def complete_temple(self):
        self.layout.apply_upgrade_room()
        self.layout.apply_explosives_room() # Not implemented currently
    
    def get_expected_scarab_value(self):
        scarab_of_timelines = SCARABS["Incursion Scarab of Timelines"]
        valuable_architects = ROOM_DATA["Theme"][ROOM_DATA["Price"] > 3 * scarab_of_timelines].values
        print(self.layout.get_scarab_value(valuable_architects))
        number_of_attempts_at_four = ceil(self.incursions_remaining / 4)
        number_of_attempts_at_three = ceil(self.incursions_remaining / 3)
        # What is the output of this function? Expected value? Chance for each room to be T3?
        # I am envisioning something that says "x% chance for T3 <room>; expected return of y chaos"
        # Whatever the numbers are need to be stored somewhere in self for the UI
        if number_of_attempts_at_three > number_of_attempts_at_four:
            print("Unallocating Artefacts of the Vaal will give you an additional Scarab of Timelines attempt.")
    
    def calc_minimum_area_level_for_max(self):
        # Minimum area level to get a temple of level 83
        if self.highest_incursion_area_level < 83:
            return 83
        if self.incursions_remaining == 0:
            return 0
        return ceil((876 - self.total_incursion_area_levels) / self.incursions_remaining)
    
    def get_temple_area_level(self):
        return min(self.highest_incursion_area_level, floor(self.total_incursion_area_levels / (12 - self.incursions_remaining)) + 10)
    
    def itemize(self):
        # This generates the Chronicle of Atzoatl
        open_rooms = self.layout.slot_map[self.layout.slot_map["Open"] == True]
        obstructed_rooms = self.layout.slot_map[self.layout.slot_map["Open"] == False]
        open_rooms = open_rooms.sort_index(key=chronicle_key)["Room"]
        obstructed_rooms = obstructed_rooms.sort_index(key=chronicle_key)["Room"]
        output = "Chronicle of Atzoatl\n"
        output += "====================\n"
        output += f"Area Level {self.get_temple_area_level()}\n"
        output += "--------------------\n"
        output += "Open Rooms:\n"
        for room in open_rooms:
            if room == Room("ENT", 0):
                continue
            output += room.chronicle_display + "\n"
        if len(obstructed_rooms) > 0:
            output += "\nObstructed Rooms:\n"
        for room in obstructed_rooms:
            output += room.chronicle_display + "\n"
        
        return output
    
    def __str__(self):
        output = str(self.layout)
        incursion_str = ""
        room = self.incursion.room
        if room is not None:
            output = output.replace(f" [{room}] ", f"*[{room}]*").replace(f" ({room}) ", f"*({room})*")
            incursion_str = str(self.incursion)

        remaining = f"{self.incursions_remaining} Incursions Remaining"
        remaining = ' ' * floor((32 - len(remaining) - 1) / 2) + remaining
        remaining = remaining.ljust(32) + "\n"
        output += "\n" + remaining

        return output + incursion_str


if __name__ == "__main__":
    test = Temple.from_vision_output({
        "layout": {
            "0F1": {"Name": "ANTECHAMBER", "Connections": ["—"]},
            "0F2": {"Name": "ENTRANCE", "Connections": []},
            "0F3": {"Name": "BANQUET HALL", "Connections": []},
            "1F0": {"Name": "CELLAR", "Connections": ["/", "\\"]},
            "1F1": {"Name": "CHASM", "Connections": []},
            "1F2": {"Name": "CLOISTER", "Connections": ["—"]},
            "1F3": {"Name": "HALLS", "Connections": []},
            "2F0": {"Name": "PASSAGEWAYS", "Connections": ["\\"]},
            "2F1": {"Name": "PITS", "Connections": []},
            "2F2": {"Name": "CORRUPTION CHAMBER", "Connections": []},
            "3F0": {"Name": "TOMBS", "Connections": ["\\"]},
            "3F1": {"Name": "SACRIFICIAL CHAMBER", "Connections": []},
            "4F0": {"Name": "APEX OF ATZOATL", "Connections": ["/"]}
        },
        "incursion": {
            "room": "PASSAGEWAYS",
            "left_option": "STRONGBOX CHAMBER",
            "right_option": "TORMENT CELLS"
        },
        "remaining": 0
    })
    print(test.layout.slot_map)
    exit()
    test.highest_incursion_area_level = 82
    test.total_incursion_area_levels = 73 * 12
    print(test.get_temple_area_level())
    print(test.itemize())
