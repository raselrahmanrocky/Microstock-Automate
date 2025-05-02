# Image Metadata Editor

![Python](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A Python GUI application for viewing and editing image metadata (EXIF and XMP) directly in original image files.

## Features

- ✏️ Edit metadata in original files (no "Save As" required)
- 📝 Supports all standard metadata fields:
  - Title/Description
  - Artist/Author
  - Copyright
  - Rating (0-5 stars)
  - Comments
  - Keywords/Tags
- ⏱️ Automatic timestamp updates
- 🔒 Built-in safety features:
  - Temporary file creation
  - Automatic backups
  - Error recovery
- 🖼️ Supports JPEG, PNG, and TIFF formats

## Screenshot

![Application Screenshot](screenshot.png)

## Installation

1. Ensure you have Python 3.6+ installed
2. Install required packages:

```bash
pip install pillow piexif
Download the script:

bash
wget https://raw.githubusercontent.com/yourusername/image-metadata-editor/main/metadata_editor_fixed.py
Usage
bash
python metadata_editor_fixed.py
Click "SELECT IMAGE" to choose a file

Edit the metadata fields

Click "UPDATE METADATA" to save changes

Supported Metadata Fields
Field	Metadata Standard	Storage Format
Title/Description	EXIF	ImageDescription
Artist/Author	EXIF	Artist
Copyright	EXIF	Copyright
Rating	XMP	xmp:Rating
Comments	EXIF	UserComment
Keywords/Tags	XMP	dc:subject
Safety Features
🛡️ Original files are never modified directly

💾 Automatic backup (.bak) created before changes

♻️ Original restored if anything fails

🗑️ Temporary files cleaned up automatically

Requirements
Python 3.6+

Pillow (PIL)

piexif

tkinter (usually included with Python)

License
MIT License - Free for personal and commercial use


To download this as a README.md file:

1. Copy all the text above
2. Save it as `README.md` in your project directory
3. Add a screenshot named `screenshot.png` in the same directory (optional)

The file includes:
- Badges for Python version and license
- Clear feature list with emojis
- Installation and usage instructions
- Metadata field reference table
- Safety feature explanations
- Requirements and license information

You may want to customize:
- The repository URL in the download instructions
- Add an actual screenshot
- Adjust any details specific to your project
