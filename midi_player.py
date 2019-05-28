import wave, mido, sys, math, struct, array, random, argparse
from dataclasses import dataclass

try:
	import mido
except ImportError:
	print("Unable to import mido! Please install mido and try again.", file=sys.stderr)
	sys.exit(0)

sa = None

try:
	import simpleaudio as sa
except ImportError:
	print("Unable to import simpleaudio! Audio output disabled.", file=sys.stderr)

SAMPLE_RATE = 44100

@dataclass
class Envelope:
	"""Class for specifying a synthesis envelope for a note."""
	attack: float = 0
	decay: float = 0
	sustain: float = .5
	release: float = 0

@dataclass
class Tremolo:
	frequency: float = 5
	amplitude: float = .25

@dataclass
class Delay:
	delay: float = 20
	level: float = .5

@dataclass
class Flanger:
	rate: float = 1
	depth: float = 1
	resonance: float = 1

# Generate conversion from MIDI note to frequency.
# Obtained from: http://www.inspiredacoustics.com/en/MIDI_note_numbers_and_center_frequencies
FREQS = {}
for n in range(128):
	FREQS[n] = 440 * 2**((n-69)/12)
	
"""Generates samples of a sine wave(s)."""
def sine(nsamples, frequency, num_harmonics=0):
	result = array.array('d', [0] * nsamples)

	for i in range(num_harmonics+1):
		for j in range(nsamples):
			w = 2.0 * math.pi * (frequency * (1 + 2*i)) * j
			s = math.sin(w / SAMPLE_RATE)
			result[j] += s / (1<<i)

	return result

"""Scales a list of floating point samples to signed 2-byte integers."""
def scale(samples):
	scale_factor = max(abs(max(samples)), abs(min(samples)))
	return [math.floor((sample/scale_factor) * (2**15-1)) for sample in samples]

class Message:
	def __init__(self, start_tick=0, msg=None):
		self.start_tick = start_tick
		self.msg = msg

	def __str__(self):
		return "Message(start_tick={}, msg={})".format(self.start_tick, self.msg)

	def __lt__(self, other):
		return self.start_tick < other.start_tick

def parse_midi(filename):
	score = []
	playing = []
	tempo = 500000

	midi_file = mido.MidiFile(filename)
	print("Number of tracks:", len(midi_file.tracks))

	# Combine all tracks into a single list
	combined = []
	for track in midi_file.tracks:
		total_ticks = 0
		for msg in track:
			total_ticks += msg.time
			combined.append(Message(total_ticks, msg))

	# Sort the commands to be in order
	combined.sort()

	total_seconds = 0.0
	total_ticks = 0
	for message in combined:
		msg = message.msg

		delta_ticks = message.start_tick - total_ticks
		total_ticks = message.start_tick
		total_seconds += mido.tick2second(delta_ticks, midi_file.ticks_per_beat, tempo)

		# print(msg)

		# Set tempo for song
		if msg.type == "set_tempo":
			tempo = msg.tempo
			score.append(Tempo(total_seconds, msg.tempo))
			print("Tempo set to {} at {:.2f} seconds ({} ticks)".format(tempo, total_seconds, total_ticks))

		# Start playing note
		elif msg.type == "note_on" and msg.velocity > 0:
			playing.append(Note(msg.note, total_seconds, velocity=msg.velocity))
		
		# End playing note
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			for j in range(len(playing)):
				if playing[j].note == msg.note:
					playing[j].duration = total_seconds - playing[j].start
					score.append(playing.pop(j))
					break

	if len(playing) > 0:
		print("Leftover notes:", len(playing))
	score.extend(playing)
	score.sort()
	print("Score length: ", len(score))

	return score, midi_file.length

class Tempo:
	def __init__(self, start, tempo):
		self.start = start
		self.tempo = tempo

	def __str__(self):
		return "Tempo(start={:.3f}, tempo={})".format(self.start, self.tempo)

	def __repr__(self):
		return str(self)
	
	# For sorting notes in score
	def __lt__(self, other):
		return self.start < other.start

class Note:
	def __init__(self, note, start=0, duration=0, velocity=100):
		self.note = note
		self.start = start
		self.duration = duration
		self.velocity = velocity

	def synthesize(self, opts):
		num_samples = math.floor(SAMPLE_RATE * (self.duration + opts.envelope.release))
		samples = sine(num_samples, FREQS[self.note], 1)

		num_attack_samples = math.floor(opts.envelope.attack * SAMPLE_RATE)
		num_decay_samples = math.floor(opts.envelope.decay * SAMPLE_RATE)
		num_release_samples = math.floor(opts.envelope.release * SAMPLE_RATE)

		# Apply envelope attack
		for i in range(min(num_attack_samples, num_samples)):
			samples[i] *= i / num_attack_samples

		# Apply envelope decay
		sustain_level = num_decay_samples * opts.envelope.sustain
		for i in range(1, min(num_decay_samples, num_samples - num_attack_samples)):
			samples[num_attack_samples + i] *= ((num_decay_samples - i) * (1 - opts.envelope.sustain) + sustain_level) / num_decay_samples

		# Apply envelope sustain
		for i in range(num_attack_samples + num_decay_samples, len(samples)):
			samples[i] *= opts.envelope.sustain

		# Apply envelope release
		for i in range(num_release_samples):
			samples[-i] *= i / num_release_samples

		if opts.tremolo:
			for i in range(len(samples)):
				s = math.sin((2.0 * math.pi * opts.tremolo.frequency * i) / SAMPLE_RATE)
				s = (s * opts.tremolo.amplitude) + 1
				samples[i] *= s

		return samples

	# For debugging and display
	def __str__(self):
		return "Note(note={}, start={:.3f}, duration={:.3f}, velocity={})".format(self.note, self.start, self.duration, self.velocity)

	# For debugging and display
	def __repr__(self):
		return str(self)

	# For sorting notes in score
	def __lt__(self, other):
		return self.start < other.start

	# For synth caching
	def __eq__(self, other):
		return (self.note, self.duration) == (other.note, other.duration)

	# For synth caching
	def __hash__(self):
		return hash((self.note, self.duration))

def main(opts):
	print("Parsing MIDI file...")
	score, length = parse_midi(sys.argv[1])

	# print("\n".join(str(note) for note in score))
	print("Song length: {:.3f} sec".format(length))
	tempo = 500000

	length += opts.envelope.release

	if opts.delay:
		length += opts.delay.delay * 5

	raw_samples = array.array('d', [0] * math.floor(length * SAMPLE_RATE))

	cache = {"miss": 0, "total": 0}
	for i, note in enumerate(score):
		print("\rSynthesizing note {} of {}...".format(i+1, len(score)), end="", flush=True)

		if isinstance(note, Tempo):
			tempo = note.tempo

		elif isinstance(note, Note):
			# Cache synths for reuse
			cache["total"] += 1
			if note not in cache:
				cache["miss"] += 1
				cache[note] = note.synthesize(opts)

			samples = cache[note]

			start = math.floor(note.start * SAMPLE_RATE)
			for j in range(len(samples)):
				raw_samples[start + j] += samples[j] * note.velocity

	print("\rApplying effects..." + " "*20, end="", flush=True)
	# Post synthesis effects
	if opts.delay:
		delay_length = math.floor(opts.delay.delay * SAMPLE_RATE)
		for i in range(len(raw_samples) - delay_length):
			raw_samples[i+delay_length] += raw_samples[i]*opts.delay.level

		# Attenuate end of track
		length = math.floor(opts.delay.delay * SAMPLE_RATE)
		for i in range(length):
			raw_samples[-i] *= i / length

	print("\rScaling output...  ", end="", flush=True)
	samples = scale(raw_samples)

	# Convert raw samples to 2-byte frames
	print("\rConverting output...", end="", flush=True)
	output_frames = bytearray(len(samples) * 2)
	for i, sample in enumerate(samples):
		output_frames[i*2:i*2+2] = struct.pack("<h", sample)

	# Open output file
	if opts.out_file:
		print("\rWriting wav file...", end="", flush=True)
		out = wave.open(opts.out_file)
		out.setnchannels(1)
		out.setsampwidth(2)
		out.setframerate(SAMPLE_RATE)

		# Write samples
		out.writeframes(output_frames)
		out.close()

	print("\rCache hit rate: {:2.1f}%".format((cache["total"] - cache["miss"])*100/cache["total"]))

	if sa and opts.play:
		print("\rPlaying audio file...")
		try:
			sa.play_buffer(output_frames, 1, 2, SAMPLE_RATE).wait_done()
		except KeyboardInterrupt:
			pass
	else:
		print("\a", end="")

	print("\rDone." + " " * 10)

class EffectAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, self.const(*values))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Synthesizes a midi file")
	parser.add_argument("midi", help="Filename of midi file to synthesize")
	parser.add_argument("-p", "--play", help="Play the audio after synthesizing it", action="store_true")
	parser.add_argument("-o", "--output", type=argparse.FileType('wb'), dest="out_file", metavar="filename", help="Save the synthesized audio to a wav file with the given filename")
	parser.add_argument("--tremolo", nargs=2, type=float, action=EffectAction, const=Tremolo, help="Add tremolo effect", metavar=("frequency", "amplitude"))
	parser.add_argument("--delay", nargs=2, type=float, action=EffectAction, const=Delay, help="Add a delay effect", metavar=("delay", "level"))
	parser.add_argument("--envelope", nargs=4, type=float, action=EffectAction, const=Envelope, help="ADSR envelope to apply to each note", metavar=("attack", "decay", "sustain", "release"), default=Envelope(attack=.02, decay=.02, sustain=.70, release=.2))
	main(parser.parse_args())
