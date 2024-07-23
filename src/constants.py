import pandas as pd
import json


# Maps room names to their "theme" (such as weapons) and their tier (0 to 3)
with open(r"src\rooms.json") as f:
    ROOM_DATA = pd.DataFrame.from_dict(json.load(f), orient="index")
    ROOM_DATA["Fixed"] = False
    ROOM_DATA.loc["ENTRANCE", "Fixed"] = True
    ROOM_DATA.loc["APEX OF ATZOATL", "Fixed"] = True
    ROOM_DATA["Valuable"] = False

# All the possible architects
ARCHITECTS = ROOM_DATA[["Theme", "Valuable"]][ROOM_DATA["Tier"] == 3].set_index("Theme")
ARCHITECTS["Impactful"] = False
ARCHITECTS.loc["EX", "Impactful"] = True
ARCHITECTS.loc["UP", "Impactful"] = True

# TODO: Implement ability to update this data from API
SCARABS = {
    "Incursion Scarab": 0.25,
    "Incursion Scarab of Timelines": 12,
}
