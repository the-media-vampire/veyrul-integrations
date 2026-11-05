from array import array
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

from loop_check import measure


class LoopMeasurements(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'sample.wav'

    def tearDown(self):
        self.tmp.cleanup()

    def wav(self, frames, channels=1, width=2):
        values = array('h', frames)
        if sys.byteorder != 'little':
            values.byteswap()
        with wave.open(str(self.path), 'wb') as w:
            w.setparams((channels, width, 8000, 0, 'NONE', 'not compressed'))
            w.writeframes(values.tobytes())
        return self.path

    def test_silence_has_no_ratio_and_no_perceptual_verdict(self):
        r = measure(self.wav([0] * 32))
        self.assertEqual(r['per_channel'][0]['boundary_jump_fs'], 0)
        self.assertIsNone(r['per_channel'][0]['boundary_to_max_adjacent_ratio'])
        self.assertFalse(r['audibility_assessed'])
        self.assertFalse(r['loudness_lufs_measured'])

    def test_dc_offset_is_not_hidden_by_zero_boundary(self):
        c = measure(self.wav([16384] * 8))['per_channel'][0]
        self.assertEqual(c['dc_offset_fs'], .5)
        self.assertEqual(c['rms_fs'], .5)
        self.assertEqual(c['boundary_jump_fs'], 0)

    def test_periodic_wave_boundary_is_an_ordinary_step(self):
        c = measure(self.wav([0, 8192, 0, -8192] * 4))['per_channel'][0]
        self.assertEqual(c['boundary_jump_fs'], .25)
        self.assertEqual(c['boundary_to_max_adjacent_ratio'], 1)

    def test_ramp_exposes_large_boundary(self):
        c = measure(self.wav(list(range(0, 8001, 1000))))['per_channel'][0]
        self.assertEqual(c['boundary_to_max_adjacent_ratio'], 8)

    def test_channels_measured_independently_not_canceled(self):
        c = measure(self.wav([0, 0, 1000, -1000, 2000, -2000], channels=2))['per_channel']
        self.assertEqual(c[0]['boundary_jump_fs'], 2000 / 32768)
        self.assertEqual(c[1]['boundary_jump_fs'], 2000 / 32768)
        self.assertEqual(c[0]['dc_offset_fs'], -c[1]['dc_offset_fs'])

    def test_delta_across_streaming_chunks_is_included(self):
        c = measure(self.wav([0] * 8192 + [16384] * 8192))['per_channel'][0]
        self.assertEqual(c['max_adjacent_jump_fs'], .5)
        self.assertAlmostEqual(c['adjacent_jump_rms_fs'], .5 / (16383 ** .5))

    def test_signed_full_scale(self):
        c = measure(self.wav([-32768, 32767]))['per_channel'][0]
        self.assertEqual(c['peak_fs'], 1)
        self.assertEqual(c['boundary_jump_fs'], 65535 / 32768)

    def test_empty_or_single_frame_is_rejected(self):
        for frames in ([], [0]):
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                measure(self.wav(frames))

    def test_unsupported_sample_width_rejected(self):
        with self.assertRaisesRegex(ValueError, '16-bit'):
            measure(self.wav([0, 0], width=1))

    def test_truncated_audio_rejected(self):
        self.wav([0] * 64)
        self.path.write_bytes(self.path.read_bytes()[:-4])
        with self.assertRaisesRegex(ValueError, 'truncated'):
            measure(self.path)

    def test_malicious_declared_payload_rejected_before_read(self):
        self.wav([0] * 64)
        raw = bytearray(self.path.read_bytes())
        at = raw.index(b'data') + 4
        raw[at:at + 4] = struct.pack('<I', 0x7ffffffe)
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'declared audio'):
            measure(self.path)

    def test_file_size_bound(self):
        with self.assertRaisesRegex(ValueError, 'byte limit'):
            measure(self.wav([0] * 64), max_bytes=50)

    def test_input_unchanged_and_cli_json(self):
        self.wav([0, 100, 0, -100])
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        r = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('loop_check.py')), str(self.path)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)['frames'], 4)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)
        self.assertEqual(len(list(Path(self.tmp.name).iterdir())), 1)

    def test_invalid_cli_returns_error_without_traceback(self):
        self.path.write_bytes(b'not a WAV file')
        r = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('loop_check.py')), str(self.path)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn('error', json.loads(r.stderr))
        self.assertEqual(r.stdout, '')


if __name__ == '__main__':
    unittest.main()
