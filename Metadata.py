import customtkinter as ctk
from tkinter import filedialog, ttk, messagebox
import os
import json
import threading
import queue
from PIL import Image, UnidentifiedImageError
import google.generativeai as genai
import csv
import time
import webbrowser
import piexif
import piexif.helper
from datetime import datetime
import tempfile

CONFIG_FILE = "imagemeta_config.json"
STATS_FILE = "imagemeta_stats.json"

class ImageMetaGenerator(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Image Metadata Generator")
        self.geometry("1200x800")
        
        # Configuration and state variables
        self.api_key = ""
        self.selected_files = []
        self.file_iid_map = {}
        self.processing_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.processing_thread = None
        self.is_paused = False
        self.stop_processing_event = threading.Event()
        
        # Statistics tracking
        self.processed_files_count = 0
        self.total_selected_files = 0
        self.current_batch_start_time = None
        self.total_processing_time = 0.0
        self.all_time_stats = {"files_processed": 0}
        self.last_24h_stats = {"files_processed": 0, "timestamp": time.time()}
        
        # Load configuration and initialize UI
        self._load_config()
        self._load_stats()
        ctk.set_appearance_mode(self.user_theme_preference)
        
        # Configure main window layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Main content area
        
        # Create UI sections
        self._create_header_section()
        self._create_controls_section()
        self._create_file_selection_section()
        self._create_metadata_table_section()
        self._create_status_bar()
        
        # Apply initial settings
        self._apply_treeview_style()
        self.update_stats_display()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.api_key = config.get("api_key", "")
                self.user_theme_preference = config.get("theme", "Dark")
        except (FileNotFoundError, json.JSONDecodeError):
            self.api_key = ""
            self.user_theme_preference = "Dark"

    def _save_config(self):
        config = {
            "api_key": self.api_key,
            "theme": ctk.get_appearance_mode(),
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except IOError:
            messagebox.showerror("Error", "Could not save configuration.")

    def _load_stats(self):
        try:
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
                self.all_time_stats["files_processed"] = stats.get("all_time_processed", 0)
                self.last_24h_stats = stats.get("last_24h_stats", {"files_processed": 0, "timestamp": time.time()})
                self.total_processing_time = stats.get("total_processing_time", 0.0)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_stats(self):
        stats = {
            "all_time_processed": self.all_time_stats["files_processed"],
            "last_24h_stats": self.last_24h_stats,
            "total_processing_time": self.total_processing_time
        }
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(stats, f, indent=4)
        except IOError:
            print("Error saving statistics.")

    def _create_header_section(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        # Title and developer info
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(title_frame, text="Image Metadata Generator", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Generate AI-powered metadata for your images", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w")
        
        # API key controls
        api_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        api_frame.pack(side="right")
        ctk.CTkLabel(api_frame, text="API Key:").pack(side="left", padx=(0, 5))
        self.api_key_entry = ctk.CTkEntry(api_frame, width=250, placeholder_text="Enter Gemini API Key")
        self.api_key_entry.pack(side="left", padx=5)
        self.api_key_entry.insert(0, self.api_key)
        
        ctk.CTkButton(api_frame, text="Validate", width=80, 
                     command=self.validate_api_key).pack(side="left", padx=5)
        ctk.CTkButton(api_frame, text="Save", width=60, 
                     command=self.save_api_key).pack(side="left", padx=5)
        ctk.CTkButton(api_frame, text="Get API", width=80, 
                     command=lambda: webbrowser.open("https://makersuite.google.com/app/apikey")).pack(side="left", padx=5)

    def _create_controls_section(self):
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Theme selection
        theme_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        theme_frame.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=(0, 10))
        self.theme_var = ctk.StringVar(value=self.user_theme_preference)
        ctk.CTkRadioButton(theme_frame, text="Dark", variable=self.theme_var, 
                          value="Dark", command=self.change_theme).pack(side="left", padx=5)
        ctk.CTkRadioButton(theme_frame, text="Light", variable=self.theme_var, 
                          value="Light", command=self.change_theme).pack(side="left", padx=5)
        
        # Action buttons
        action_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        action_frame.pack(side="right")
        self.start_button = ctk.CTkButton(action_frame, text="▶ Start", 
                                        command=self.start_processing, fg_color="green")
        self.start_button.pack(side="left", padx=5)
        self.pause_button = ctk.CTkButton(action_frame, text="❚❚ Pause", 
                                         state="disabled", command=self.pause_processing, 
                                         fg_color="orange")
        self.pause_button.pack(side="left", padx=5)
        self.update_metadata_button = ctk.CTkButton(action_frame, text="Update Metadata", 
                                                   command=self.update_image_metadata)
        self.update_metadata_button.pack(side="left", padx=5)
        self.export_button = ctk.CTkButton(action_frame, text="Export CSV", 
                                          command=self.export_to_csv)
        self.export_button.pack(side="left", padx=5)
        self.clear_button = ctk.CTkButton(action_frame, text="Clear All", 
                                        command=self.clear_all, fg_color="red")
        self.clear_button.pack(side="left", padx=5)

    def _create_file_selection_section(self):
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(file_frame, text="Image Files:").pack(side="left", padx=(0, 10))
        ctk.CTkButton(file_frame, text="Select Images", 
                     command=self.select_images).pack(side="left", padx=5)
        ctk.CTkButton(file_frame, text="Select Folder", 
                     command=self.select_folder).pack(side="left", padx=5)
        
        self.status_label = ctk.CTkLabel(file_frame, text="Ready")
        self.status_label.pack(side="right", padx=10)

    def _create_metadata_table_section(self):
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=3, column=0, padx=10, pady=(0, 5), sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview with scrollbar
        self.tree = ttk.Treeview(table_frame, columns=("Filename", "Title", "Keywords", "Description"), 
                                show="headings", selectmode="extended")
        self.tree.heading("Filename", text="Filename")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Keywords", text="Keywords")
        self.tree.heading("Description", text="Description")
        
        # Set column widths
        self.tree.column("Filename", width=200, stretch=False)
        self.tree.column("Title", width=200, stretch=False)
        self.tree.column("Keywords", width=250, stretch=False)
        self.tree.column("Description", width=400, stretch=True)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Add scrollbar
        scrollbar = ctk.CTkScrollbar(table_frame, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _create_status_bar(self):
        status_frame = ctk.CTkFrame(self, height=40)
        status_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(status_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", padx=10, pady=5, fill="x", expand=True)
        
        # Stats labels
        stats_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        stats_frame.pack(side="right", padx=10)
        self.files_processed_label = ctk.CTkLabel(stats_frame, text="Processed: 0")
        self.files_processed_label.pack(side="left", padx=5)
        self.time_label = ctk.CTkLabel(stats_frame, text="Time: 00:00")
        self.time_label.pack(side="left", padx=5)

    def _apply_treeview_style(self):
        style = ttk.Style()
        current_theme = ctk.get_appearance_mode()
        
        if current_theme == "Dark":
            bg_color = "#2B2B2B"
            fg_color = "white"
            heading_bg = "#3C3C3C"
            style.theme_use('default')
        else:
            bg_color = "white"
            fg_color = "black"
            heading_bg = "#E1E1E1"
            style.theme_use('clam')
        
        style.configure("Treeview", background=bg_color, foreground=fg_color, 
                       fieldbackground=bg_color, borderwidth=0, rowheight=25)
        style.configure("Treeview.Heading", background=heading_bg, 
                       foreground=fg_color, relief="flat", 
                       font=('Helvetica', 10, 'bold'))

    def change_theme(self):
        theme = self.theme_var.get()
        ctk.set_appearance_mode(theme)
        self._apply_treeview_style()
        self.user_theme_preference = theme
        self._save_config()

    def validate_api_key(self):
        api_key = self.api_key_entry.get()
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key")
            return
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
            model.generate_content("Test prompt")
            messagebox.showinfo("Success", "API key is valid")
        except Exception as e:
            messagebox.showerror("Error", f"API validation failed: {str(e)}")

    def save_api_key(self):
        self.api_key = self.api_key_entry.get()
        self._save_config()
        messagebox.showinfo("Success", "API key saved")

    def select_images(self):
        filetypes = (("Image files", "*.jpg *.jpeg *.png *.webp"), ("All files", "*.*"))
        files = filedialog.askopenfilenames(title="Select Images", filetypes=filetypes)
        
        if files:
            new_files = [f for f in files if f not in self.selected_files]
            self.selected_files.extend(new_files)
            self._update_file_list(new_files)
            self._update_file_count()

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            new_files = []
            extensions = ('.jpg', '.jpeg', '.png', '.webp')
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(extensions):
                        filepath = os.path.join(root, file)
                        if filepath not in self.selected_files:
                            new_files.append(filepath)
            
            if new_files:
                self.selected_files.extend(new_files)
                self._update_file_list(new_files)
                self._update_file_count()

    def _update_file_list(self, files):
        for filepath in files:
            filename = os.path.basename(filepath)
            iid = self.tree.insert("", "end", values=(filename, "Pending...", "", ""))
            self.file_iid_map[filepath] = iid

    def _update_file_count(self):
        count = len(self.selected_files)
        self.total_selected_files = count
        self.status_label.configure(text=f"{count} files selected")

    def start_processing(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected")
            return
        
        api_key = self.api_key_entry.get()
        if not api_key:
            messagebox.showerror("Error", "API key is required")
            return
        
        # Get files that haven't been processed yet
        files_to_process = [
            f for f in self.selected_files 
            if self.tree.item(self.file_iid_map[f])['values'][1] in ["Pending...", "Error"]
        ]
        
        if not files_to_process:
            messagebox.showinfo("Info", "No files need processing")
            return
        
        # Setup processing state
        self.is_paused = False
        self.stop_processing_event.clear()
        self.processed_files_count = 0
        self.current_batch_start_time = time.time()
        
        # Update UI
        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.update_metadata_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.status_label.configure(text="Processing...", text_color="orange")
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_files,
            args=(files_to_process, api_key),
            daemon=True
        )
        self.processing_thread.start()
        
        # Start checking results queue
        self.after(100, self._check_processing_results)

    def _process_files(self, filepaths, api_key):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
            
            for filepath in filepaths:
                if self.stop_processing_event.is_set():
                    self.results_queue.put(("stopped", filepath))
                    return
                
                while self.is_paused:
                    if self.stop_processing_event.is_set():
                        self.results_queue.put(("stopped", filepath))
                        return
                    time.sleep(0.1)
                
                try:
                    img = Image.open(filepath)
                    prompt = self._create_prompt()
                    response = model.generate_content([prompt, img], request_options={'timeout': 120})
                    
                    # Clean and parse the response
                    response_text = response.text.strip()
                    if response_text.startswith("```json"):
                        response_text = response_text[7:]
                    if response_text.endswith("```"):
                        response_text = response_text[:-3]
                    
                    metadata = json.loads(response_text)
                    self.results_queue.put(("success", filepath, metadata))
                    
                except UnidentifiedImageError:
                    self.results_queue.put(("error", filepath, "Invalid image file"))
                except json.JSONDecodeError:
                    self.results_queue.put(("error", filepath, "Invalid response format"))
                except Exception as e:
                    self.results_queue.put(("error", filepath, str(e)))
            
            self.results_queue.put(("finished", None))
            
        except Exception as e:
            self.results_queue.put(("error", None, f"Processing failed: {str(e)}"))

    def _create_prompt(self):
        return """Analyze this image and generate metadata in JSON format with these fields:
- "title": A descriptive title (5-10 words)
- "keywords": Comma-separated relevant keywords (10-20 items)
- "description": A detailed description (50-100 words)

Return only the JSON object, like this:
{"title": "...", "keywords": "...", "description": "..."}"""

    def _check_processing_results(self):
        try:
            while True:
                result = self.results_queue.get_nowait()
                
                if result[0] == "success":
                    _, filepath, metadata = result
                    iid = self.file_iid_map[filepath]
                    self.tree.item(iid, values=(
                        os.path.basename(filepath),
                        metadata.get("title", "N/A"),
                        metadata.get("keywords", "N/A"),
                        metadata.get("description", "N/A")
                    ))
                    self.processed_files_count += 1
                    self.all_time_stats["files_processed"] += 1
                    self.last_24h_stats["files_processed"] += 1
                    
                elif result[0] == "error":
                    _, filepath, error = result
                    if filepath:
                        iid = self.file_iid_map[filepath]
                        self.tree.item(iid, values=(
                            os.path.basename(filepath),
                            "Error",
                            error[:100],
                            ""
                        ))
                    self.processed_files_count += 1
                    
                elif result[0] == "stopped":
                    self._finish_processing(cancelled=True)
                    return
                    
                elif result[0] == "finished":
                    self._finish_processing()
                    return
                
                # Update progress
                progress = self.processed_files_count / len(self.selected_files)
                self.progress_bar.set(progress)
                elapsed = time.time() - self.current_batch_start_time
                self.time_label.configure(text=f"Time: {time.strftime('%M:%S', time.gmtime(elapsed))}")
                
        except queue.Empty:
            pass
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.after(100, self._check_processing_results)

    def _finish_processing(self, cancelled=False):
        if self.current_batch_start_time:
            elapsed = time.time() - self.current_batch_start_time
            self.total_processing_time += elapsed
            self.time_label.configure(text=f"Time: {time.strftime('%M:%S', time.gmtime(elapsed))}")
        
        self.progress_bar.set(1)
        self.start_button.configure(state="normal")
        self.pause_button.configure(state="disabled")
        self.update_metadata_button.configure(state="normal")
        self.export_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        
        if cancelled:
            self.status_label.configure(text="Processing cancelled", text_color="red")
        else:
            self.status_label.configure(text="Processing complete", text_color="green")
            self._save_stats()
            self.update_stats_display()

    def pause_processing(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.configure(text="▶ Resume")
            self.status_label.configure(text="Paused", text_color="orange")
        else:
            self.pause_button.configure(text="❚❚ Pause")
            self.status_label.configure(text="Processing...", text_color="orange")

    def update_image_metadata(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "No files selected in the table")
            return
        
        if not messagebox.askyesno("Confirm", f"Update metadata for {len(selected_items)} selected image(s)?"):
            return
        
        success_count = 0
        error_count = 0
        
        for item in selected_items:
            values = self.tree.item(item)['values']
            if len(values) < 4 or values[1] in ["Pending...", "Error"]:
                continue
            
            filepath = None
            for path, iid in self.file_iid_map.items():
                if iid == item:
                    filepath = path
                    break
            
            if not filepath:
                continue
            
            try:
                # Get metadata from table
                title = values[1]
                keywords = values[2]
                description = values[3]
                
                # Open the image
                img = Image.open(filepath)
                
                # Load existing EXIF or create new
                exif_dict = piexif.load(img.info['exif']) if 'exif' in img.info else {
                    "0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None
                }
                
                # Update EXIF metadata
                if title:
                    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = title.encode('utf-8')
                if description:
                    exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(
                        description, encoding="unicode")
                
                # Update timestamps
                now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
                exif_dict["0th"][piexif.ImageIFD.DateTime] = now
                exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = now
                exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = now
                
                # Create XMP metadata for keywords
                xmp = f"""<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 5.4.0">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">
            <dc:subject>
                <rdf:Bag>
                    <rdf:li>{keywords}</rdf:li>
                </rdf:Bag>
            </dc:subject>
        </rdf:Description>
    </rdf:RDF>
</x:xmpmeta>""".encode('utf-8')
                
                # Save to temporary file first (safety measure)
                temp_path = os.path.join(tempfile.gettempdir(), f"temp_{os.path.basename(filepath)}")
                exif_bytes = piexif.dump(exif_dict)
                
                if filepath.lower().endswith(('.jpg', '.jpeg')):
                    img.save(temp_path, exif=exif_bytes, quality=95, xmp=xmp)
                elif filepath.lower().endswith('.png'):
                    img.save(temp_path, exif=exif_bytes, xmp=xmp)
                else:
                    img.save(temp_path)
                
                img.close()
                
                # Replace original file
                backup_path = filepath + ".bak"
                os.replace(filepath, backup_path)
                
                try:
                    os.replace(temp_path, filepath)
                    os.remove(backup_path)
                    success_count += 1
                except Exception as e:
                    if os.path.exists(backup_path):
                        os.replace(backup_path, filepath)
                    raise e
                
            except Exception as e:
                error_count += 1
                print(f"Error updating metadata for {filepath}: {str(e)}")
        
        messagebox.showinfo("Complete", 
                          f"Metadata update complete\n\nSuccess: {success_count}\nFailed: {error_count}")

    def export_to_csv(self):
        if not self.tree.get_children():
            messagebox.showwarning("Warning", "No data to export")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save CSV File"
        )
        
        if not filepath:
            return
            
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write headers
                writer.writerow([self.tree.heading(col)["text"] for col in self.tree["columns"]])
                # Write data
                for item in self.tree.get_children():
                    writer.writerow(self.tree.item(item)["values"])
                    
            messagebox.showinfo("Success", f"Data exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def clear_all(self):
        if self.processing_thread and self.processing_thread.is_alive():
            if messagebox.askyesno("Confirm", "Processing is running. Stop and clear all?"):
                self.stop_processing_event.set()
                self.is_paused = False
            else:
                return
                
        self.selected_files = []
        self.file_iid_map = {}
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.progress_bar.set(0)
        self.status_label.configure(text="Ready", text_color="white")
        self.time_label.configure(text="Time: 00:00")

    def update_stats_display(self):
        current_time = time.time()
        if current_time - self.last_24h_stats["timestamp"] > 86400:  # 24 hours
            self.last_24h_stats = {"files_processed": 0, "timestamp": current_time}
            
        self.files_processed_label.configure(
            text=f"Processed: {self.processed_files_count}/{len(self.selected_files)}"
        )

    def on_closing(self):
        self._save_config()
        self._save_stats()
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_processing_event.set()
            self.processing_thread.join(timeout=1)
        self.destroy()

if __name__ == "__main__":
    app = ImageMetaGenerator()
    app.mainloop()