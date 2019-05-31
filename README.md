# MIDI Synthesizer

## Dependencies
This project requires Python 3 to run. It has been tested with Python 3.5 and 3.7, 
but other minor versions may work as well.

This project depends on the [mido](https://mido.readthedocs.io/en/latest/)
Python package for reading and parsing MIDI files.
Additionally, if the [sa (Simple Audio)](https://pypi.org/project/simpleaudio/)
Python package is installed, it is used to play the synthesized audio to the
speakers. Otherwise, the program will still run, but the `--play` option is
disabled.

## Running
To run this project, use the following syntax:
```
python3 midi_player.py [-h] [-p] [-o filename] [--tremolo frequency amplitude]
                       [--envelope attack decay sustain release]
                       [--delay delay level] [-s {sine,fm}]
                       [--fmod frequency] [--amod amplitude]
                       <midi_file>
```

### Required arguments:
`<midi_file>`         Filename of the input midi file to synthesize

### Optional arguments:
`-h`, `--help`
Show a help message and exit

`-p`, `--play`
Play the audio to the speakers after synthesizing it

`-o <filename>.wav`, `--output <filename>.wav`
Save the synthesized audio to a wav file with the given filename

`--tremolo frequency amplitude`
Apply a tremolo effect with the given frequency and amplitude to the track

`--delay delay level`
Add a delay effect

`--envelope attack decay sustain release`
Apply a standard ADSR envelope to each note

`-s {sine,fm}, --synthesizer {sine,fm}`
What method to use when synthesizing a note

#### For fm method:
`--fmod frequency`
Frequency of modulating signal fm synthesizer

`--amod amplitude`
Amplitude of modulation of fm synthesizer

#### For sine method:
`--harmonics harmonics`
Number of odd harmonics to generate and add to signal 
