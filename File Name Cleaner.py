import os
import re
import sys

def clean_filename(filename):
    """Clean filename with smart capitalization and number removal"""
    name, ext = os.path.splitext(filename)
    
    # Step 1: Replace special chars AND numbers with spaces
    pattern = r'[-_()~!@#$%^&*\[\]{};:,<>?/\\|`\'"+=\s0-9]+'
    clean_name = re.sub(pattern, ' ', name)
    
    # Step 2: Remove extra spaces and normalize case
    words = clean_name.strip().split()
    if words:
        # First word: Capitalize first letter, lowercase rest
        words[0] = words[0][0].upper() + words[0][1:].lower() if words[0] else ''
        
        # Other words: Lowercase all
        for i in range(1, len(words)):
            words[i] = words[i].lower()
    
    clean_name = ' '.join(words)
    return clean_name + ext  # Keep original extension case

def rename_selected_files(file_paths):
    """Process each selected file"""
    for old_path in file_paths:
        if os.path.isdir(old_path):
            continue
            
        dirname = os.path.dirname(old_path)
        old_name = os.path.basename(old_path)
        new_name = clean_filename(old_name)
        
        if new_name != old_name:
            new_path = os.path.join(dirname, new_name)
            try:
                os.rename(old_path, new_path)
                print(f"✓ Renamed: '{old_name}' → '{new_name}'")
            except Exception as e:
                print(f"✗ Error renaming '{old_name}': {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        rename_selected_files(sys.argv[1:])
    else:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            files = filedialog.askopenfilenames(title="Select files to clean")
            if files:
                rename_selected_files(files)
            else:
                print("No files selected.")
        except ImportError:
            print("Error: Tkinter not available. Drag files onto the script instead.")
    
    sys.exit(0)
