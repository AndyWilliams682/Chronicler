from dataclasses import dataclass


@dataclass(frozen=True)
class Slot():
    diag: int
    layer: int

    def from_str(string):
        # String is expected to be of the form 0F1
        return Slot(int(string[-1]), int(string[0]))
    
    def distance_to(self, other):
        return (abs(self.diag - other.diag) + abs(self.diag + self.layer - other.diag - other.layer) + abs(self.layer - other.layer)) / 2
    
    # TODO: This feels more like a function, than a method
    def pick_rightmost(self, other):
        output = self
        if self.diag == other.diag:
            if other.layer < self.layer:
                output = other
        else:
            if other.diag < self.diag:
                output = other
        return output
    
    def relative_direction_from(self, other):
        distance = self.distance_to(other)
        if distance != 1:
            raise ValueError(f"Cannot measure the direction between two slots if their distance is not equal to 1. Got {distance}")
        if self.diag == other.diag:
            return "\\"
        elif self.layer == other.layer:
            return "—"
        else:
            return "/"
    
    def get_adjacent_slot(self, direction):
        diag = self.diag
        if "r" in direction and "/" not in direction:
            diag -= 1
        elif "r" not in direction and direction != "\\":
            diag += 1
        layer = self.layer
        if "\\" in direction:
            layer += 1
        elif "/" in direction:
            layer -= 1
        return Slot(diag, layer)
    
    @property
    def chronicle_order(self):
        # Chronicle displays rooms starting at the bottom layer, left-most diag, moving right and then up to the next layer
        return 3 * self.layer - self.diag
    
    def __repr__(self):
        return f"{self.layer}F{self.diag}"


def chronicle_key(index):
    return index.map(lambda slot: slot.chronicle_order)
