# File Management Tool

A desktop GUI application built with **Tkinter** for Windows/Linux/macOS that allows users to:

- Edit image metadata (EXIF and XMP)
- Batch rename files or entire folders
- Rename files inside ZIP archives

## Features

### 📸 Metadata Editor
- Edit EXIF fields like:
  - Title/Description
  - Artist/Author
  - Copyright
  - Comments
- Add or update:
  - Rating (0-5, stored in XMP)
  - Subject/Keywords
- Automatically updates timestamps
- Safe editing using temporary files and backups

### 📁 Batch File Renamer
- Rename selected files or all files in a folder
- Supports ZIP files (renames internal files)
- Handles naming collisions automatically

## Installation

### Requirements

- Python 3.7+
- Required packages:
  - `Pillow`
  - `piexif`

Install dependencies:

```bash
pip install pillow piexif

Usage
Run the script directly with Python:

bash
Copy
Edit
python metadata\ editing\ and\ batch\ renaming.py
UI Overview
Metadata Editor Tab:

Select an image to edit metadata

Fill in fields and press "Update Metadata"

Batch Renamer Tab:

Select files or a folder

Enter a base name

Click "Start Renaming"

Backup & Safety
Metadata editing creates a .bak backup of the original image

Renaming handles file overwrites by appending a counter (e.g., NewName_1.jpg)

Supported Formats
Images: .jpg, .jpeg, .png, .tif, .tiff

Archives: .zip

Screenshot
(Optional: add screenshots of the GUI here)

License
MIT License – feel free to use and modify.
