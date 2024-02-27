import customtkinter as ctk
import threading, pyaudio, wave, logging
import os
import pitch_detection

logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
class AudioRecorder:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("VocalPiano")
        self.root.geometry("400x200")

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.start_button = ctk.CTkButton(master=self.root, text="Start Recording", command=self.start_recording)
        self.start_button.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

        self.stop_button = ctk.CTkButton(master=self.root, text="Stop Recording", command=self.stop_recording)
        self.stop_button.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)
        self.stop_button.place_forget()

        self.pyaudio =  pyaudio.PyAudio()
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.sample_rate = 44100
        self.frames = []
        self.is_recording = False

        self.root.mainloop()

    def start_recording(self):
        if not self.is_recording:
            logging.info("Start Recording")
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self.record, daemon=True)
            self.recording_thread.start()
           
            self.stop_button.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)
            self.start_button.place_forget()

    def record(self):
        self.stream = self.pyaudio.open(format=self.format, channels=self.channels, rate=self.sample_rate, 
                                        input=True, frames_per_buffer=self.chunk)
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
            except IOError as e:
                logging.warning(f"Input overflowed, ignoring this chunk. {e}")
            
        self.stream.stop_stream()
        self.stream.close()

    def stop_recording(self):
        self.is_recording = False
        self.recording_thread.join()

        self.save_recording()
        self.frames=[]


        self.start_button.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)
        self.stop_button.place_forget()
        
        pitch_detection.Pitch_Detect("/Users/jesseakoh/Desktop/Code/Python/vocal-piano/src/audio/recording.wav")
    
    def save_recording(self):

        logging.info(f"Total frames: {len(self.frames)}, Total data size: {sum(len(frame) for frame in self.frames)} bytes")

        try:
            audio_dir = "src/audio"
            os.makedirs(audio_dir, exist_ok=True)
            file_path = os.path.join(audio_dir, "recording.wav")

            with wave.open(file_path, 'wb') as wave_file:
             wave_file.setnchannels(self.channels)
             wave_file.setsampwidth(self.pyaudio.get_sample_size(self.format))
             wave_file.setframerate(self.sample_rate)
             wave_file.writeframes(b''.join(self.frames))
             wave_file.close()
             logging.info("File Saved")

        except Exception as e:
            logging.error(f"Error saving recording{e}")