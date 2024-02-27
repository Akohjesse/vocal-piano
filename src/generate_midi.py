import mido
from mido import Message, MidiFile, MidiTrack

def note_to_midi_number(note):
   note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
   octave = int(note[-1])
   name = note[:-1]
   return note_names.index(name) + 12 * (octave + 1)

def create_midi_from_notes(notes, output_file):
   midi_file = MidiFile()
   track = MidiTrack()
   midi_file.tracks.append(track)

   track.append(Message('program_change', program=12))

   for note, duration in notes:
      if note != "Silence":
         note_number = note_to_midi_number(note)
         track.append(Message('note_on', note=note_number, velocity=64, time=0))

         tick_duration = int(mido.second2tick(duration, midi_file.ticks_per_beat, 500000))
         track.append(Message('note_off', note=note_number, velocity=64, time=tick_duration))

   midi_file.save(output_file)