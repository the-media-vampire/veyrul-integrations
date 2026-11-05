"""Original generated-signal regression checks. Requires an installed FFmpeg."""
import json
import math
import os
from pathlib import Path
import struct
import tempfile
import unittest
import wave
from normalize import normalize, measured_values


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'original.wav'
        with wave.open(str(self.source), 'wb') as output:
            output.setnchannels(2); output.setsampwidth(2); output.setframerate(22050)
            frames = bytearray()
            for i in range(22050 * 8):
                t = i / 22050
                envelope = .3 + .15 * math.sin(2 * math.pi * .7 * t)
                left = int(5000 * envelope * (math.sin(2*math.pi*220*t) + .4*math.sin(2*math.pi*370*t)))
                right = int(4000 * envelope * math.sin(2*math.pi*330*t))
                frames.extend(struct.pack('<hh', left, right))
            output.writeframes(frames)

    def tearDown(self):
        # Only disposable fixtures created by this test are removed.
        self.temp.cleanup()

    def run_normalize(self, **kwargs):
        return normalize(self.source, self.root/'out.wav', receipt=self.root/'receipt.json',
                         ffmpeg=os.environ.get('FFMPEG', 'ffmpeg'), **kwargs)

    def test_changed_stereo_target_and_encoded_format(self):
        report = self.run_normalize(integrated=-18, true_peak=-2, channels=2, sample_rate=44100)
        self.assertTrue(report['accepted_numerically'])
        with wave.open(str(self.root/'out.wav'), 'rb') as output:
            self.assertEqual((output.getnchannels(), output.getsampwidth(), output.getframerate(), output.getnframes()),
                             (2, 2, 44100, 352800))
        self.assertEqual(json.loads((self.root/'receipt.json').read_text()), report)

    def test_silence_has_no_finite_integrated_loudness(self):
        with wave.open(str(self.source), 'wb') as output:
            output.setnchannels(1); output.setsampwidth(2); output.setframerate(16000)
            output.writeframes(bytes(16000 * 2 * 4))
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            self.run_normalize()
        self.assertFalse((self.root/'out.wav').exists())

    def test_no_existing_output_overwrite(self):
        output=self.root/'out.wav'; output.write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'no overwrite'): self.run_normalize()
        self.assertEqual(output.read_bytes(), b'keep')

    def test_no_source_or_receipt_alias(self):
        with self.assertRaises(ValueError):
            normalize(self.source, self.root/'out.wav', receipt=self.source)

    def test_bad_targets_rejected_before_ffmpeg(self):
        for kwargs in ({'integrated':float('nan')},{'true_peak':1},{'lra':0},{'channels':6},{'stream':-1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): self.run_normalize(**kwargs)

    def test_missing_and_nonfinite_measurements_rejected(self):
        for text in ('no measurement', '{}', '{"input_i":"-inf"}'):
            with self.subTest(text=text), self.assertRaises(ValueError): measured_values(text)


if __name__ == '__main__':
    unittest.main()
