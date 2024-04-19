import tensorflow as tf
import tensorflow_hub as hub
import os
import logging
import numpy as np
import math
import statistics
import music21
import librosa
from librosa import display as librosadisplay
import matplotlib.pyplot as plt
from scipy.io import wavfile
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

MAX_ABS_INT16 = 32768.0

class Pitch_Detect:
    def __init__(self, path):
        self.path = path 
        self.best_error = float("inf")
        self.best_notes_and_rests = None
        self.best_prediction_per_note = None
        if os.path.exists(path=path):
            self.analyze_audio()
            self.music_score()
        else:
            print('File does not exist f{path}')
            
    def plot_stft(self, x, sr):
        x_stft = np.abs(librosa.stft(x, n_fft=2048))
        fig, _ = plt.subplots()
        fig.set_size_inches(5,5)
        x_stft_db = librosa.amplitude_to_db(x_stft, ref=np.max)
        librosadisplay.specshow(data=x_stft_db, y_axis='log', sr=sr, cmap='gray_r')
        plt.colorbar(format='%+2.0f db')

    def load_model(self, y):
        model = hub.load(os.path.join("src/spice"))
        model_output = model.signatures["serving_default"](tf.constant(y, tf.float32))
        self.pitch_outputs = model_output["pitch"]
        self.uncertainty_outputs = model_output["uncertainty"]
        self.confidence_outputs = 1.0 - self.uncertainty_outputs

        logging.info(f"confidence output,{type(self.confidence_outputs)} {self.confidence_outputs}")
        logging.info(f"pitch outputs, {type(self.pitch_outputs)} {self.pitch_outputs}")

        # fig, ax = plt.subplots()
        # fig.set_size_inches(10,5)
        # plt.plot(pitch_outputs, label='pitch')
        # plt.plot(confidence_outputs, label='confidence')
        # plt.legend(loc="lower right")
        # plt.show()

    def analyze_audio(self):
       try: 
            y, sr = librosa.load(self.path, sr=16000)
            sample_rate, audio_samples = wavfile.read(self.path, 'rb')

            #  plt.figure(figsize=(10,4))
            #  plt.title('Audio waveform')
            #  plt.xlabel('time')
            #  plt.ylabel('frequency')
            #  plt.plot(y)
            #  plt.plot(audio_samples)

            #  self.plot_stft(audio_samples/ MAX_ABS_INT16, sr=sample_rate)
            #  self.plot_stft(y, sr=sr)
            #  plt.show()

            self.load_model(y)

            self.confidence_outputs = list(self.confidence_outputs)
            self.pitch_outputs = [ float(x) for x in self.pitch_outputs]
        
            indices = range(len(self.pitch_outputs))
            self.confidence_pitch_outputs = [ (i,p) for i,p,c in zip(indices, self.pitch_outputs, self.confidence_outputs) if c >= 0.9 ]
            self.confidence_pitch_outputs_x, self.confidence_pitch_outputs_y = zip(*self.confidence_pitch_outputs)

            self.confidence_pitch_values_hz = [output_to_hertz(p) for p in self.confidence_pitch_outputs_y]

            # _, ax = plt.subplots()
            # fig.set_size_inches(10,5)
            # ax.set_ylim([0,1])
            # self.plot_stft(y, sr=16000)
            # plt.scatter(self.confidence_pitch_outputs_x, self.confidence_pitch_values_hz, c='purple')
            # plt.show()


            self.pitch_outputs_rest = [ output_to_hertz(p) if c >= 0.9 else 0 
                              for i,p,c in zip(indices, self.pitch_outputs, self.confidence_outputs)]
            self.a4 = 440
            self.c0 = self.a4 * pow(2, -4.75)
            self.note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

            offsets = [self.freq_to_offset(p) for p in self.pitch_outputs_rest if p!=0]
            self.ideal_offset = statistics.mean(offsets)

            for predictions_per_note in range(20, 65, 1):
                for prediction_start_offset in range(predictions_per_note):
                    error, notes_and_rests = self.get_quantization_and_error(self.pitch_outputs_rest, predictions_per_note, prediction_start_offset, self.ideal_offset) 
                    if error < self.best_error :
                        self.best_error = error
                        self.best_notes_and_rests = notes_and_rests
                        self.best_prediction_per_note = predictions_per_note
        
            while best_notes_and_rests[0] == 'Rest':
                best_notes_and_rests = best_notes_and_rests[1:]
            while best_notes_and_rests[-1] == "Rest":
                best_notes_and_rests = best_notes_and_rests[:-1]

       except Exception as e :
            print(f'Error analyzing audio {e}')

    def music_score(self):
        sc = music21.stream.Score()
        bpm = 60 * 60 / self.best_prediction_per_note
        a = music21.tempo.MetronomeMark(number=bpm)
        sc.insert(0, a)

        for snote in self.best_notes_and_rests:
            d = 'half'
            if snote == 'Rest':
                sc.append(music21.note.Rest(type=d))
            else:
                sc.append(music21.note.Note(snote, type=d))

        audio_file = os.path.join('src/audio', "test.wav")
        midi_file = audio_file[:-4] +'.mid'
        fp = sc.write('midi', fp=midi_file)

    def freq_to_offset(self,freq):
        if freq <= 0: return None
        h = round(12 * math.log2(freq / self.c0)) # no of frequencies between freq and c0, semitone difference
        return 12 * math.log2(freq / self.c0) - h # returns the fractional offset, how far freq is from the whole semitone
    
    def quantize_predictions(self, group, ideal_offset):
        non_zero_values = [v for v in group if v!=0]
        zero_values_count = len(group) - len(non_zero_values)
        
        #check if 80% of the group is silent, otherwise make a note
        if zero_values_count > 0.8 * len(group): 
            return 0.51 * len(non_zero_values), "Rest"    
        else:
            h = round(statistics.mean([
                12 * math.log2(freq/self.c0) - ideal_offset for freq in non_zero_values 
            ]))
            octave = h // 12 # No of octaves between c0 and h
            n = h % 12
            note = self.note_names[n] + str(octave)
            error = sum([
                abs(12*math.log2(freq/self.c0) - ideal_offset - h) for freq in non_zero_values
            ])
            return error, note
        
    def get_quantization_and_error(self, pitch_outputs_rest, prediction_per_eigth,
                                    prediction_start_offset, ideal_offset):
        pitch_outputs_rest = [0] * prediction_start_offset + \
            pitch_outputs_rest
        groups = [
            pitch_outputs_rest[i:i + prediction_per_eigth]
            for i in range (0, len(pitch_outputs_rest), prediction_per_eigth)
        ]
        quantization_error = 0
        
        notes_and_rests = []
        for group in groups:
            error, note_or_rest = self.quantize_predictions(group, ideal_offset)
            quantization_error += error
            notes_and_rests.append(note_or_rest)
        
        return quantization_error, notes_and_rests
        

def output_to_hertz(pitch_output):
    PT_OFFSET = 25.58
    PT_SLOPE = 63.07
    FMIN = 10.0
    BINS_PER_OCTAVE = 12.0

    cqt_bin = pitch_output * PT_SLOPE + PT_OFFSET
    return FMIN * 2.0 ** (1.0 * cqt_bin / BINS_PER_OCTAVE)


if __name__ == "__main__":
    Pitch_Detect(os.path.join('src/audio', 'recording.wav'))

