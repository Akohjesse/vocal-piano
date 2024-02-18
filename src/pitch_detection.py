import librosa
import numpy as np
import logging

logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Pitch_Detect:
    def __init__(self, path):
        self.path = path
        self.analyze_audio(self.path)

    def getPitches(y, sr, hop_length=512, n_fft=2048):
        stft = np.abs(librosa.stft(y, n_fft, hop_length))
        frequencies = librosa.fft_frequencies(sr, n_fft)
        indices = np.argmax(stft, axis=0)
        pitches = frequencies[indices]
        return pitches

    def frequency_to_note(freq):
        a4 = 440
        c0 = a4 * pow(2, -4.75)
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        h = round(12 * np.log2(freq / c0))
        octave = h // 12
        n = h % 12
        return note_names[n] + str(octave)

    def analyze_audio(self, path):
        y, sr = librosa.load(path)
        pitches = self.getPitches(y, sr)
        notes = [self.frequency_to_note(pitch) for pitch in pitches]
        logging.info(notes)
        return notes