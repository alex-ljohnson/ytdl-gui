# YTDL GUI
A GUI For youtube-dl. Capable of many features + spotify-youtube translation support.
## What is this?
	This is a python program providing an implementation of YTDL in a GUI form.
## How does it work?
	It uses a tkinter GUI along with the youtube_dl module for python to provide a simple, easy-to-use user interface.
	
## Installing the program
- ### Using the installer (recommended)
	The best way to install the program for use is to use the installer provided under the releases section.
- ### Using the source code
	Clone the repository and create a virtual env (NAMED ".venv") in the same file as [\_\_main\_\_.py](__main__.py). Install the [requirements](requirements.txt) into the environment.
	```bash
	git clone https://github.com/MrTransparentBox/ytdl-gui.git
	cd ytdl-gui
	python -m venv .venv
	"./.venv/Scripts/activate"
	pip install -r requirement.txt
	```
	
## Using the program
### First setup
	First time opening the program, you will be asked to give a directory. 
	This will be the location which file will be downloaded to and scans will be taken from.

### Using the GUI
	Once the GUI is open you must enter one url on each line of the textbox in the GUI window. 
	Then, once saved, you may click the download button.
	
### Customising options
	Under 'tools' you will find 'Download Options...'. 
	When you click this a new menu pops up with different options for how and what should be downloaded.
	
### Customising preferences
	Under 'file' you will find 'Preferences'. 
	Clicking this brings up a menu with settings to customise the way the app behaves.

### Getting help
	For more information visit "Help > Help & Instructions" in the app's menu.

### Choosing a font
	In the view menu, under 'Font...' you can find a menu which allows you to select a font to be used in the text boxes.



## Advanced
### Writing extensions
	If you wish to add custom functionality to the program you can write your own python extensions. All python modules under the "(_internal)/modules/extensions" folder will be loaded at runtime.

#### Example
```python
from modules.extension import Extension

# Class must inherit from Extension in order to be loaded
class MyExtension(Extension):

	_name = "My custom extension" # (RECOMMENDED) Alternate name for use in UI
	def __init__(self): # Called when first loaded after start-up
		self.variable = "xyz"

	# Called when enabled in menu by user
	def enable(self):
		super().enable() # (REQUIRED) Signals that extension is on and ready for use
		# Logic here

	def disable(self):
		super().disable()
		# Logic here
```

#### Available packages
The packages available to import in your module include:

- Standard library 
- altgraph==0.17.5
- certifi==2026.2.25
- charset-normalizer==3.4.7
- idna==3.11
- mutagen==1.47.0
- packaging==26.1
- pefile==2024.8.26
- pillow==12.2.0
- psutil==7.2.2
- pyinstaller==6.19.0
- pyinstaller-hooks-contrib==2026.4
- pywin32-ctypes==0.2.3
- redis==7.4.0
- requests==2.33.1
- setuptools==82.0.1
- spotipy==2.26.0
- ttkthemes==3.3.0
- urllib3==2.6.3
- validators==0.35.0
- wheel==0.46.3
- yt-dlp==2026.3.17
