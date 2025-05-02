import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import piexif
import piexif.helper
from datetime import datetime
import tempfile
from pathlib import Path
import zipfile
import shutil

class FileManagementTool:
    def __init__(self, root):
        self.root = root
        self.root.title("File Management Tool")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self.metadata_tab = ttk.Frame(self.notebook)
        self.renamer_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.metadata_tab, text="Metadata Editor")
        self.notebook.add(self.renamer_tab, text="Batch Renamer")
        
        # Initialize both tools
        self.init_metadata_editor()
        self.init_batch_renamer()
    
    # ===== METADATA EDITOR FUNCTIONS =====
    def init_metadata_editor(self):
        self.selected_image = ""
        self.title_var = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.copyright_var = tk.StringVar()
        self.rating_var = tk.IntVar(value=5)
        self.comment_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        
        # Metadata Editor GUI
        tk.Label(self.metadata_tab, text="IMAGE METADATA EDITOR", font=('Arial', 14, 'bold')).pack(pady=10)
        self.selected_label = tk.Label(self.metadata_tab, text="No image selected", wraplength=550)
        self.selected_label.pack(pady=5)
        tk.Button(self.metadata_tab, text="🖼️ SELECT IMAGE", command=self.select_image,
                 bg='#4CAF50', fg='white', height=2, width=20).pack(pady=10)
        
        fields_frame = tk.Frame(self.metadata_tab)
        fields_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(fields_frame, text="Title/Description:").grid(row=0, column=0, sticky='w', pady=5)
        tk.Entry(fields_frame, textvariable=self.title_var, width=50).grid(row=0, column=1, padx=5)
        tk.Label(fields_frame, text="Artist/Author:").grid(row=1, column=0, sticky='w', pady=5)
        tk.Entry(fields_frame, textvariable=self.artist_var, width=50).grid(row=1, column=1, padx=5)
        tk.Label(fields_frame, text="Copyright:").grid(row=2, column=0, sticky='w', pady=5)
        tk.Entry(fields_frame, textvariable=self.copyright_var, width=50).grid(row=2, column=1, padx=5)
        tk.Label(fields_frame, text="Rating (0-5):").grid(row=3, column=0, sticky='w', pady=5)
        tk.Scale(fields_frame, from_=0, to=5, orient=tk.HORIZONTAL, 
                variable=self.rating_var, length=200).grid(row=3, column=1, sticky='w', padx=5)
        tk.Label(fields_frame, text="Comments:").grid(row=4, column=0, sticky='w', pady=5)
        tk.Entry(fields_frame, textvariable=self.comment_var, width=50).grid(row=4, column=1, padx=5)
        tk.Label(fields_frame, text="Subject/Keywords:").grid(row=5, column=0, sticky='w', pady=5)
        tk.Entry(fields_frame, textvariable=self.subject_var, width=50).grid(row=5, column=1, padx=5)
        
        self.metadata_progress = ttk.Progressbar(self.metadata_tab, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.metadata_progress.pack(pady=20)
        
        btn_frame = tk.Frame(self.metadata_tab)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="💾 UPDATE METADATA", command=self.update_metadata,
                 bg='#2196F3', fg='white', height=2, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔴 EXIT", command=self.safe_quit,
                 bg='#f44336', fg='white', height=2, width=15).pack(side=tk.LEFT, padx=5)
    
    def select_image(self):
        filetypes = (('Image files', '*.jpg *.jpeg *.png *.tiff *.tif'), ('All files', '*.*'))
        filename = filedialog.askopenfilename(title="Select Image File", filetypes=filetypes)
        if filename:
            self.selected_image = filename
            self.selected_label.config(text=f"Selected: {os.path.basename(filename)}")
            self.load_existing_metadata()
    
    def load_existing_metadata(self):
        try:
            img = Image.open(self.selected_image)
            if 'exif' in img.info:
                exif_dict = piexif.load(img.info['exif'])
                self.title_var.set(exif_dict["0th"].get(piexif.ImageIFD.ImageDescription, b'').decode('utf-8', errors='ignore'))
                self.artist_var.set(exif_dict["0th"].get(piexif.ImageIFD.Artist, b'').decode('utf-8', errors='ignore'))
                self.copyright_var.set(exif_dict["0th"].get(piexif.ImageIFD.Copyright, b'').decode('utf-8', errors='ignore'))
                user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment, b'')
                if user_comment:
                    try:
                        self.comment_var.set(piexif.helper.UserComment.load(user_comment))
                    except:
                        self.comment_var.set("")
            # Try to load subject from XMP if available
            if hasattr(img, 'info') and 'xmp' in img.info:
                try:
                    xmp = img.info['xmp'].decode('utf-8')
                    if '<dc:subject>' in xmp:
                        start = xmp.find('<dc:subject>') + len('<dc:subject>')
                        end = xmp.find('</dc:subject>')
                        self.subject_var.set(xmp[start:end])
                except:
                    pass
            img.close()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load metadata: {str(e)}")
    
    def update_metadata(self):
        if not self.selected_image:
            messagebox.showerror("Error", "Please select an image first!")
            return
        
        # Confirm with user before modifying original file
        if not messagebox.askyesno("Confirm", "This will modify the original file. Continue?"):
            return
            
        try:
            self.metadata_progress["value"] = 0
            self.root.update()
            
            # Open the original image
            img = Image.open(self.selected_image)
            
            # Load existing EXIF or create new
            exif_dict = piexif.load(img.info['exif']) if 'exif' in img.info else {
                "0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None
            }
            
            # Update metadata fields
            self.update_exif_data(exif_dict)
            
            # Create XMP metadata
            xmp = self.create_xmp_metadata()
            
            # Save to temporary file first (safety measure)
            temp_path = self.save_to_temp_file(img, exif_dict, xmp)
            
            # Replace original file
            self.replace_original_file(temp_path)
            
            self.metadata_progress["value"] = 100
            messagebox.showinfo("Success", "Metadata updated successfully in original file!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update metadata: {str(e)}")
            self.cleanup_temp_file(temp_path)
    
    def update_exif_data(self, exif_dict):
        """Update EXIF dictionary with current form values"""
        if self.title_var.get():
            exif_dict["0th"][piexif.ImageIFD.ImageDescription] = self.title_var.get().encode('utf-8')
        if self.artist_var.get():
            exif_dict["0th"][piexif.ImageIFD.Artist] = self.artist_var.get().encode('utf-8')
        if self.copyright_var.get():
            exif_dict["0th"][piexif.ImageIFD.Copyright] = self.copyright_var.get().encode('utf-8')
        if self.comment_var.get():
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(
                self.comment_var.get(), encoding="unicode")
        
        # Update timestamps
        now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        exif_dict["0th"][piexif.ImageIFD.DateTime] = now
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = now
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = now
    
    def create_xmp_metadata(self):
        """Create XMP metadata string with rating and subject"""
        return f"""<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 5.4.0">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/">
            <xmp:Rating>{self.rating_var.get()}</xmp:Rating>
        </rdf:Description>
        <rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">
            <dc:subject>
                <rdf:Bag>
                    <rdf:li>{self.subject_var.get()}</rdf:li>
                </rdf:Bag>
            </dc:subject>
        </rdf:Description>
    </rdf:RDF>
</x:xmpmeta>""".encode('utf-8')
    
    def save_to_temp_file(self, img, exif_dict, xmp):
        """Save image with new metadata to temporary file"""
        temp_path = os.path.join(tempfile.gettempdir(), f"temp_{os.path.basename(self.selected_image)}")
        exif_bytes = piexif.dump(exif_dict)
        
        if self.selected_image.lower().endswith(('.jpg', '.jpeg')):
            img.save(temp_path, exif=exif_bytes, quality=95, xmp=xmp)
        elif self.selected_image.lower().endswith('.png'):
            img.save(temp_path, exif=exif_bytes, xmp=xmp)
        else:
            img.save(temp_path)
        
        img.close()
        return temp_path
    
    def replace_original_file(self, temp_path):
        """Replace original file with the temporary file"""
        # Make backup of original file
        backup_path = self.selected_image + ".bak"
        os.replace(self.selected_image, backup_path)
        
        try:
            # Move temp file to original location
            os.replace(temp_path, self.selected_image)
            
            # If everything succeeded, remove backup
            os.remove(backup_path)
        except Exception as e:
            # Restore from backup if something went wrong
            if os.path.exists(backup_path):
                os.replace(backup_path, self.selected_image)
            raise e
    
    def cleanup_temp_file(self, temp_path):
        """Clean up temporary file if it exists"""
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
    
    # ===== BATCH RENAMER FUNCTIONS =====
    def init_batch_renamer(self):
        self.selected_files = []
        self.new_name = tk.StringVar(value="NewName")
        
        # Batch Renamer GUI
        tk.Label(self.renamer_tab, text="BATCH FILE RENAMER", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Selected items label
        self.renamer_selected_label = tk.Label(self.renamer_tab, text="No files selected")
        self.renamer_selected_label.pack(pady=5)
        
        # New Name Entry
        frame_name = tk.Frame(self.renamer_tab)
        frame_name.pack(pady=10, padx=10, fill=tk.X)
        tk.Label(frame_name, text="New Base Name:").pack(side=tk.LEFT)
        tk.Entry(frame_name, textvariable=self.new_name, width=30).pack(side=tk.LEFT, padx=5)
        
        # Action Buttons
        btn_frame = tk.Frame(self.renamer_tab)
        btn_frame.pack(pady=15)
        
        # Green Button - Select Files
        tk.Button(btn_frame, text="🟢 SELECT FILES", command=self.renamer_select_files,
                 bg='#4CAF50', fg='white', height=2, width=15).pack(side=tk.LEFT, padx=5)
        
        # Blue Button - Select Folder
        tk.Button(btn_frame, text="🔵 SELECT FOLDER", command=self.renamer_select_folder,
                 bg='#2196F3', fg='white', height=2, width=15).pack(side=tk.LEFT, padx=5)
        
        # Red Button - Exit
        tk.Button(btn_frame, text="🔴 EXIT", command=self.safe_quit,
                 bg='#f44336', fg='white', height=2, width=15).pack(side=tk.LEFT, padx=5)
        
        # Progress Bar
        self.renamer_progress = ttk.Progressbar(self.renamer_tab, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.renamer_progress.pack(pady=20)
        
        # Big Rename Button
        tk.Button(self.renamer_tab, text="START RENAMING", command=self.rename_items,
                 bg='#FF9800', fg='white', height=2, width=25, font=('Arial', 10, 'bold')).pack(pady=10)
    
    def renamer_select_files(self):
        files = filedialog.askopenfilenames(title="Select Files to Rename")
        if files:
            self.selected_files = list(files)
            self.renamer_selected_label.config(text=f"Selected: {len(self.selected_files)} files")
    
    def renamer_select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Files")
        if folder:
            self.selected_files = []
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.selected_files.append(file_path)
            self.renamer_selected_label.config(text=f"Selected: {len(self.selected_files)} files")
    
    def rename_items(self):
        new_name = self.new_name.get().strip()
        
        if not self.selected_files:
            messagebox.showerror("Error", "Please select files first!")
            return
        
        if not new_name:
            messagebox.showerror("Error", "Please enter a base name!")
            return
        
        try:
            self.renamer_progress["maximum"] = len(self.selected_files)
            self.root.update()
            
            for file_path in self.selected_files:
                if file_path.lower().endswith('.zip'):
                    self.rename_files_in_zip(file_path, new_name)
                else:
                    self.rename_regular_file(file_path, new_name)
                
                self.renamer_progress["value"] += 1
                self.root.update_idletasks()
            
            messagebox.showinfo("Success", "All files renamed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename: {str(e)}")
    
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
    
    # ===== COMMON FUNCTIONS =====
    def safe_quit(self):
        """Ensures complete application exit"""
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileManagementTool(root)
    root.protocol("WM_DELETE_WINDOW", app.safe_quit)
    root.mainloop()
