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

![image](https://github.com/user-attachments/assets/32600e01-7ea3-4592-a698-4f06fafd68eb)


## Installation

1. Ensure you have Python 3.6+ installed
2. Install required packages:

```bash
pip install pillow piexif
Download the script:

bash
wget https://raw.githubusercontent.com/raselrahmanrocky/image-metadata-editor/main/image_metadata_editor.py
Usage
bash
python image_metadata_editor.py
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

