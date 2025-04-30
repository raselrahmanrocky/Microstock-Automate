import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import zipfile
import tempfile
import sys
import shutil

class BatchRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch File Renamer")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Variables
        self.selected_files = []
        self.new_name = tk.StringVar(value="NewName")
        
        # GUI Setup
        self.create_widgets()
    
    def create_widgets(self):
        # Title
        tk.Label(self.root, text="BATCH FILE RENAMER", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Selected items label
        self.selected_label = tk.Label(self.root, text="No files selected")
        self.selected_label.pack(pady=5)
        
        # New Name Entry
        frame_name = tk.Frame(self.root)
        frame_name.pack(pady=10, padx=10, fill=tk.X)
        tk.Label(frame_name, text="New Base Name:").pack(side=tk.LEFT)
        tk.Entry(frame_name, textvariable=self.new_name, width=30).pack(side=tk.LEFT, padx=5)
        
        # Action Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)
        
        # Green Button - Select Files
        tk.Button(btn_frame, text="🟢 SELECT FILES", command=self.select_files,
                 bg='#4CAF50', fg='white', height=2, width=15).pack(side=tk.LEFT, padx=5)
        
        # Blue Button - Select Folder
        tk.Button(btn_frame, text="🔵 SELECT FOLDER", command=self.select_folder,
                 bg='#2196F3', fg='white', height=2, width=15).pack(side=tk.LEFT, padx=5)
        
        # Red Button - Exit
        tk.Button(btn_frame, text="🔴 EXIT", command=self.safe_quit,
                 bg='#f44336', fg='white', height=2, width=15).pack(side=tk.LEFT, padx=5)
        
        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(pady=20)
        
        # Big Rename Button
        tk.Button(self.root, text="START RENAMING", command=self.rename_items,
                 bg='#FF9800', fg='white', height=2, width=25, font=('Arial', 10, 'bold')).pack(pady=10)
    
    def select_files(self):
        files = filedialog.askopenfilenames(title="Select Files to Rename")
        if files:
            self.selected_files = list(files)
            self.selected_label.config(text=f"Selected: {len(self.selected_files)} files")
    
    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Files")
        if folder:
            self.selected_files = []
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.selected_files.append(file_path)
            self.selected_label.config(text=f"Selected: {len(self.selected_files)} files")
    
    def rename_items(self):
        new_name = self.new_name.get().strip()
        
        if not self.selected_files:
            messagebox.showerror("Error", "Please select files first!")
            return
        
        if not new_name:
            messagebox.showerror("Error", "Please enter a base name!")
            return
        
        try:
            self.progress["maximum"] = len(self.selected_files)
            self.root.update()
            
            for file_path in self.selected_files:
                if file_path.lower().endswith('.zip'):
                    self.rename_files_in_zip(file_path, new_name)
                else:
                    self.rename_regular_file(file_path, new_name)
                
                self.progress["value"] += 1
                self.root.update_idletasks()
            
            messagebox.showinfo("Success", "All files renamed successfully!")
            self.safe_quit()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename: {str(e)}")
            self.safe_quit()

    def rename_regular_file(self, file_path, new_name):
        """Rename regular files (non-zip)"""
        path = Path(file_path)
        new_filename = f"{new_name}{path.suffix}"
        new_path = path.with_name(new_filename)
        
        # Handle duplicates
        counter = 1
        while new_path.exists():
            new_filename = f"{new_name}_{counter}{path.suffix}"
            new_path = path.with_name(new_filename)
            counter += 1
        
        path.rename(new_path)

    def rename_files_in_zip(self, zip_path, new_name):
        """Rename files inside ZIP archives"""
        temp_dir = tempfile.mkdtemp()
        temp_zip = os.path.join(temp_dir, "temp.zip")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zin:
                with zipfile.ZipFile(temp_zip, 'w') as zout:
                    for item in zin.infolist():
                        if not item.is_dir():
                            # Extract file extension
                            _, ext = os.path.splitext(item.filename)
                            # Create new filename
                            new_filename = f"{new_name}{ext}"
                            # Add file with new name to temp zip
                            zout.writestr(new_filename, zin.read(item.filename))
            
            # Replace original with renamed version
            os.remove(zip_path)
            shutil.move(temp_zip, zip_path)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def safe_quit(self):
        """Ensures complete application exit"""
        self.root.quit()  # Stops mainloop
        self.root.destroy()  # Destroys all widgets
        os._exit(0)  # Force exit all threads

if __name__ == "__main__":
    root = tk.Tk()
    app = BatchRenamerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.safe_quit)
    root.mainloop()
