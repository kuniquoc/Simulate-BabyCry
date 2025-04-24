import tkinter as tk
from audio_recorder import AudioRecorder
from ui import RecorderUI
import os

"""
Audio Recorder Application

This application records audio in 3-second windows with a 1-second slide,
sending each chunk through WebSocket for real-time processing.

To run this application:
1. Install required packages: pip install -r requirements.txt
2. Run this script: python main.py
3. Use the GUI to start/stop recording
4. Audio chunks will be sent through WebSocket for processing
"""

def main():
    """
    Main entry point for the application.
    Sets up the audio recorder with 3-second windows and 1-second sliding,
    and initializes the UI.
    """
    # WebSocket endpoint configuration
    ws_url = "ws://localhost:8000/ws/3a54299f-37d8-452e-b048-7cb7711fe90f"
    
    # Create output directory for audio chunks if it doesn't exist
    os.makedirs("recorded_chunks", exist_ok=True)
    
    # Initialize the audio recorder with 3-second windows and 1-second sliding
    recorder = AudioRecorder(
        window_size=3,      # Each audio segment is 3 seconds long
        slide_size=1,       # Window slides by 1 second each time
        sample_rate=16000,  # 16kHz sample rate for good speech quality
        ws_url=ws_url       # WebSocket endpoint
    )
    
    # Set up the UI
    root = tk.Tk()
    app = RecorderUI(root, recorder)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()
