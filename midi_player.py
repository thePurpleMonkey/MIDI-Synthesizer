import wave, mido, sys, math, struct, array

input_file = sys.argv[1]

SAMPLE_RATE = 44100

FREQS = {
	32: 51.91,
	34: 58.27,
	36: 65.41,
	37: 69.30,
	39: 77.78,
	40: 82.41,
	41: 87.31,
	42: 92.50,
	43: 98.00,
	44: 103.83,
	45: 110.00,
	46: 116.54,
	47: 123.47, 
	48: 130.81,
	49: 138.59,
	50: 146.83,
	51: 155.56,
	52: 164.81,
	53: 174.61,
	54: 185.00, 
	55: 196.00,
	56: 207.65,
	57: 220.00,
	58: 233.08,
	59: 246.94, 
	60: 261.63,
	61: 277.18,
	62: 293.66,
	63: 311.13,
	64: 329.63,
	65: 349.23,
	66: 369.99,
	67: 392.00,
	68: 415.30,
	69: 440.00,
	70: 466.16, 
	71: 493.88,
	72: 523.25,
	73: 554.37,
	74: 587.33,
	75: 622.25,
	76: 659.26,
	77: 698.46,
	78: 739.99,
	79: 783.99,
	80: 830.61,
	81: 880.00,
	82: 932.33,
	83: 987.77,
	84: 1046.50,
	85: 1108.73,
	91: 1567.98
}

def sine(nsamples, frequency):
	result = array.array('d')
	for i in range(nsamples):
		w = 2.0 * math.pi * frequency * i
		s = math.sin(w / SAMPLE_RATE)
		result.append(s)
	return result

def sine_harmonics(nsamples, frequency, num_harmonics=0):
	result = array.array('d', [0] * nsamples)
	# for i in range(nsamples):
	# 	w = 2.0 * math.pi * frequency * i
	# 	s = math.sin(w / SAMPLE_RATE)
	# 	result.append(s)

	for i in range(num_harmonics+1):
		for j in range(nsamples):
			w = 2.0 * math.pi * (frequency * (1 + 2*i)) * j
			s = math.sin(w / SAMPLE_RATE)
			result[j] += s / (1<<i)

	return result

def scale(samples):
	old_max = max(samples)
	old_min = min(samples)
	new_max = 2**15-1
	new_min = -2**15
	
	old_range = (old_max - old_min)  
	new_range = (new_max - new_min) 

	scaled_samples = array.array("h") 
	
	for sample in samples:
		scaled_samples.append(round((((sample - old_min) * new_range) / old_range) + new_min))

	return scaled_samples

class Note:
	def __init__(self, note, start=0, duration=0, velocity=100):
		self.note = note
		self.start = start
		self.duration = duration
		self.velocity = velocity

	def synthesize(self, func, *args, **kwargs):
		return func(self.duration, FREQS[self.note], *args, **kwargs)

	def __str__(self):
		return "Note(note={}, start={}, duration={}, velocity={})".format(self.note, self.start, self.duration, self.velocity)

	def __lt__(self, other):
		return self.start < other.start

	def __eq__(self, other):
		return self.start == other.start

	def __repr__(self):
		return str(self)

score = []
playing = []
total_time = 0
tempo = 0
total_samples = 0

mid = mido.MidiFile(input_file)

for i, track in enumerate(mid.tracks):
	for msg in track:
		if not msg.is_meta:
			total_time += msg.time

		# print(msg)

		if msg.type == "set_tempo":
			tempo = msg.tempo
			print("Tempo set.")
		elif msg.type == "note_on" and msg.velocity > 0:
			start_sample = math.floor(SAMPLE_RATE * mido.tick2second(total_time, mid.ticks_per_beat, tempo))
			playing.append(Note(msg.note, start_sample, velocity=msg.velocity))
		
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			for j in range(len(playing)):
				if playing[j].note == msg.note:
					playing[j].duration = math.floor(SAMPLE_RATE * mido.tick2second(total_time, mid.ticks_per_beat, tempo)) - playing[j].start
					total_samples = max(total_samples, playing[j].start + playing[j].duration)
					score.append(playing.pop(j))
					break

print("Leftover notes:", len(playing))
score.extend(playing)
score.sort()
print("Score length: ", len(score))
# print("\n".join(str(note) for note in score[:10]))

if tempo == 0:
	print("No tempo message found! Unable to synthesize.")
	exit(1)

raw_samples = array.array('d', [0] * total_samples)
count_did = 0
count_skipped = 0
count_total = 0
for i, note in enumerate(score):
	count_total += 1
	print("\rSynthesizing note {} of {}...".format(i, len(score)), end="", flush=True)

	# if note.note < 60 and False:
	# 	print("Skipping {}".format(note))
	# 	count_skipped += 1
	# 	continue

	# samples = note.synthesize(sine)
	samples = note.synthesize(sine_harmonics, num_harmonics=4)

	count_did += 1

	for j in range(note.duration):
		raw_samples[note.start + j] += samples[j] * note.velocity

# print("Total notes: ", count_total)
# print("Skipped notes:", count_skipped)
# print("Synthesized notes:", count_did)
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

print("Done." + " " * 10)
