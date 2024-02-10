import customtkinter as ctk
import pyaudio
import wave
import os


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
            print("Start Recording")
            self.is_recording = True
            self.stream = self.pyaudio.open(format=self.format, channels=self.channels, rate=self.sample_rate, input=True, frames_per_buffer=self.chunk)
            self.root.after(100, self.record)
            self.stop_button.place(relx=0.5, rely=0.7, anchor=ctk.CENTER)
            self.start_button.place_forget()

    def record(self):
        if self.is_recording:
            try:
               data = self.stream.read(self.chunk, exception_on_overflow=False)
               self.frames.append(data)
            except IOError as e:
                print(f"Input overflowed, ignoring this chunk. {e}")

            self.root.after(100, self.record)
        else: 
            self.stop_recording()

    def stop_recording(self):
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()
        # self.pyaudio.terminate()

        self.start_button.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)
        self.stop_button.place_forget()
       
        self.save_recording()
    
    def save_recording(self):
        print(f"Total frames: {len(self.frames)}, Total data size: {sum(len(frame) for frame in self.frames)} bytes")

        audio_dir = "src/audio"
        os.makedirs(audio_dir, exist_ok=True)
        file_path = os.path.join(audio_dir, "recording.wav")

        wave_file = wave.open(file_path, 'wb')
        wave_file.setnchannels(self.channels)
        wave_file.setsampwidth(self.pyaudio.get_sample_size(self.format))
        wave_file.setframerate(self.sample_rate)
        wave_file.writeframes(b''.join(self.frames))
        wave_file.close()
        self.frames=[]





        
       



