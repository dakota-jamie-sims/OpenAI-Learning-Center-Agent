#!/usr/bin/env python3
"""
Dakota Content Generator - Mac Desktop App
A native Mac application for generating investment content
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import subprocess
import json
import threading
import queue
from datetime import datetime
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Embedded API Keys (replaced during build)
EMBEDDED_CONFIG = {
    "OPENAI_API_KEY": "%%OPENAI_API_KEY%%",
    "VECTOR_STORE_ID": "%%VECTOR_STORE_ID%%", 
    "SERPER_API_KEY": "%%SERPER_API_KEY%%"
}

class DakotaGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dakota Content Generator")
        self.root.geometry("600x650")
        self.root.resizable(False, False)
        
        # Set app icon if available
        try:
            if sys.platform == "darwin":
                self.root.iconbitmap("dakota_icon.icns")
        except:
            pass
            
        # Variables
        self.topic_var = tk.StringVar()
        self.word_count_var = tk.IntVar(value=1750)
        self.data_file_var = tk.StringVar(value="")
        self.save_location_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.progress_text_var = tk.StringVar(value="Ready to generate")
        
        # Set default save location
        default_save = os.path.expanduser("~/Documents/Dakota-Articles")
        self.save_location_var.set(default_save)
        
        # Queue for thread communication
        self.queue = queue.Queue()
        
        # Create GUI
        self.create_widgets()
        
        # Load saved preferences
        self.load_preferences()
        
        # Start queue processor
        self.process_queue()
        
    def create_widgets(self):
        """Create all GUI elements"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Dakota Content Generator",
            font=("SF Pro Display", 24, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Topic Section
        ttk.Label(
            main_frame, 
            text="Topic:",
            font=("SF Pro Text", 14)
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        topic_entry = ttk.Entry(
            main_frame,
            textvariable=self.topic_var,
            font=("SF Pro Text", 12),
            width=50
        )
        topic_entry.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Word Count Section
        ttk.Label(
            main_frame,
            text="Word Count:",
            font=("SF Pro Text", 14)
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        word_count_frame = ttk.Frame(main_frame)
        word_count_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        ttk.Radiobutton(
            word_count_frame,
            text="Short (800)",
            variable=self.word_count_var,
            value=800
        ).grid(row=0, column=0, padx=(0, 20))
        
        ttk.Radiobutton(
            word_count_frame,
            text="Standard (1,750)",
            variable=self.word_count_var,
            value=1750
        ).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Radiobutton(
            word_count_frame,
            text="Long (2,500)",
            variable=self.word_count_var,
            value=2500
        ).grid(row=0, column=2)
        
        # Data Analysis Section
        ttk.Label(
            main_frame,
            text="Data Analysis (Optional):",
            font=("SF Pro Text", 14)
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        # Drop zone frame
        drop_frame = tk.Frame(
            main_frame,
            bg="#f0f0f0",
            relief=tk.RIDGE,
            borderwidth=2,
            height=80
        )
        drop_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        drop_frame.grid_columnconfigure(0, weight=1)
        
        self.drop_label = ttk.Label(
            drop_frame,
            text="📎 Drag spreadsheet here or click to browse...",
            font=("SF Pro Text", 12),
            foreground="#666666"
        )
        self.drop_label.grid(row=0, column=0, pady=25)
        
        # Bind click event
        drop_frame.bind("<Button-1>", lambda e: self.browse_file())
        self.drop_label.bind("<Button-1>", lambda e: self.browse_file())
        
        # File selected label
        self.file_label = ttk.Label(
            main_frame,
            text="",
            font=("SF Pro Text", 11),
            foreground="#007AFF"
        )
        self.file_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        # Save Location Section
        ttk.Label(
            main_frame,
            text="Save Location:",
            font=("SF Pro Text", 14)
        ).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        location_frame = ttk.Frame(main_frame)
        location_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        location_frame.grid_columnconfigure(0, weight=1)
        
        location_entry = ttk.Entry(
            location_frame,
            textvariable=self.save_location_var,
            font=("SF Pro Text", 12)
        )
        location_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(
            location_frame,
            text="Browse...",
            command=self.browse_save_location
        ).grid(row=0, column=1)
        
        # Generate Button
        self.generate_button = ttk.Button(
            main_frame,
            text="Generate Article",
            command=self.generate_article,
            style="Generate.TButton"
        )
        self.generate_button.grid(row=10, column=0, columnspan=2, pady=(20, 10))
        
        # Progress Section
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=560
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.progress_label = ttk.Label(
            self.progress_frame,
            textvariable=self.progress_text_var,
            font=("SF Pro Text", 11),
            foreground="#666666"
        )
        self.progress_label.grid(row=1, column=0)
        
        # Configure styles
        style = ttk.Style()
        style.configure(
            "Generate.TButton",
            font=("SF Pro Text", 14, "bold"),
            foreground="white",
            background="#007AFF"
        )
        
    def browse_file(self):
        """Open file dialog for spreadsheet selection"""
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[
                ("Spreadsheet files", "*.csv *.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.data_file_var.set(filename)
            self.file_label.config(text=f"✓ {os.path.basename(filename)}")
            self.drop_label.config(text="📄 File selected")
            
    def browse_save_location(self):
        """Open directory dialog for save location"""
        directory = filedialog.askdirectory(
            title="Select Save Location",
            initialdir=self.save_location_var.get()
        )
        
        if directory:
            self.save_location_var.set(directory)
            self.save_preferences()
            
    def generate_article(self):
        """Start article generation in background thread"""
        # Validate inputs
        if not self.topic_var.get().strip():
            messagebox.showerror("Error", "Please enter a topic")
            return
            
        # Disable generate button
        self.generate_button.config(state="disabled")
        self.progress_var.set(0)
        
        # Start generation in background thread
        thread = threading.Thread(target=self._generate_article_thread)
        thread.daemon = True
        thread.start()
        
    def _generate_article_thread(self):
        """Run article generation in background"""
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(EMBEDDED_CONFIG)
            
            # Build command
            script_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "scripts",
                "generate_dakota_article_with_data.py" if self.data_file_var.get() else "generate_dakota_article.py"
            )
            
            cmd = [
                sys.executable,
                script_path,
                "--topic", self.topic_var.get(),
                "--word-count", str(self.word_count_var.get())
            ]
            
            if self.data_file_var.get():
                cmd.extend(["--data-file", self.data_file_var.get()])
            
            # Run process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # Parse output for progress
            phase_progress = {
                "Phase 1": 10,
                "Phase 2": 25,
                "Phase 3": 40,
                "Phase 4": 60,
                "Phase 5": 75,
                "Phase 6": 85,
                "Phase 7": 95
            }
            
            output_folder = None
            
            for line in process.stdout:
                # Update progress based on phase
                for phase, progress in phase_progress.items():
                    if phase in line:
                        self.queue.put(("progress", progress, f"Running {phase}..."))
                        
                # Capture output folder
                if "Output folder:" in line:
                    output_folder = line.split("Output folder:")[-1].strip().rstrip("/")
                    
            # Wait for completion
            return_code = process.wait()
            
            if return_code == 0 and output_folder:
                # Move files to user's chosen location
                final_folder = self._move_output_files(output_folder)
                self.queue.put(("complete", final_folder))
            else:
                stderr = process.stderr.read()
                self.queue.put(("error", stderr or "Generation failed"))
                
        except Exception as e:
            self.queue.put(("error", str(e)))
            
    def _move_output_files(self, source_folder):
        """Move generated files to user's chosen location"""
        # Create destination folder
        timestamp = datetime.now().strftime("%Y-%m-%d")
        topic_slug = self.topic_var.get()[:50].replace("/", "-").replace(" ", "-").lower()
        dest_folder = os.path.join(
            self.save_location_var.get(),
            f"{timestamp}-{topic_slug}"
        )
        
        os.makedirs(dest_folder, exist_ok=True)
        
        # Copy files
        if os.path.exists(source_folder):
            for file in os.listdir(source_folder):
                if file.endswith(('.md', '.json')):
                    shutil.copy2(
                        os.path.join(source_folder, file),
                        os.path.join(dest_folder, file)
                    )
                    
        return dest_folder
        
    def process_queue(self):
        """Process messages from background thread"""
        try:
            while True:
                msg = self.queue.get_nowait()
                
                if msg[0] == "progress":
                    _, value, text = msg
                    self.progress_var.set(value)
                    self.progress_text_var.set(text)
                    
                elif msg[0] == "complete":
                    _, folder = msg
                    self.progress_var.set(100)
                    self.progress_text_var.set("Generation complete!")
                    self.generate_button.config(state="normal")
                    
                    # Show completion dialog
                    result = messagebox.showinfo(
                        "Success",
                        f"Article generated successfully!\n\nSaved to:\n{folder}",
                        detail="Click OK to open the folder."
                    )
                    
                    # Open folder
                    if sys.platform == "darwin":
                        subprocess.call(["open", folder])
                    
                    # Reset form
                    self.reset_form()
                    
                elif msg[0] == "error":
                    _, error = msg
                    self.progress_var.set(0)
                    self.progress_text_var.set("Generation failed")
                    self.generate_button.config(state="normal")
                    
                    messagebox.showerror(
                        "Generation Failed",
                        f"An error occurred:\n\n{error[:200]}"
                    )
                    
        except queue.Empty:
            pass
            
        # Schedule next check
        self.root.after(100, self.process_queue)
        
    def reset_form(self):
        """Reset form after successful generation"""
        self.topic_var.set("")
        self.data_file_var.set("")
        self.file_label.config(text="")
        self.drop_label.config(text="📎 Drag spreadsheet here or click to browse...")
        self.progress_var.set(0)
        self.progress_text_var.set("Ready to generate")
        
    def save_preferences(self):
        """Save user preferences"""
        prefs = {
            "save_location": self.save_location_var.get(),
            "word_count": self.word_count_var.get()
        }
        
        prefs_file = os.path.expanduser("~/.dakota_generator_prefs.json")
        with open(prefs_file, "w") as f:
            json.dump(prefs, f)
            
    def load_preferences(self):
        """Load saved preferences"""
        prefs_file = os.path.expanduser("~/.dakota_generator_prefs.json")
        
        if os.path.exists(prefs_file):
            try:
                with open(prefs_file, "r") as f:
                    prefs = json.load(f)
                    
                if "save_location" in prefs:
                    self.save_location_var.set(prefs["save_location"])
                    
                if "word_count" in prefs:
                    self.word_count_var.set(prefs["word_count"])
                    
            except:
                pass


def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Configure for Mac
    if sys.platform == "darwin":
        try:
            root.tk.call("::tk::unsupported::MacWindowStyle", "style", root._w, "moveableModal", "")
        except:
            pass
            
    app = DakotaGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()