# Deep Rock Galactic Save Editor

Continuation of the DRG Save Editor first created here: https://github.com/robertnunn/DRG-Save-Editor

I decided to pick up on implementing some of the features here after being personally grievanced by some of the assignments locking you into them until you complete them, preventing me from picking up the holiday assignments to play with my friends.

Standalone DRG save editor written in python, using PySide6 and packaged with PyInstaller. Release builds are made by GitHub Actions when a `v*` tag is pushed.

## Requirements
- Windows 10 or later (the Qt 6 / modern Python builds don't support Windows 7)

## Installation
Download the latest zip from the Releases page, extract it, and run `DRG Save Editor.exe`.

## Running from source
```
pip install -r requirements.txt
python src/main/python/main.py
```
Run it from the repository root, since `guids.json`, `cosmetics.json` and `campaigns.json` are read from the working directory.

## Known Issues
- The editor still finds most values (resources, XP, credits, perk points, promotions) by searching the raw save data. If something isn't in the save yet (e.g. a resource you've never owned) the editor can give nonsensical results. The solution is to acquire at least one of the resource in game _then_ use the editor.
- Only some cosmetic overclocks are known: beards, moustaches, sideburns, headwear, victory poses and weapon skins. Any other overclock you have acquired but not forged is listed as "Unknown overclock" and kept in your save. Cosmetics that are not overclocks (armor paint jobs, hair and skin colours, ...) cannot be edited yet.

## Troubleshooting
If the editor fails to start, please run it from source (see Running from source) in a command prompt. This will let you see any error messages that will be necessary for bug fixes. 

If the editor opens but doesn't edit your save properly (i.e., values not being read properly, changes not being reflected in-game, etc) please open an issue, describe the problem as thoroughly as you can, and attach a copy of your save file from BEFORE any edits were attempted.

## Usage
### ALWAYS BACKUP YOUR SAVE FILE!
The editor will make a backup of the save file you open in the same folder as the save file with the extension of `.old`. The editor makes this backup at the moment you open the save file.

The editor is split into pages, picked in the sidebar: Classes, Resources, Season, Overclocks and Assignments. Open a save, change what you want, and press **Save changes** (Ctrl+S). Save and Reset are only available while there are unsaved changes, which the top bar tells you about.

Some notes:
- Overclocks are grouped by class and then by weapon; the cosmetic overclocks (beards, victory poses, ...) have a group per kind after the weapons. Use the search box and the class, type (weapon or cosmetic) and status filters to narrow the list. Select overclocks (Ctrl+Click or Shift+Click for several) and press **Add selected to inventory**. Selecting a whole weapon, cosmetic group or class adds everything unacquired under it that is currently shown.
- Added overclocks go to **Acquired but unforged** on the right and are written to your save when you save. The list shows the class initial (D, E, G, S) in the class colour, a dot, then the weapon or cosmetic kind, then the name; weapon overclocks come first. Remove them from there the same way. In game you can then forge them (use **Add required materials** to get the resources for everything in that list).
- The Season page edits one season at a time; the newest season is selected by default.
- On the Assignments page you can tick assignments as completed, assign one as your active assignment, or complete or unassign the active one. Changes take effect at once on screen and are written to the save with everything else. The weekly assignments (Core Hunt and Priority Assignment) are managed by the game and are not listed.
- Changing XP values will update the other relevant fields when the focus changes (i.e., click on a different part of the program or another program entirely)
- If you have promotions beyond Legendary 3 those promotions will be preserved as long as the drop-down is set to "Legendary 3+". If you don't have enough promotions for a specific dwarf and set them to "Legendary 3+" it will keep whatever the original value was.

### Overclocks Tab
![overclocks](sshot.png)

### Classes Tab
![classes](sshot_classes.png)

## Data sources
Overclock names, costs and GUIDs in `guids.json` were verified against the game's own data (extracted with FModel).

## Would be nice, but ehh...
- Character loadout support
- Perk support
- Weapon modification support
- Milestone support
- Bells & Whistles
