Here's a comprehensive `README.md` file for your GitHub repository:

```markdown
# File Name Extractor

A Python script that extracts file names (including extensions) from selected files or folders and saves them to a text file. Works with both GUI and command line interfaces.

## Features

- Extracts complete file names with extensions
- Supports both individual file selection and batch folder processing
- Simple graphical interface (GUI) for easy use
- Command line interface for automation
- Outputs clean text file with one file name per line
- Preserves special characters in file names (UTF-8 encoding)

## Installation

1. Clone this repository or download the script:
   ```bash
   git clone https://github.com/yourusername/file-name-extractor.git
   ```
2. Ensure you have Python 3.x installed
3. Install required dependencies (only Tkinter which usually comes with Python):
   ```bash
   pip install tk
   ```

## Usage

### GUI Mode (Recommended for most users)

1. Run the script:
   ```bash
   python filename_extractor.py
   ```
2. Choose between:
   - "Select Files" to pick individual files
   - "Select Folder" to process all files in a directory
3. Select where to save the output text file
4. View your extracted file names in the output file

### Command Line Mode (For automation)

Process files:
```bash
python filename_extractor.py file1.txt file2.jpg -o output.txt
```

Process a folder:
```bash
python filename_extractor.py /path/to/folder -o output.txt
```

Process both files and folders:
```bash
python filename_extractor.py file1.txt /path/to/folder file2.jpg -o output.txt
```

## Output Format

The output text file will contain one file name per line, including the extension. Example:

```
document.pdf
image.jpg
presentation.pptx
data_2023.xlsx
```

## Screenshots

![GUI Interface]
![image](https://github.com/user-attachments/assets/52aadaa5-5462-4db0-a82d-6bdfdaaf396b)


## Requirements

- Python 3.x
- Tkinter (usually included with Python installation)

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or pull request for any improvements.

## Support

If you encounter any issues, please [open an issue](https://github.com/raselrahmanrocky/Microstock-Automate/File-Name-Extractor/file-name-extractor/issues) on GitHub.
```

To use this README:

1. Save it as `README.md` in your project directory
2. Replace `yourusername` with your actual GitHub username
3. Add a screenshot if available (save as `screenshot.png` in your repo)
4. Customize any sections as needed

The README includes:
- Clear project description
- Installation instructions
- Usage examples for both interfaces
- Output format explanation
- Requirements
- License information
- Contribution guidelines
- Support information

This will help users understand and use your project effectively when they visit your GitHub repository.
