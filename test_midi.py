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
		messages = [midi_player.Message(9), midi_player.Message(2), midi_player.Message(5)]
		messages.sort()
		self.assertEqual(messages[0].start_tick, 2)
		self.assertEqual(messages[1].start_tick, 5)
		self.assertEqual(messages[2].start_tick, 9)


if __name__ == '__main__':
	unittest.main()