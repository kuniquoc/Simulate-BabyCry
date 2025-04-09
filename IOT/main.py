import tkinter as tk
from audio_recorder import AudioRecorder
from ui import RecorderUI
import os

"""
Audio Recorder Application

This application records audio in 3-second windows with a 1-second slide,
sending each chunk to an external API.

To run this application:
1. Install required packages: pip install pyaudio numpy requests
2. Run this script: python main.py
3. Use the GUI to start/stop recording
4. Audio chunks will be sent to the configured API endpoint
"""

def main():
    """
    Main entry point for the application.
    Sets up the audio recorder with 3-second windows and 1-second sliding,
    and initializes the UI.
    """
    # API endpoint configuration
    api_url = "http://localhost:8000/predict_with_timestamp"  # Replace with your actual API endpoint
    
    # Create output directory for audio chunks if it doesn't exist
    os.makedirs("recorded_chunks", exist_ok=True)
    
    # Initialize the audio recorder with 3-second windows and 1-second sliding
    recorder = AudioRecorder(
        window_size=3,    # Each audio segment is 3 seconds long
        slide_size=1,     # Window slides by 1 second each time
        sample_rate=16000, # 16kHz sample rate for good speech quality
        api_url=api_url
    )
    
    # Set up the UI
    root = tk.Tk()
    app = RecorderUI(root, recorder)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()
