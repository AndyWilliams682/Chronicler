import pandas as pd
import json

ROOM_DATA = {
    "ANTECHAMBER": { "Theme": "aa", "Tier": 0 },
    "APEX OF ATZOATL": { "Theme": "APX", "Tier": 0 },
    "BANQUET HALL": { "Theme": "bb", "Tier": 0 },
    "CELLAR": { "Theme": "cc", "Tier": 0 },
    "CHASM": { "Theme": "dd", "Tier": 0 },
    "CLOISTER": { "Theme": "ee", "Tier": 0 },
    "ENTRANCE": { "Theme": "ENT", "Tier": 0 },
    "HALLS": { "Theme": "ff", "Tier": 0 },
    "PASSAGEWAYS": { "Theme": "gg", "Tier": 0 },
    "PITS": { "Theme": "hh", "Tier": 0 },
    "TOMBS": { "Theme": "ii", "Tier": 0 },
    "TUNNELS": { "Theme": "jj", "Tier": 0 },
    "SACRIFICIAL CHAMBER": { "Theme": "UN", "Tier": 1 },
    "HALL OF OFFERINGS": { "Theme": "UN", "Tier": 2 },
    "APEX OF ASCENSION": { "Theme": "UN", "Tier": 3 },
    "ARMOURER'S WORKSHOP": { "Theme": "AR", "Tier": 1 },
    "ARMOURY": { "Theme": "AR", "Tier": 2 },
    "CHAMBER OF IRON": { "Theme": "AR", "Tier": 3 },
    "JEWELLER'S WORKSHOP": { "Theme": "IR", "Tier": 1 },
    "JEWELLERY FORGE": { "Theme": "IR", "Tier": 2 },
    "GLITTERING HALLS": { "Theme": "IR", "Tier": 3 },
    "GUARDHOUSE": { "Theme": "PS", "Tier": 1 },
    "BARRACKS": { "Theme": "PS", "Tier": 2 },
    "HALL OF WAR": { "Theme": "PS", "Tier": 3 },
    "HATCHERY": { "Theme": "MN", "Tier": 1 },
    "AUTOMATON LAB": { "Theme": "MN", "Tier": 2 },
    "HYBRIDISATION CHAMBER": { "Theme": "MN", "Tier": 3 },
    "VAULT": { "Theme": "$$", "Tier": 1 },
    "TREASURY": { "Theme": "$$", "Tier": 2 },
    "WEALTH OF THE VAAL": { "Theme": "$$", "Tier": 3 },
    "POOLS OF RESTORATION": { "Theme": "RG", "Tier": 1 },
    "SANCTUM OF VITALITY": { "Theme": "RG", "Tier": 2 },
    "SANCTUM OF IMMORTALITY": { "Theme": "RG", "Tier": 3 },
    "EXPLOSIVES ROOM": { "Theme": "EX", "Tier": 1 },
    "DEMOLITION LAB": { "Theme": "EX", "Tier": 2 },
    "SHRINE OF UNMAKING": { "Theme": "EX", "Tier": 3 },
    "WORKSHOP": { "Theme": "LF", "Tier": 1 },
    "ENGINEERING DEPARTMENT": { "Theme": "LF", "Tier": 2 },
    "FACTORY": { "Theme": "LF", "Tier": 3 },
    "STORAGE ROOM": { "Theme": "IT", "Tier": 1 },
    "WAREHOUSES": { "Theme": "IT", "Tier": 2 },
    "MUSEUM OF ARTEFACTS": { "Theme": "IT", "Tier": 3 },
    "TRAP WORKSHOP": { "Theme": "TR", "Tier": 1 },
    "TEMPLE DEFENSE WORKSHOP": { "Theme": "TR", "Tier": 2 },
    "DEFENSE RESEARCH LAB": { "Theme": "TR", "Tier": 3 },
    "HALL OF METTLE": { "Theme": "LG", "Tier": 1 },
    "HALL OF HEROES": { "Theme": "LG", "Tier": 2 },
    "HALL OF LEGENDS": { "Theme": "LG", "Tier": 3 },
    "CORRUPTION CHAMBER": { "Theme": "CR", "Tier": 1 },
    "CATALYST OF CORRUPTION": { "Theme": "CR", "Tier": 2 },
    "LOCUS OF CORRUPTION": { "Theme": "CR", "Tier": 3 },
    "FLAME WORKSHOP": { "Theme": "FR", "Tier": 1 },
    "OMNITECT FORGE": { "Theme": "FR", "Tier": 2 },
    "CRUCIBLE OF FLAME": { "Theme": "FR", "Tier": 3 },
    "SHRINE OF EMPOWERMENT": { "Theme": "UP", "Tier": 1 },
    "SANCTUM OF UNITY": { "Theme": "UP", "Tier": 2 },
    "TEMPLE NEXUS": { "Theme": "UP", "Tier": 3 },
    "POISON GARDEN": { "Theme": "PP", "Tier": 1 },
    "CULTIVAR CHAMBER": { "Theme": "PP", "Tier": 2 },
    "TOXIC GROVE": { "Theme": "PP", "Tier": 3 },
    "SPARRING ROOM": { "Theme": "WP", "Tier": 1 },
    "ARENA OF VALOUR": { "Theme": "WP", "Tier": 2 },
    "HALL OF CHAMPIONS": { "Theme": "WP", "Tier": 3 },
    "TEMPEST GENERATOR": { "Theme": "TM", "Tier": 1 },
    "HURRICANE ENGINE": { "Theme": "TM", "Tier": 2 },
    "STORM OF CORRUPTION": { "Theme": "TM", "Tier": 3 },
    "TORMENT CELLS": { "Theme": "TS", "Tier": 1 },
    "TORTURE CAGES": { "Theme": "TS", "Tier": 2 },
    "SADIST'S DEN": { "Theme": "TS", "Tier": 3 },
    "SURVEYOR'S STUDY": { "Theme": "MP", "Tier": 1 },
    "OFFICE OF CARTOGRAPHY": { "Theme": "MP", "Tier": 2 },
    "ATLAS OF WORLDS": { "Theme": "MP", "Tier": 3 },
    "ROYAL MEETING ROOM": { "Theme": "MM", "Tier": 1 },
    "HALL OF LORDS": { "Theme": "MM", "Tier": 2 },
    "THRONE OF ATZIRI": { "Theme": "MM", "Tier": 3 },
    "LIGHTNING WORKSHOP": { "Theme": "LN", "Tier": 1 },
    "OMNITECT REACTOR PLANT": { "Theme": "LN", "Tier": 2 },
    "CONDUIT OF LIGHTNING": { "Theme": "LN", "Tier": 3 },
    "GEMCUTTER'S WORKSHOP": { "Theme": "GM", "Tier": 1 },
    "DEPARTMENT OF THAUMATURGY": { "Theme": "GM", "Tier": 2 },
    "DORYANI'S INSTITUTE": { "Theme": "GM", "Tier": 3 },
    "STRONGBOX CHAMBER": { "Theme": "SB", "Tier": 1 },
    "HALL OF LOCKS": { "Theme": "SB", "Tier": 2 },
    "COURT OF SEALED DEATH": { "Theme": "SB", "Tier": 3 },
    "SPLINTER RESEARCH LAB": { "Theme": "BR", "Tier": 1 },
    "BREACH CONTAINMENT CENTER": { "Theme": "BR", "Tier": 2 },
    "HOUSE OF THE OTHERS": { "Theme": "BR", "Tier": 3 }
}

# Maps room names to their "theme" (such as weapons) and their tier (0 to 3)
ROOM_DATA = pd.DataFrame.from_dict(ROOM_DATA, orient="index")
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
