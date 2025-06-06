import tkinter as tk
from tkinter import ttk
class RecorderUI:
    def __init__(self, root, recorder):
        self.root = root
        self.recorder = recorder
        
        self.root.title("Audio Recorder with Sliding Window")
        self.root.geometry("400x300")  # Increased height for new elements
        self.root.resizable(False, False)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Audio Recorder", font=("Arial", 16))
        title_label.pack(pady=10)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(side=tk.LEFT)
        
        # Info frame
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="Window Size: 3s | Slide Size: 1s").pack(pady=5)
        
        # Chunks info
        self.chunks_var = tk.StringVar(value="Processed Chunks: 0")
        chunks_label = ttk.Label(info_frame, textvariable=self.chunks_var)
        chunks_label.pack(pady=5)
        
        # WebSocket status frame
        ws_frame = ttk.Frame(main_frame)
        ws_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ws_frame, text="WebSocket Status:").pack(side=tk.LEFT, padx=5)
        self.ws_status_var = tk.StringVar(value="Not connected")
        self.ws_status_label = ttk.Label(ws_frame, textvariable=self.ws_status_var, foreground="orange")
        self.ws_status_label.pack(side=tk.LEFT)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        self.record_button = ttk.Button(buttons_frame, text="Start Recording", command=self.toggle_recording)
        self.record_button.pack(side=tk.LEFT, padx=5, expand=True)
        
        self.exit_button = ttk.Button(buttons_frame, text="Exit", command=self.on_exit)
        self.exit_button.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Update chunk counter and WebSocket status periodically
        self.update_ui_info()
        
    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.recorder.start_recording()
            self.status_var.set("Recording")
            self.status_label.config(foreground="red")
            self.record_button.config(text="Stop Recording")
        else:
            self.recorder.stop_recording()
            self.status_var.set("Ready")
            self.status_label.config(foreground="blue")
            self.record_button.config(text="Start Recording")
    
    def update_ui_info(self):
        # Update chunk counter
        self.chunks_var.set(f"Processed Chunks: {self.recorder.save_counter}")
        
        # Update WebSocket status
        ws_status = self.recorder.last_ws_status
        self.ws_status_var.set(ws_status)
        
        # Set color based on status
        if "Connected" in ws_status or "Data sent" in ws_status:
            self.ws_status_label.config(foreground="green")
        elif "Error" in ws_status or "Disconnected" in ws_status:
            self.ws_status_label.config(foreground="red")
        else:
            self.ws_status_label.config(foreground="orange")
        
        # Schedule next update
        self.root.after(500, self.update_ui_info)
        
    def on_exit(self):
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        self.recorder.close()
        self.root.destroy()
