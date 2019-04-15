import wave, mido, sys, math, struct, array

SAMPLE_RATE = 44100

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
	# Calculate scaling factors
	old_max = max(samples)
	old_min = min(samples)
	new_max = 2**15-1
	new_min = -2**15

	old_range = (old_max - old_min)  
	new_range = (new_max - new_min) 

	scaled_samples = array.array("h") 
	
	# Scale each sample
	for sample in samples:
		scaled_samples.append(round((((sample - old_min) * new_range) / old_range) + new_min))

	return scaled_samples

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
	# print("\n".join(str(n) for n in combined))

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

	print("Leftover notes:", len(playing))
	score.extend(playing)
	score.sort()
	print("Score length: ", len(score))

	return score

class SynthesizationError(Exception):
	pass

class Tempo:
	def __init__(self, start, tempo):
		self.start = start
		self.tempo = tempo
		self.duration = 0 # To be compatible with the Note object

	def synthesize(self, *args, **kwargs):
		return None

	def __str__(self):
		return "Tempo(start={:.3f}, tempo={})".format(self.start, self.tempo)

	def __repr__(self):
		return str(self)
	
	# For sorting notes in score
	def __lt__(self, other):
		return self.start < other.start


class Note:
	cache = dict()

	def __init__(self, note, start=0, duration=0, velocity=100):
		self.note = note
		self.start = start
		self.duration = duration
		self.velocity = velocity

	def synthesize(self, func, *args, **kwargs):
		if self not in Note.cache:
			try:
				Note.cache[self] = func(self.duration, FREQS[self.note], *args, **kwargs)
			except KeyError:
				raise SynthesizationError("Unable to convert MIDI note {} to frequency!".format(self.note))

		return Note.cache[self]

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

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("USAGE: python3 {} <midi input file> <wav output file>".format(sys.argv[0]), file=sys.stderr)
		exit(1)

	print("Parsing MIDI file...")
	score = parse_midi(sys.argv[1])
	mid = mido.MidiFile(sys.argv[1])
	# mid.print_tracks()

	# print("\n".join(str(note) for note in score))
	print("Song length: {:.3f} sec".format(mid.length))
	tempo = 500000

	raw_samples = array.array('d', [0] * math.floor(mid.length * SAMPLE_RATE))

	for i, note in enumerate(score):
		print("\rSynthesizing note {} of {}...".format(i, len(score)), end="", flush=True)

		if isinstance(note, Tempo):
			tempo = note.tempo

		elif isinstance(note, Note):
			start = math.floor(note.start * SAMPLE_RATE)
			samples = sine(math.floor(SAMPLE_RATE * note.duration), FREQS[note.note], 4)

			for j in range(len(samples)):
				raw_samples[start + j] += samples[j] * note.velocity

	print("\rScaling output..." + " "*20, end="", flush=True)
	samples = scale(raw_samples)

	print("\rWriting wav file...", end="", flush=True)
	# Convert raw samples to 2-byte frames
	output_frames = bytearray(len(samples) * 2)
	for i, sample in enumerate(samples):
		output_frames[i*2:i*2+2] = struct.pack("<h", sample)

	# Open output file
	out = wave.open(sys.argv[2], "wb")
	out.setnchannels(1)
	out.setsampwidth(2)
	out.setframerate(SAMPLE_RATE)

	# Write samples
	out.writeframes(output_frames)
	out.close()

	print("Done." + " " * 10)