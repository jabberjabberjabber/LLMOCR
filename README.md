# LLMOCR

LLMOCR uses a local LLM to read text from images.

You can also change the instruction to have the LLM use the image in the way that you prompt.

![Screenshot](llmocr.png)

## Features
 
- **Local Processing**: All processing is done locally on your machine.
- **User-Friendly GUI**: Includes a GUI. Relies on Koboldcpp, a single executable, for all AI functionality.  
- **GPU Acceleration**: Will use Apple Metal, Nvidia CUDA, or AMD (Vulkan) hardware if available to greatly speed inference.
- **Cross-Platform**: Supports Windows, macOS ARM, and Linux.

### Prerequisites

- Python 3.8 or higher

### Windows Installation

1. Clone the repository

2. Install [Python for Windows](https://www.python.org/downloads/windows/)

3. Open KoboldCpp or an OpenAI compatible API and load a vision model
 
4. Open `llmocr.bat` 


### Mac and Linux Installation

1. Clone the repository or download and extract the ZIP file

2. Install Python 3.8 or higher if not already installed

3. Create a new python env and install the requirements.txt

4. Open KoboldCpp or an OpenAI compatible API with a loaded vision model

5. Run llmocr.py using Python
