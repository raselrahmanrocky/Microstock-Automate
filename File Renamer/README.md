# Batch File Renamer GUI

![Python](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A powerful Python GUI application for batch renaming files and files within ZIP archives with an intuitive interface.

## Features

- 🖼️ **GUI Interface** - User-friendly graphical interface
- 📁 **Batch Processing** - Rename multiple files/folders at once
- 🗃️ **ZIP Support** - Rename files inside ZIP archives (while keeping archive name)
- 🔢 **Smart Numbering** - Automatic duplicate handling with numbered suffixes
- 📊 **Progress Tracking** - Visual progress bar during operations
- 🚀 **Auto-Exit** - Clean automatic shutdown after completion

## Screenshot

![image](https://github.com/user-attachments/assets/e812ed19-411a-4acf-9df1-bdeb53a63985)


## Installation

### Prerequisites
- Python 3.6 or higher
- Tkinter (usually included with Python)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/batch-file-renamer.git
cd batch-file-renamer

# Run the application
python renamer.py
Usage
Launch the application

Select files/folders using the buttons:

🟢 SELECT FILES - Choose individual files

🔵 SELECT FOLDER - Process all files in a directory

Enter your desired base name

Click START RENAMING

The application will automatically close when finished

Special Features
Files inside ZIP archives will be renamed while keeping the ZIP filename

Duplicate names are automatically handled (e.g., file_1.txt, file_2.txt)

Preserves all original file extensions

Technical Details
File Handling
Regular files: oldname.ext → NewName.ext

ZIP contents: archive.zip/oldname.ext → archive.zip/NewName.ext

Duplicates: NewName_1.ext, NewName_2.ext, etc.

Code Structure
Uses Python's pathlib for robust path handling

Implements proper temporary file handling for ZIP operations

Thread-safe shutdown procedure

Troubleshooting
Issue: Application doesn't close properly
Solution: Ensure you're using the latest version with the fixed shutdown sequence

Issue: ZIP file operations fail
Solution: Make sure ZIP files aren't password protected

Contributing
Contributions are welcome! Please:

Fork the repository

Create a feature branch

Submit a pull request

License
This project is licensed under the MIT License - see the LICENSE file for details.

Developed with ❤️ using Python and Tkinter


This README includes:

1. Eye-catching badges for Python version and license
2. Clear feature list with emojis
3. Installation and usage instructions
4. Technical implementation details
5. Troubleshooting section
6. Contribution guidelines
7. License information

To complete your repository:

1. Add a `LICENSE` file (MIT recommended)
2. Take a screenshot of the application and save as `screenshot.png`
3. Consider adding a `requirements.txt` if you add dependencies
4. Optionally add GitHub Actions for automated testing

The README is designed to be both visually appealing and informative, helping users quickly understand and use your application.
