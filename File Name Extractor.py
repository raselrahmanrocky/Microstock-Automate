import os
import tkinter as tk
from tkinter import filedialog, messagebox
import sys

def extract_filenames(file_paths, output_file):
    """Extract filenames (with extensions) from selected files and save to output file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for path in file_paths:
                if os.path.isdir(path):
                    continue
                filename = os.path.basename(path)
                f.write(f"{filename}\n")  # Now includes extension
        return True
    except Exception as e:
        print(f"Error saving to {output_file}: {e}")
        return False

def extract_filenames_from_folder(folder_path, output_file):
    """Extract filenames (with extensions) from all files in a folder and save to output file"""
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory")
        return False
    
    file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                 if os.path.isfile(os.path.join(folder_path, f))]
    
    if not file_paths:
        print("No files found in the selected folder.")
        return False
    
    return extract_filenames(file_paths, output_file)

def create_gui():
    """Create graphical user interface with buttons"""
    root = tk.Tk()
    root.title("File Name Extractor")
    root.geometry("500x250")
    
    def select_output_location():
        return filedialog.asksaveasfilename(
            title="Save extracted names as",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
    
    def select_files():
        files = filedialog.askopenfilenames(title="Select files to extract names from")
        if not files:
            messagebox.showwarning("Warning", "No files selected.")
            return
            
        output_file = select_output_location()
        if not output_file:
            return
            
        if extract_filenames(files, output_file):
            messagebox.showinfo("Success", f"File names (with extensions) extracted and saved to:\n{output_file}")
        else:
            messagebox.showerror("Error", "Failed to save extracted names.")
        root.destroy()
    
    def select_folder():
        folder = filedialog.askdirectory(title="Select folder to extract names from")
        if not folder:
            messagebox.showwarning("Warning", "No folder selected.")
            return
            
        output_file = select_output_location()
        if not output_file:
            return
            
        if extract_filenames_from_folder(folder, output_file):
            messagebox.showinfo("Success", f"File names (with extensions) extracted and saved to:\n{output_file}")
        else:
            messagebox.showerror("Error", "Failed to save extracted names.")
        root.destroy()
    
    # Create and place widgets
    tk.Label(root, text="File Name Extractor", font=('Arial', 14, 'bold')).pack(pady=10)
    tk.Label(root, text="Extracts file names including extensions", font=('Arial', 10)).pack()
    tk.Label(root, text="Select an option to extract file names:", font=('Arial', 10)).pack()
    
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
        import argparse
        
        parser = argparse.ArgumentParser(description='Extract file names (with extensions) to a text file.')
        parser.add_argument('paths', nargs='+', help='Files or folders to process')
        parser.add_argument('-o', '--output', required=True, help='Output text file path')
        
        args = parser.parse_args()
        
        folders = [arg for arg in args.paths if os.path.isdir(arg)]
        files = [arg for arg in args.paths if os.path.isfile(arg)]
        
        success = False
        if folders:
            for folder in folders:
                success = extract_filenames_from_folder(folder, args.output) or success
        if files:
            success = extract_filenames(files, args.output) or success
            
        if not success:
            print("Error: No valid files processed.")
            sys.exit(1)
        else:
            print(f"File names (with extensions) saved to: {args.output}")
    else:
        try:
            create_gui()
        except ImportError:
            print("Error: Tkinter not available. Please use command line mode.")
            print("Usage: python filename_extractor.py [files_or_folders] -o output.txt")
    
    sys.exit(0)