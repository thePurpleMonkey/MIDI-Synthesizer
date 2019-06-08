import unittest, midi_player

class TestMidiSynthesizer(unittest.TestCase):
	def test_freqs(self):
		self.assertEqual(midi_player.FREQS[69], 440)

	def test_scale(self):
		max_short = 2**15-1
		l = [-1, 0, 1]
		self.assertEqual(midi_player.scale(l), [-max_short, 0, max_short])

		l = [0, 1, 2]
		self.assertEqual(midi_player.scale(l), [0, max_short // 2, max_short])

		l = [-4, -2, 0, 2]
		self.assertEqual(midi_player.scale(l), [-max_short, -max_short // 2, 0, max_short // 2])

	def test_message(self):
		pass


if __name__ == '__main__':
	unittest.main()