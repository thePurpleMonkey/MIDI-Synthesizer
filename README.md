# MIDI Synthesizer

## Dependencies
This project requires Python 3.7 to run.

This project depends on the [mido](https://mido.readthedocs.io/en/latest/)
Python package for reading and parsing MIDI files.
Additionally, if the [simpleaudio](https://pypi.org/project/simpleaudio/)
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
                       [--harmonics harmonics]
                       <midi_file>
```

### Required arguments:
`<midi_file>`
Filename of the midi file to synthesize.

### Optional arguments:
`-h`, `--help`
Show a help message and exit.

`-p`, `--play`
Play the audio to the speakers after synthesizing it.
Requires the `simpleaudio` package.

`-o <filename>.wav`, `--output <filename>.wav`
Save the synthesized audio to a wav file with the given filename.

`--tremolo frequency amplitude`
Apply a tremolo effect with the given frequency and amplitude to the track.
Frequency is in hertz, and amplitude is percentage volume [0, 1]. 

`--delay delay level`
Add a delay effect.
Delay is in seconds, and level is percentage volume [0, 1). 

`--envelope attack decay sustain release`
Apply a standard ADSR envelope to each note
Attack, decay, and release are in seconds. Sustain is a percentage volume [0, 1].
Default is .02 attack, .02 decay, .7 sustain, and .2 release.

`-s {sine,fm}, --synthesizer {sine,fm}`
What method to use when synthesizing a note. Possible options are `sine` to
which uses pure sine waves, and `fm` which uses frequency modulation.
Default is `sine`.

#### For fm method:
`--fmod frequency`
Frequency of modulating signal fm synthesizer.
Frequency is in hertz.

`--amod amplitude`
Amplitude of modulation of fm synthesizer.
Amplitude is in hertz. 

#### For sine method:
`--harmonics harmonics`
Number of odd harmonics to generate and add to the signal.
Harmonics is an integer. The more harmonics, the longer it takes to synthesize.
