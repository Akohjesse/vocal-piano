import librosa
import numpy as np
import os
import logging
from generate_midi import create_midi_from_notes
import matplotlib.pyplot as plt

logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Pitch_Detect:
    def __init__(self, path):
        self.path = path
        if os.path.exists(path):
            self.analyze_audio()
        else:
          logging.error(f"File does not exist {path}")

    @staticmethod
    def getPitches(y, sr, hop_length=1024, n_fft=2048):
        stft = np.abs(librosa.stft(y=y, n_fft=n_fft, hop_length=hop_length))
        frequencies = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
        indices = np.argmax(stft, axis=0)
        pitches = frequencies[indices]
        logging.info(f"pitches {pitches}")
        return pitches

    @staticmethod
    def frequency_to_note(freq):
        if freq <= 0: return "Silence"
        a4 = 440 
        c0 = a4 * pow(2, -4.75)
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        h = round(12 * np.log2(freq / c0))
        octave = h // 12
        n = h % 12
        return note_names[n] + str(octave)

    def analyze_audio(self):
        try:
          y, sr = librosa.load(self.path)
          plt.plot(y)
          pitches = self.getPitches(y, sr)
          frame_dur = 1024 / sr
          raw_notes = [self.frequency_to_note(pitch) for pitch in pitches if pitch > 0]
          notes = []
          prev_note = None
          note_duration = 0

          for note in raw_notes:
              if note == prev_note:
                  note_duration +=1
              else: 
                  if prev_note is not None and note_duration * frame_dur >= 0.1:
                      notes.append((prev_note, note_duration * frame_dur))
                  prev_note = note
                  note_duration = 1
          if prev_note is not None and note_duration * frame_dur >= 0.1:
              notes.append((prev_note, note_duration * frame_dur))
         
          logging.info(f"Notes: ${notes}")
          print(f"\n Notes: ${notes}")
          midi_output = os.path.join("src/audio", "output.mid")
        #   create_midi_from_notes(notes=notes, output_file=midi_output)
        except Exception as e:
            logging.error(f"Error processing audio {e}")
            
if __name__ == "__main__":
    Pitch_Detect(os.path.join('src/audio', 'test.wav'))