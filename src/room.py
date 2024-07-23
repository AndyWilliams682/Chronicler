from dataclasses import dataclass
from random import randint

from constants import ROOM_DATA


@dataclass()
class Room:
    _immutable_themes = ["ENT", "APX"]
    architect: str = "--"
    tier: int = 0

    def from_abbreviation(abbreviation: str):
        if len(abbreviation) != 3:
            raise ValueError(f"Expected a string of lenth 3, got {len(abbreviation)}")
        if abbreviation in Room._immutable_themes:
            architect = abbreviation
            tier = 0
            return Room(architect, tier)
        
        architect = abbreviation[:2]
        tier = int(abbreviation[-1])
        return Room(architect, tier)
    
    def from_name(name: str):
        architect = ROOM_DATA["Theme"][name]
        tier = ROOM_DATA["Tier"][name]
        return Room(architect, tier)
    
    @property
    def full_name(self):
        return ROOM_DATA.index[(ROOM_DATA["Theme"] == self.architect) & (ROOM_DATA["Tier"] == self.tier)][0]
    
    @property
    def chronicle_display(self):
        output = self.full_name
        if self.tier > 0:
            output += f" (Tier {self.tier})"
        return output
    
    def __repr__(self):
        # Printing might depend on user formatting to output
        if self.architect in self._immutable_themes:
            return self.architect
        return self.architect + str(self.tier)
    
    def upgrade(self, additional_atlas_chance: int = 0):
        if self.tier == 0:
            raise ValueError(f"Only tiered rooms can be upgraded, {self.architect} (tier 0) cannot be upgraded")
        upgrade_size = 1
        chance = randint(1, 100)
        if chance <= additional_atlas_chance:
            upgrade_size = 2
        return Room(self.architect, min(3, self.tier + upgrade_size))
    
    def swap(self, new_architect: str, contested_development: bool = False):
        if self.architect in self._immutable_themes or self.tier == 3:
            raise ValueError(f"Fixed rooms cannot be swapped, failed to swap {self.architect} at tier {self.tier}")
        if contested_development:
            return Room(new_architect, min(3, self.tier + 1))
        return Room(new_architect, 1)
