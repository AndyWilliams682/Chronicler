# Chronicler

An overlay tool for the Incursion mechanic in the game Path of Exile. Recognizes what rooms are in the temple and provides feedback to the player on what they should do.
## Features

The overlay provides a lot of information. Here's a sample below:
![](https://i.imgur.com/yQOpPhF.png)

### Building a Temple

When running incursions in maps, the tool can analyze the temple menu and provide feedback on. See mechanics.md for more information:

1) Which architect to kill
2) Which doors to open
3) Whether you should skip the rest of the incursions in the map
4) If it is worthwhile to use an Incursion Scarab of Timelines, and if it is worth unallocating ![Artefacts of the Vaal](https://www.poewiki.net/wiki/Artefacts_of_the_Vaal) (This is not implemented yet)
5) What minimum area level is needed to create a level 83 temple

There are settings available to configure which rooms are considered "valuable".

### Incursion Metrics

The tool also tracks metrics related to Incursion, including:

1) How much time you've spent in Incursions and your average time per incursion
2) How many stones of passage you've used
3) How many "successful" temples you've created
4) How often each architect has appeared in your temples (not visible, but it is saved)
5) How many times ![Resource Reallocation](https://www.poewiki.net/wiki/Resource_Reallocation) has triggered, and how many upgrade tiers you've gotten from ![Contested Development](https://www.poewiki.net/wiki/Contested_Development)

These are tracked whenever the tool is running, and does not factor in which character or league you are currently playing.

## Installation
To run the overlay, you will need the Tesseract OCR engine (it is used to read the text on screen). If you do not have it installed, you can install it ![here](https://github.com/UB-Mannheim/tesseract/wiki).

Then download the exe for this tool from the dist folder. Be sure to download the src folder in there as well as it includes the config file you will need to run the executable.

## Usage
### Setup
When you first run the overlay, the settings window will appear. Currently the only supported language is English. You will need to set your client.txt path and tesseract.exe path using the provided buttons (each need the folder which contains those files). Each setting is described below:
![](https://i.imgur.com/Ibh4QoY.png)
- Language: Currently the only supported language is English
- Path to client.txt: Click this button and navigate to where your client.txt file is located (Usually "C:\Program Files (x86)\Grinding Gear Games\Path of Exile\logs"). Be sure to select the folder that contains client.txt
- Path to tesseract.exe: Same as above, but for the tesseract executable from the installation step.
- Show tips: Checking this box shows Incursion tips in the overlay.
- Screenshot Method: Manual mode will capture and analyze a screenshot when the keybind is pressed at any time. This means you should have the temple menu already open and use a keybind that won't close it. In automatic mode, set your keybind to either your in-game "league interface" or "incursion interface" keybind (defaults to "v"). When running incursions, enter the portal and press that keybind, and the overlay will appear shortly after the menu pops up.
- Screenshot key: See above. This is either your chosen manual keybind or your in-game "league interace"/"incursion menu" keybind.
- Immersive UI: This sets the colors of the overlay to better match the in-game menu.
- Show settings on startup: Checking this box shows the settings when you first run the application.
- Rooms: Checking a room means that you consider it valuable and would like to pursue its' tier 3 form. Checking the Apex prioritizes opening any doors to it when possible.

I recommend you use automatic mode and get in the practice of ctrl-clicking alva, opening the incursion, entering the incursion and pressing your keybind. This provides the smoothest experience and pauses any in-game timers (Delirium fog) while you are in the incursion.

### Reading the overlay
See the features section for more information about the overlay output.
On the right-side of the temple menu, you will see any relevant information for the current incursion/temple, including which architect to kill, which doors to open first. Tips will appear on the button of the menu. On the left-side of the temple menu, you will see your incursion metrics and some interactable elements described below:
- Show settings upon entering hideout: When checked, the settings screen will reappear upon loading into your hideout. Useful for changing settings without restarting the application.
- Exit: This will kill the overlay.
- Reset metrics: This will reset the metrics to zero.

## Future Work
I'd like to add many features to this tool, including:
- Price checking and tracking for Incursion rooms
- Support for other languages
- Support for other operating systems
- Improved performance
- New metrics and more robust decision making algorithms

Please provide your own suggestions through github, contact me at andywilliams682@gmail.com

## Acknowledgements
- Awakened POE Trade, a tool that I used for inspiration
- POE-Archnem-Scanner, another tool I used for inspiration and Python examples