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

def rename_files_in_folder(folder_path):
    """Rename all files in the selected folder"""
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory")
        return
    
    file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                 if os.path.isfile(os.path.join(folder_path, f))]
    
    if not file_paths:
        print("No files found in the selected folder.")
        return
    
    rename_selected_files(file_paths)

def create_gui():
    """Create graphical user interface with buttons"""
    root = tk.Tk()
    root.title("File Name Cleaner")
    root.geometry("400x200")
    
    def select_files():
        files = filedialog.askopenfilenames(title="Select files to clean")
        if files:
            rename_selected_files(files)
            messagebox.showinfo("Success", "File renaming completed!")
        else:
            messagebox.showwarning("Warning", "No files selected.")
        root.destroy()
    
    def select_folder():
        folder = filedialog.askdirectory(title="Select folder to clean files")
        if folder:
            rename_files_in_folder(folder)
            messagebox.showinfo("Success", "Folder files renaming completed!")
        else:
            messagebox.showwarning("Warning", "No folder selected.")
        root.destroy()
    
    # Create and place buttons
    tk.Label(root, text="Select an option to rename files:", font=('Arial', 12)).pack(pady=10)
    
    files_btn = tk.Button(root, text="Select Files", command=select_files, 
                         width=20, height=2, bg='#4CAF50', fg='white')
    files_btn.pack(pady=5)
    
    folder_btn = tk.Button(root, text="Select Folder", command=select_folder,
                          width=20, height=2, bg='#2196F3', fg='white')
    folder_btn.pack(pady=5)
    
    exit_btn = tk.Button(root, text="Exit", command=root.destroy,
                        width=20, height=2, bg='#f44336', fg='white')
    exit_btn.pack(pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        folders = [arg for arg in sys.argv[1:] if os.path.isdir(arg)]
        files = [arg for arg in sys.argv[1:] if os.path.isfile(arg)]
        
        if folders:
            for folder in folders:
                rename_files_in_folder(folder)
        if files:
            rename_selected_files(files)
    else:
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox
            create_gui()
        except ImportError:
            print("Error: Tkinter not available. Drag files or folders onto the script instead.")
    
    sys.exit(0)
