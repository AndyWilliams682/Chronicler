from dataclasses import dataclass

from src.room import Room


@dataclass
class Incursion():
    left_option: Room
    right_option: Room
    room: Room

    def __init__(self, room=None, left_option="--0", right_option="--0"):
        self.room = room
        self.left_option = left_option
        self.right_option = right_option
    
    def new(room: Room, left_option: Room, right_option: Room):
        cls = Incursion()
        cls.room = Room.from_name(room)
        cls.left_option = Room.from_name(left_option)
        cls.right_option = Room.from_name(right_option)
        return cls
    
    def __str__(self):
        output = '      ' + str(self.left_option) + ' <-- ' + str(self.room) + ' --> ' + str(self.right_option)
        return output.ljust(32)