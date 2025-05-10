import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import csv
import json
import time
import threading
from PIL import Image, UnidentifiedImageError, ExifTags
import google.generativeai as genai
import piexif
import piexif.helper
import tempfile # For temporary JPG conversion
import sys 
import pathlib

# tkinterdnd2 import
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_ENABLED = True
except ImportError:
    DND_ENABLED = False
    print("tkinterdnd2 library not found. Drag and drop will be disabled.")
    print("Install it with: pip install tkinterdnd2")

CONFIG_FILE = "api_config.json"


# --- Configuration ---
APP_NAME = "ImageMetadataGenerator" # Give a name for your application

def get_config_dir():
    """Finds the user's own configuration directory."""
    if sys.platform == "win32": # For Windows
        path = pathlib.Path(os.getenv("APPDATA", "")) / APP_NAME
    elif sys.platform == "darwin": # For macOS 
        path = pathlib.Path.home() / "Library" / "Application Support" / APP_NAME
    else: # For Linux and other Unix-like systems
        path = pathlib.Path.home() / ".config" / APP_NAME
    
    # If the directory does not exist, create it.
    path.mkdir(parents=True, exist_ok=True)
    return path

CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "api_config.json" # Now CONFIG_FILE is a path object

# --- Main Application Class ---
class ImageMetadataApp:
    def __init__(self, master_root):
        if DND_ENABLED:
            self.master = TkinterDnD.Tk()
        else:
            self.master = tk.Tk()
        
        self.master.title("Image Metadata Generator (Gemini 1.5 Flash - JSON Mode)")
        self.master.geometry("1000x750")

        self.api_key = tk.StringVar()
        self.load_api_key()

        # Sliders are now for word limits
        self.title_word_limit = tk.IntVar(value=15)     # Default 5-10 words
        self.keyword_items_limit = tk.IntVar(value=40) # Default 10-15 items
        self.desc_word_limit = tk.IntVar(value=100)     # Default 50-100 words

        self.is_processing = False
        self.is_paused = False
        self.stop_processing_flag = threading.Event()
        self.file_data = []
        
        self.gemini_model = None

        self.create_widgets()
        
        if DND_ENABLED:
            self.tree.drop_target_register(DND_FILES)
            self.tree.dnd_bind('<<Drop>>', self.handle_drop)
        
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_prompt(self):
        # Using exact word/item limits from sliders
        return f"""Analyze this image and generate metadata in JSON format with these fields:
- "title": A descriptive title (exactly {self.title_word_limit.get()} words)
- "keywords": Comma-separated relevant keywords (exactly {self.keyword_items_limit.get()} items)
- "description": A detailed description (exactly {self.desc_word_limit.get()} words)

Return *only* the JSON object itself, without any surrounding text or markdown, like this:
{{"title": "...", "keywords": "...", "description": "..."}}"""


    def on_closing(self):
        # (No changes from previous version)
        if self.is_processing:
            if messagebox.askyesno("Exit", "Processing ongoing. Exit and stop?"):
                self.stop_processing_flag.set()
                if hasattr(self, 'processing_thread') and self.processing_thread.is_alive():
                    self.processing_thread.join(timeout=2)
                self.master.destroy()
            else: return
        else: self.master.destroy()

    def create_widgets(self):
        # --- API Key Section --- (No changes)
        api_frame = ttk.LabelFrame(self.master, text="API Configuration", padding=10)
        api_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(api_frame, text="Api Key:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key, width=40, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(api_frame, text="Validate", command=self.validate_api).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(api_frame, text="Save Api", command=self.save_api_key).grid(row=0, column=3, padx=5, pady=5)
        api_frame.grid_columnconfigure(1, weight=1)

        # --- Word Limits Section ---
        limits_frame = ttk.LabelFrame(self.master, text="Output Length Guidelines (Words/Items)", padding=10)
        limits_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(limits_frame, text="Title Words:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.title_slider = ttk.Scale(limits_frame, from_=5, to=20, orient="horizontal", variable=self.title_word_limit, command=lambda v: self.title_limit_val_label.config(text=f"{int(float(v))}"))
        self.title_slider.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.title_limit_val_label = ttk.Label(limits_frame, text=str(self.title_word_limit.get()), width=3)
        self.title_limit_val_label.grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(limits_frame, text="Keyword Items:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.keyword_slider = ttk.Scale(limits_frame, from_=5, to=25, orient="horizontal", variable=self.keyword_items_limit, command=lambda v: self.keyword_limit_val_label.config(text=f"{int(float(v))}"))
        self.keyword_slider.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.keyword_limit_val_label = ttk.Label(limits_frame, text=str(self.keyword_items_limit.get()), width=3)
        self.keyword_limit_val_label.grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(limits_frame, text="Desc Words:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.desc_slider = ttk.Scale(limits_frame, from_=25, to=150, orient="horizontal", variable=self.desc_word_limit, command=lambda v: self.desc_limit_val_label.config(text=f"{int(float(v))}"))
        self.desc_slider.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.desc_limit_val_label = ttk.Label(limits_frame, text=str(self.desc_word_limit.get()), width=3)
        self.desc_limit_val_label.grid(row=2, column=2, padx=5, pady=5)
        
        limits_frame.grid_columnconfigure(1, weight=1)

        # --- Input & Processing Controls Section --- (No changes)
        controls_frame_outer = ttk.Frame(self.master, padding=5)
        controls_frame_outer.pack(fill="x", padx=5)
        input_controls_frame = ttk.LabelFrame(controls_frame_outer, text="Input & Processing", padding=10)
        input_controls_frame.pack(side="left", fill="x", expand=True)
        ttk.Label(input_controls_frame, text="Input:").pack(side="left", padx=(0,5))
        ttk.Button(input_controls_frame, text="Select Image(s)", command=self.select_image).pack(side="left", padx=2)
        ttk.Button(input_controls_frame, text="Select Folder", command=self.select_folder).pack(side="left", padx=2)
        ttk.Button(input_controls_frame, text="Start", command=self.start_processing).pack(side="left", padx=(10,2))
        self.pause_button = ttk.Button(input_controls_frame, text="Pause", command=self.pause_processing, state="disabled")
        self.pause_button.pack(side="left", padx=2)
        ttk.Button(input_controls_frame, text="Retry Failed", command=self.retry_failed).pack(side="left", padx=2)
        ttk.Button(input_controls_frame, text="Clear List", command=self.clear_table).pack(side="left", padx=(10,2))
        action_buttons_frame = ttk.LabelFrame(controls_frame_outer, text="File Actions", padding=10)
        action_buttons_frame.pack(side="left", padx=(10,0))
        ttk.Button(action_buttons_frame, text="Export CSV", command=self.export_csv).pack(side="left", padx=2)
        ttk.Button(action_buttons_frame, text="Rename File(s)", command=self.rename_files).pack(side="left", padx=2)
        ttk.Button(action_buttons_frame, text="Embed Metadata", command=self.embed_metadata).pack(side="left", padx=2)
        ttk.Button(action_buttons_frame, text="Export As JPG", command=self.export_as_jpg).pack(side="left", padx=2)

        # --- File Data Table Section --- (No changes)
        table_frame = ttk.LabelFrame(self.master, text="Files", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.select_all_var = tk.BooleanVar()
        ttk.Checkbutton(table_frame, text="Select All / Deselect All", variable=self.select_all_var, command=self.toggle_select_all).pack(anchor="w")
        columns = ("select", "filename", "title", "keyword", "description", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("select", text="Sel"); self.tree.heading("filename", text="Filename")
        self.tree.heading("title", text="Title"); self.tree.heading("keyword", text="Keyword")
        self.tree.heading("description", text="Description"); self.tree.heading("status", text="Status")
        self.tree.column("select", width=30, stretch=tk.NO, anchor="center"); self.tree.column("filename", width=250, anchor="w")
        self.tree.column("title", width=200, anchor="w"); self.tree.column("keyword", width=150, anchor="w")
        self.tree.column("description", width=250, anchor="w"); self.tree.column("status", width=100, anchor="w")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview); vsb.pack(side='right', fill='y')
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview); hsb.pack(side='bottom', fill='x')
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.status_bar = ttk.Label(self.master, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)

    # --- API Key Methods --- (No changes)
    def load_api_key(self):
        try:
            # CONFIG_FILE is now a pathlib.Path object
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.api_key.set(config.get("api_key", ""))
        except Exception as e:
            # It is better to show the full path in the error message
            print(f"There was a problem loading the API key. ({CONFIG_FILE}): {e}")

    def save_api_key(self):
        try:
            # CONFIG_FILE is a pathlib.Path object, can be opened directly
            with open(CONFIG_FILE, 'w') as f: 
                json.dump({"api_key": self.api_key.get()}, f)
            # Tell the user where the file is saved
            messagebox.showinfo("API Key", f"API Key Successfully Saved\n{CONFIG_FILE}")
        except Exception as e:
            # It is better to show the full path in the error message
            messagebox.showerror("API Key", f"There was a problem saving the API key. ({CONFIG_FILE}):\n{e}")







    def validate_api(self):
        key = self.api_key.get()
        if not key: messagebox.showwarning("API Validation", "API Key empty."); self.gemini_model=None; return False
        try:
            self.status_bar.config(text="Validating API Key..."); self.master.update_idletasks()
            genai.configure(api_key=key)
            model_to_test = genai.GenerativeModel('gemini-1.5-flash-latest')
            model_to_test.generate_content("test connection", request_options={'timeout': 10})
            self.gemini_model = model_to_test
            messagebox.showinfo("API Validation", "API Key valid."); self.status_bar.config(text="API Key Validated.")
            return True
        except Exception as e:
            self.gemini_model=None; messagebox.showerror("API Validation", f"API Key invalid/network error: {e}")
            self.status_bar.config(text="API Key Validation Failed."); return False

    # --- File Handling & Table Methods --- (No changes)
    def add_files_to_list(self, filepaths):
        new_added=0
        for fp_raw in filepaths:
            fp = fp_raw.strip('{}')
            if not os.path.isfile(fp): continue
            abs_fp = os.path.abspath(fp)
            if not any(i['filepath'] == abs_fp for i in self.file_data):
                try:
                    with Image.open(fp): pass
                    item_id = self.tree.insert("", "end", values=("☐",os.path.basename(fp),"","","","Pending"))
                    self.file_data.append({"id":item_id,"selected":False,"filepath":abs_fp,"filename":os.path.basename(fp),
                                           "title":"","keyword":"","description":"","status":"Pending"})
                    new_added+=1
                except UnidentifiedImageError: print(f"Skipping unidentified: {fp}")
                except Exception as e: print(f"Error adding {fp}: {e}")
        if new_added > 0: self.status_bar.config(text=f"Added {new_added} file(s).")
        self.update_select_all_checkbox_state()
    def update_treeview_item(self, item_data):
        if self.tree.exists(item_data["id"]):
            self.tree.item(item_data["id"], values=("☑" if item_data["selected"] else "☐", item_data["filename"],
                                                    item_data["title"],item_data["keyword"],item_data["description"],item_data["status"]))
    def select_image(self):
        fps = filedialog.askopenfilenames(title="Select Images", filetypes=(("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff"),("All","*.*")))
        if fps: self.add_files_to_list(fps)
    def select_folder(self):
        f_path = filedialog.askdirectory(title="Select Folder")
        if f_path:
            fps = [os.path.join(f_path,f) for f in os.listdir(f_path) if f.lower().endswith((".jpg",".jpeg",".png",".webp",".bmp",".tiff"))]
            if fps: self.add_files_to_list(fps)
            else: messagebox.showinfo("Select Folder", "No supported images found.")
    def handle_drop(self, event):
        fps_str = event.data; fps = []
        if '{' in fps_str and '}' in fps_str:
            import re; paths = re.findall(r'\{([^}]+)\}|([^{}\s]+)', fps_str)
            fps = [p[0] if p[0] else p[1] for p in paths]
        else: fps = fps_str.split()
        valid_fps = [fp for fp in fps if os.path.isfile(fp.strip('{}')) and fp.lower().endswith((".jpg",".jpeg",".png",".webp",".bmp",".tiff"))]
        if valid_fps: self.add_files_to_list(valid_fps)
        elif fps: messagebox.showwarning("Drag & Drop", "No valid images dropped.")
    def on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            col_id, item_iid = self.tree.identify_column(event.x), self.tree.identify_row(event.y)
            if item_iid and col_id == "#1":
                for item in self.file_data:
                    if item["id"] == item_iid:
                        item["selected"] = not item["selected"]; self.update_treeview_item(item)
                        self.update_select_all_checkbox_state(); break
    def toggle_select_all(self):
        state = self.select_all_var.get()
        for item in self.file_data: item["selected"]=state; self.update_treeview_item(item)
    def update_select_all_checkbox_state(self):
        if not self.file_data: self.select_all_var.set(False); return
        self.select_all_var.set(all(item["selected"] for item in self.file_data))
    def clear_table(self):
        if self.is_processing: messagebox.showwarning("Clear", "Cannot clear while processing."); return
        if messagebox.askyesno("Confirm Clear", "Clear all items?"):
            for i in self.tree.get_children(): self.tree.delete(i)
            self.file_data.clear(); self.select_all_var.set(False)
            self.status_bar.config(text="List cleared.")

    # --- Processing Methods ---
    def start_processing(self): # (No changes)
        if self.is_processing: messagebox.showinfo("Processing", "Already in progress."); return
        if not self.api_key.get(): messagebox.showerror("API Error", "Enter API key."); return
        if not self.gemini_model and not self.validate_api(): messagebox.showerror("API Error", "Validate API key."); return
        to_process = [i for i in self.file_data if i["selected"] and i["status"] not in ["Completed","Processing..."]]
        if not to_process:
            to_process = [i for i in self.file_data if i["status"] not in ["Completed","Processing..."]]
            if not to_process: messagebox.showinfo("Processing", "No items to process."); return
        self.is_processing=True; self.is_paused=False; self.stop_processing_flag.clear()
        self.pause_button.config(text="Pause",state="normal"); self.status_bar.config(text="Processing...")
        self.processing_thread = threading.Thread(target=self.process_files_thread, args=(to_process,),daemon=True)
        self.processing_thread.start()
    def _generate_gemini_content_json(self, pil_image, prompt_text): # (No changes)
        if self.stop_processing_flag.is_set(): return None, "Stopped"
        try:
            response = self.gemini_model.generate_content([prompt_text, pil_image], request_options={'timeout':90})
            return response.text.strip() if response and response.text else None, "Completed"
        except Exception as e:
            print(f"Gemini API error: {e}")
            if "API key not valid" in str(e) or "API_KEY_INVALID" in str(e): return None, "API Key Error"
            return None, f"API Error: {str(e)[:50]}"
    def process_files_thread(self, items_to_process): # (No changes)
        prompt = self._create_prompt()
        for item_data in items_to_process:
            if self.stop_processing_flag.is_set(): item_data["status"]="Stopped"; self.master.after(0,self.update_treeview_item,item_data); break
            while self.is_paused:
                if self.stop_processing_flag.is_set(): break
                time.sleep(0.5)
            if self.stop_processing_flag.is_set(): item_data["status"]="Stopped"; self.master.after(0,self.update_treeview_item,item_data); break
            item_data["status"]="Processing..."; self.master.after(0,self.update_treeview_item,item_data)
            try:
                with Image.open(item_data['filepath']) as pil_image:
                    img_to_send = pil_image
                    if pil_image.mode not in ['RGB','RGBA']: img_to_send = pil_image.convert('RGB')
                    json_text, api_status = self._generate_gemini_content_json(img_to_send, prompt)
                if api_status == "API Key Error":
                    item_data["status"]=api_status; self.master.after(0,self.update_treeview_item,item_data)
                    self.master.after(0,lambda: messagebox.showerror("API Error","API Key error. Processing stopped."))
                    break
                if api_status != "Completed" or not json_text:
                    item_data["status"] = api_status if api_status != "Completed" else "No Response"
                    self.master.after(0,self.update_treeview_item,item_data); continue
                try:
                    if json_text.startswith("```json"): json_text = json_text.strip("```json").strip("`").strip()
                    metadata = json.loads(json_text)
                    item_data["title"]=metadata.get("title",""); item_data["keyword"]=metadata.get("keywords","")
                    item_data["description"]=metadata.get("description",""); item_data["status"]="Completed"
                except json.JSONDecodeError as je: print(f"JSON Decode Error: {je} for {json_text}"); item_data["status"]="Bad JSON"
                except Exception as ep: print(f"Parse Error: {ep}"); item_data["status"]="Parse Error"
            except UnidentifiedImageError: item_data["status"]="Bad Image"
            except Exception as e: print(f"Processing Error: {e}"); item_data["status"]=f"Error: {str(e)[:30]}"
            self.master.after(0,self.update_treeview_item,item_data)
        self.master.after(0,self.on_processing_finished)
    def on_processing_finished(self): # (No changes)
        self.is_processing=False; self.is_paused=False; self.pause_button.config(text="Pause",state="disabled")
        api_err = any(i["status"]=="API Key Error" for i in self.file_data)
        if self.stop_processing_flag.is_set(): self.status_bar.config(text="Processing stopped by user.")
        elif api_err: self.status_bar.config(text="Processing stopped due to API Key Error.")
        else: self.status_bar.config(text="Processing finished.")
    def pause_processing(self): # (No changes)
        if not self.is_processing: return
        self.is_paused = not self.is_paused; self.pause_button.config(text="Resume" if self.is_paused else "Pause")
        self.status_bar.config(text="Processing Paused." if self.is_paused else "Processing Resumed...")
    def retry_failed(self): # (No changes)
        if self.is_processing: messagebox.showwarning("Retry","Cannot retry while processing."); return
        to_retry = [i for i in self.file_data if i["selected"] and i["status"] not in ["Completed","Pending","Processing..."]]
        if not to_retry:
            to_retry = [i for i in self.file_data if i["status"] not in ["Completed","Pending","Processing..."]]
            if not to_retry: messagebox.showinfo("Retry","No failed/stopped items."); return
        for item in to_retry: item["status"]="Pending"; self.update_treeview_item(item)
        self.start_processing()
    def get_selected_items_data(self, require_completed=False, require_selected=True): # Added require_selected
        if require_selected:
            selected = [item for item in self.file_data if item["selected"]]
            if not selected:
                if messagebox.askyesno("No Selection", "No items selected. Act on ALL items?"):
                    selected = self.file_data
                else:
                    return []
        else: # Not requiring selection implies all items
             selected = self.file_data

        if require_completed:
            completed_selected = [item for item in selected if item["status"] == "Completed"]
            if not completed_selected and selected : # if items were selected but none completed
                messagebox.showinfo("No Action", "No 'Completed' items among selection.")
                return []
            return completed_selected
        return selected


    # --- Export & File Operations ---
    def export_csv(self):
        items_to_export = self.get_selected_items_data(require_selected=True) # Use updated helper
        if not items_to_export: return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save CSV As"
        )
        if not filepath: return

        try:
            # Define fieldnames to match the keys in your item_data dictionary more directly
            fieldnames = ['filename', 'filepath', 'title', 'keyword', 'description', 'status']
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for item_data in items_to_export:
                    # Create a row dictionary ensuring all fieldnames are present
                    row_to_write = {fn: item_data.get(fn, "") for fn in fieldnames}
                    writer.writerow(row_to_write)
            messagebox.showinfo("Export CSV", f"Data exported to {filepath}")
            self.status_bar.config(text=f"CSV exported: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Export CSV", f"Error exporting CSV: {e}")

    def _convert_to_jpg_and_update_item(self, item_data, target_filepath=None, delete_original_png=False):
        """Converts an image to JPG. Updates item_data if successful. Returns new JPG path or None."""
        original_filepath = item_data['filepath']
        try:
            img = Image.open(original_filepath)
            if img.mode == 'RGBA' or img.mode == 'P': # P mode for paletted PNGs often has transparency
                img = img.convert('RGB') # Convert to RGB, removing alpha

            if target_filepath is None: # If no target, create temp
                # Create a temporary JPG file
                temp_jpg_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                new_jpg_path = temp_jpg_file.name
                temp_jpg_file.close() # Close it so Pillow can write to it
            else:
                new_jpg_path = target_filepath
            
            # Preserve EXIF if any from original (though PNGs usually don't have much)
            exif_data = img.info.get('exif')
            if exif_data:
                img.save(new_jpg_path, "JPEG", quality=90, optimize=True, exif=exif_data)
            else:
                img.save(new_jpg_path, "JPEG", quality=90, optimize=True)
            img.close()

            print(f"Converted '{original_filepath}' to '{new_jpg_path}'")
            
            # If a permanent conversion, update item_data
            if target_filepath: # This implies a permanent change
                if delete_original_png and original_filepath.lower().endswith(".png") and original_filepath != new_jpg_path:
                    try:
                        os.remove(original_filepath)
                        print(f"Deleted original PNG: {original_filepath}")
                    except OSError as e_del:
                        print(f"Error deleting original PNG {original_filepath}: {e_del}")

                item_data['filepath'] = new_jpg_path
                item_data['filename'] = os.path.basename(new_jpg_path)
                # No need to update treeview item here, calling function will do it
            return new_jpg_path
        except Exception as e:
            print(f"Error converting {original_filepath} to JPG: {e}")
            return None


    def _embed_single_file_metadata(self, item_data, filepath_to_embed):
        """Helper to embed metadata into a single file (assumed JPG/TIFF)."""
        try:
            if not filepath_to_embed.lower().endswith((".jpg", ".jpeg", ".tiff")):
                print(f"Skipping metadata for {os.path.basename(filepath_to_embed)}: Not JPG/TIFF.")
                return False

            # Reload image to ensure we have the latest version, especially after conversion
            with Image.open(filepath_to_embed) as img:
                try:
                    exif_dict = piexif.load(img.info.get('exif', b''))
                except piexif.InvalidImageDataError:
                    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

                if item_data.get("title"):
                    exif_dict["0th"][piexif.ImageIFD.XPTitle] = item_data["title"].encode('utf-16le')
                if item_data.get("keyword"):
                    exif_dict["0th"][piexif.ImageIFD.XPKeywords] = item_data["keyword"].replace(",",";").strip().encode('utf-16le')
                if item_data.get("description"):
                    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = item_data["description"].encode('utf-8')
                    exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.dump_comment(item_data["description"])
                
                exif_bytes = piexif.dump(exif_dict)
                # Save in place
                img.save(filepath_to_embed, exif=exif_bytes) 
            print(f"Embedded metadata for {os.path.basename(filepath_to_embed)}")
            return True
        except UnidentifiedImageError:
            print(f"Could not open/identify image for metadata: {os.path.basename(filepath_to_embed)}")
        except Exception as e:
            print(f"Error embedding metadata for {os.path.basename(filepath_to_embed)}: {e}")
        return False


    def embed_metadata(self):
        items_to_embed = self.get_selected_items_data(require_completed=True, require_selected=True)
        if not items_to_embed: return

        embedded_count = 0
        error_count = 0
        temp_files_to_clean = []

        for item_data in items_to_embed:
            filepath_for_embedding = item_data['filepath']
            original_is_png = item_data['filepath'].lower().endswith(".png")
            converted_to_temp_jpg = False

            if original_is_png:
                # Convert PNG to a temporary JPG for metadata embedding
                if not messagebox.askyesno("PNG Detected", f"'{item_data['filename']}' is a PNG. "
                                                       f"Metadata can only be embedded in a JPG copy.\n\n"
                                                       f"Do you want to save a JPG copy and embed metadata into it? "
                                                       f"You'll be asked where to save the new JPG."):
                    error_count += 1
                    continue

                # Ask user where to save the new JPG
                original_basename, _ = os.path.splitext(item_data['filename'])
                new_jpg_save_path = filedialog.asksaveasfilename(
                    initialfile=original_basename + ".jpg",
                    defaultextension=".jpg",
                    filetypes=[("JPEG files", "*.jpg")],
                    title=f"Save PNG '{item_data['filename']}' as JPG for metadata"
                )
                if not new_jpg_save_path: # User cancelled save dialog
                    error_count +=1
                    continue

                converted_path = self._convert_to_jpg_and_update_item(item_data, target_filepath=new_jpg_save_path, delete_original_png=False) # Don't delete original here
                if converted_path:
                    filepath_for_embedding = converted_path
                    # Update the item in the list to reflect the new JPG file
                    item_data['filepath'] = converted_path
                    item_data['filename'] = os.path.basename(converted_path)
                    self.update_treeview_item(item_data) # Update the tree view
                else:
                    error_count += 1
                    continue # Failed conversion

            # Now embed metadata into filepath_for_embedding (which is either original JPG/TIFF or new JPG)
            if self._embed_single_file_metadata(item_data, filepath_for_embedding):
                embedded_count += 1
            else:
                error_count += 1
        
        messagebox.showinfo("Embed Metadata", f"Embedded metadata in {embedded_count} file(s). {error_count} errors/skips.")
        self.status_bar.config(text=f"Embedded metadata in {embedded_count} files.")


    def export_as_jpg(self):
        items_to_export = self.get_selected_items_data(require_selected=True) # Don't require completed
        if not items_to_export: return

        exported_and_embedded_count = 0
        error_count = 0

        for item_data in items_to_export:
            original_filepath = item_data['filepath']
            original_basename, _ = os.path.splitext(item_data['filename'])
            
            # Ask where to save the new JPG
            new_jpg_save_path = filedialog.asksaveasfilename(
                initialfile=original_basename + ".jpg",
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg")],
                title=f"Export '{item_data['filename']}' as JPG"
            )
            if not new_jpg_save_path: # User cancelled
                error_count +=1
                continue

            # Convert (or copy if already JPG) to the new path
            converted_jpg_path = None
            if original_filepath.lower() == new_jpg_save_path.lower() and original_filepath.lower().endswith((".jpg", ".jpeg")):
                 # If saving to the same JPG path, we just need to ensure it's RGB and then embed
                try:
                    img = Image.open(original_filepath)
                    if img.mode != 'RGB': img = img.convert('RGB')
                    # Save it to ensure it's a clean JPG copy if any conversion happened
                    img.save(new_jpg_save_path, "JPEG", quality=90, optimize=True)
                    img.close()
                    converted_jpg_path = new_jpg_save_path
                except Exception as e:
                    print(f"Error preparing existing JPG {original_filepath}: {e}")
                    error_count+=1
                    continue
            else:
                # Use the conversion helper, it will save to new_jpg_save_path
                converted_jpg_path = self._convert_to_jpg_and_update_item(item_data, target_filepath=new_jpg_save_path, delete_original_png=False) # Don't update item_data here yet

            if not converted_jpg_path:
                error_count += 1
                continue

            # If metadata is available and generated, embed it into the new JPG
            if item_data["status"] == "Completed":
                if self._embed_single_file_metadata(item_data, converted_jpg_path):
                    print(f"Metadata embedded into exported JPG: {os.path.basename(converted_jpg_path)}")
                else:
                    print(f"Could not embed metadata into exported JPG: {os.path.basename(converted_jpg_path)}")
                    # Continue with export, but note metadata embedding failure
            
            exported_and_embedded_count += 1
            # If the export target is different from the item's current path,
            # we don't update the item_data in the table, as it's an "export as" operation.
            # If the user selected to overwrite an existing item, the conversion would have handled it.

        if exported_and_embedded_count > 0:
            messagebox.showinfo("Export as JPG", f"Successfully exported {exported_and_embedded_count} file(s) as JPG (metadata embedded where applicable).")
            self.status_bar.config(text=f"Exported {exported_and_embedded_count} file(s) as JPG.")
        elif error_count > 0 and exported_and_embedded_count == 0:
             messagebox.showwarning("Export as JPG", "No files were exported due to errors or cancellations.")


    def rename_files(self): # (No changes from previous version)
        items_to_rename = self.get_selected_items_data(require_completed=True, require_selected=True)
        if not items_to_rename: return
        renamed_count, error_count = 0,0
        for item in items_to_rename:
            if item["title"]:
                _, ext = os.path.splitext(item["filepath"])
                dir_n = os.path.dirname(item["filepath"])
                new_fn_base = "".join(c if c.isalnum() or c in " _-" else "_" for c in item["title"]).strip()[:100]
                if not new_fn_base: error_count+=1; continue
                new_fp = os.path.join(dir_n, new_fn_base + ext)
                if item["filepath"].lower() == new_fp.lower(): continue
                if os.path.exists(new_fp) and not messagebox.askyesno("Exists",f"'{os.path.basename(new_fp)}' exists. Overwrite?"):
                    error_count+=1; continue
                try:
                    os.rename(item["filepath"], new_fp)
                    item["filepath"],item["filename"] = new_fp,os.path.basename(new_fp)
                    self.update_treeview_item(item); renamed_count+=1
                except Exception as e: messagebox.showerror("Rename Error",f"Could not rename {item['filename']}:\n{e}"); error_count+=1
        messagebox.showinfo("Rename Files", f"Renamed {renamed_count} files. {error_count} errors/skips.")
        self.status_bar.config(text=f"Renamed {renamed_count} files.")

    def run(self):
        self.master.mainloop()

if __name__ == "__main__":
    app_gui = ImageMetadataApp(None)
    app_gui.run()
