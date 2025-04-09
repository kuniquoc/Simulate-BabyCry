import pyaudio
import numpy as np
import wave
import time
import threading
import queue
import os
import requests
import base64
import json
from io import BytesIO

class AudioRecorder:
    """
    Records audio using a sliding window approach.
    
    This class records audio continuously and processes it in overlapping windows.
    With default settings, it creates 3-second audio chunks that slide by 1 second,
    meaning there is a 2-second overlap between consecutive chunks.
    """
    def __init__(self, chunk_size=1024, sample_rate=16000, channels=1, 
                 window_size=3, slide_size=1, format=pyaudio.paInt16,
                 api_url="http://localhost:8000/predict_with_timestamp"):
        """
        Initialize the AudioRecorder with the specified parameters.
        
        Args:
            chunk_size (int): Number of audio frames per buffer
            sample_rate (int): Audio sampling rate in Hz (default 16000)
            channels (int): Number of audio channels (1=mono, 2=stereo)
            window_size (int): Size of each audio segment in seconds (default 3)
            slide_size (int): How much the window slides each time in seconds (default 1)
            format: PyAudio format constant
            api_url (str): URL of the API endpoint to send audio data
        """
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.channels = channels
        self.format = format
        self.window_size = window_size  # in seconds
        self.slide_size = slide_size    # in seconds
        self.api_url = api_url
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        self.frames_per_window = int(sample_rate * window_size)  # Total frames in window (e.g., 48000 frames for 3s at 16kHz)
        self.frames_per_slide = int(sample_rate * slide_size)    # Frames to slide (e.g., 16000 frames for 1s at 16kHz)
        self.chunk_queue = queue.Queue()
        self.save_counter = 0
        self.processing_thread = None
        self.last_api_status = "Not connected"
        
    def start_recording(self):
        """
        Start recording audio from the microphone.
        Creates a new thread for processing the audio in sliding windows.
        """
        if self.is_recording:
            return
            
        self.is_recording = True
        self.audio_buffer = []
        
        def callback(in_data, frame_count, time_info, status):
            """
            Callback function for PyAudio. Receives audio data from the microphone.
            """
            self.audio_buffer.append(np.frombuffer(in_data, dtype=np.int16))
            return (in_data, pyaudio.paContinue)
            
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=callback
        )
        
        # Start a thread to process audio in sliding windows
        self.processing_thread = threading.Thread(target=self._process_audio)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
    def _process_audio(self):
        """
        Process audio in sliding windows.
        
        This method continuously monitors the audio buffer. Once enough data 
        is collected for a window (e.g., 3 seconds), it processes that window
        and then slides forward by slide_size (e.g., 1 second) to prepare for
        the next window.
        """
        frames_accumulated = 0
        samples_per_chunk = self.chunk_size
        buffer_ready = False  # Flag to indicate if we have enough data for a full window
        
        while self.is_recording:
            if len(self.audio_buffer) > 0:
                with self.buffer_lock:
                    # Tính tổng số khung âm thanh đã tích lũy
                    total_samples_in_buffer = sum(len(chunk) for chunk in self.audio_buffer)
                    frames_accumulated = total_samples_in_buffer
                    
                    # Kiểm tra nếu đủ dữ liệu cho một cửa sổ
                    if not buffer_ready and frames_accumulated >= self.frames_per_window:
                        buffer_ready = True
                    
                    # Chỉ xử lý cửa sổ khi có đủ dữ liệu
                    if buffer_ready and frames_accumulated >= self.frames_per_window:
                        # Ghép tất cả các chunk thành một mảng duy nhất
                        flat_buffer = np.concatenate(self.audio_buffer)
                        
                        # Trích xuất cửa sổ cuối cùng (3 giây)
                        window_data = flat_buffer[-self.frames_per_window:]
                        
                        # Kiểm tra độ dài của cửa sổ trước khi xử lý
                        if len(window_data) == self.frames_per_window:
                            self.process_window(window_data)
                        else:
                            print("Not enough data for a full window. Waiting for more data...")
                            continue
                        
                        # Xóa đúng số lượng khung âm thanh tương ứng với slide_size
                        samples_to_remove = self.frames_per_slide
                        while samples_to_remove > 0 and len(self.audio_buffer) > 0:
                            if len(self.audio_buffer[0]) <= samples_to_remove:
                                samples_to_remove -= len(self.audio_buffer[0])
                                self.audio_buffer.pop(0)
                            else:
                                self.audio_buffer[0] = self.audio_buffer[0][samples_to_remove:]
                                samples_to_remove = 0
                        
                        # Cập nhật frames_accumulated sau khi xóa
                        frames_accumulated = sum(len(chunk) for chunk in self.audio_buffer)
                        
            time.sleep(0.1)  # Prevent CPU overuse
    
    def process_window(self, window_data):
        """
        Process a 3-second window of audio data.
        
        This method handles each sliding window of audio data.
        For example, with a 3-second window and 1-second slide:
          - First window: 0-3 seconds
          - Second window: 1-4 seconds
          - Third window: 2-5 seconds
          
        Args:
            window_data (numpy.ndarray): Audio data for the current window (3 seconds)
        """
        # Put the window in a queue for further processing
        self.chunk_queue.put(window_data)
        
        # Send to API using a separate thread to avoid blocking
        send_thread = threading.Thread(
            target=self.send_to_api, 
            args=(window_data, f"audio_chunk_{self.save_counter}")
        )
        send_thread.daemon = True
        send_thread.start()
        
        self.save_counter += 1
        
    def send_to_api(self, audio_data, chunk_id):
        """
        Send audio data to an external API.
        
        Args:
            audio_data (numpy.ndarray): Audio data to send (3 seconds)
            chunk_id (str): Identifier for this audio chunk
        """
        try:
            # Convert audio data to WAV format in memory
            buffer = BytesIO()
            wf = wave.open(buffer, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
            wf.close()
            
            # Get the WAV data from the buffer
            buffer.seek(0)
            wav_data = buffer.read()
            
            # Encode the WAV data as base64 for sending via JSON
            encoded_data = base64.b64encode(wav_data).decode('utf-8')
            
            # Prepare the payload
            payload = {
                'chunk_id': chunk_id,
                'timestamp': time.time(),
                'sample_rate': self.sample_rate,
                'channels': self.channels,
                'audio_data': encoded_data
            }
            
            # Send to the API
            response = requests.post(
                self.api_url, 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )

            print({response.status_code})
            
            # Update status with response info
            if response.status_code == 200:
                self.last_api_status = f"Success ({response.status_code})"
            else:
                self.last_api_status = f"Error ({response.status_code})"
                
            # Log the response (could be extended for more detailed handling)
            print(f"API Response for {chunk_id}: {response.status_code}")
            
        except Exception as e:
            self.last_api_status = f"Error: {str(e)}"
            print(f"Error sending audio to API: {e}")
    
    def save_to_wav(self, audio_data, filename):
        """
        Save audio data to a WAV file (kept for backward compatibility).
        
        Args:
            audio_data (numpy.ndarray): Audio data to save (3 seconds)
            filename (str): Name of the output file
        """
        directory = "recorded_chunks"
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        filepath = os.path.join(directory, filename)
        wf = wave.open(filepath, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.sample_rate)
        wf.writeframes(audio_data.tobytes())
        wf.close()
        
    def stop_recording(self):
        """
        Stop the audio recording and close the audio stream.
        """
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Wait for processing thread to finish if it exists
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)  # Wait up to 1 second
        
    def close(self):
        """
        Close all resources and terminate PyAudio.
        This should be called when the application exits.
        """
        self.stop_recording()
        self.audio.terminate()