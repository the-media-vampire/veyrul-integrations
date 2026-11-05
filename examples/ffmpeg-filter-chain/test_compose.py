import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("compose_filters", Path(__file__).with_name("compose_filters.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CompositionChecks(unittest.TestCase):
    def test_crop_resize_caption_order_and_distinct_output(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "input with spaces;$(noop).mov"
            source.write_text("original")
            argv = module.compose(source, Path(d) / "new output.mp4", 1920, 1080, 1080, 1080, 720, 720)
            self.assertEqual(argv.count("-vf"), 1)
            self.assertEqual(argv[argv.index("-vf") + 1],
                             "crop=1080:1080:(iw-ow)/2:(ih-oh)/2,scale=720:720,subtitles=filename=captions.ass")
            self.assertEqual(argv[argv.index("-i") + 1], str(source.resolve()))
            self.assertIn("-n", argv)
            self.assertEqual(source.read_text(), "original")
            self.assertFalse(Path(argv[-1]).exists())

    def test_changed_dimensions_and_subtitle_name(self):
        with tempfile.TemporaryDirectory() as d:
            argv = module.compose(Path(d)/"in.mov", Path(d)/"out.mp4", 3840, 2160, 2160, 2160, 1080, 1080, "revision-2.ass")
            self.assertIn("crop=2160:2160:(iw-ow)/2:(ih-oh)/2,scale=1080:1080,subtitles=filename=revision-2.ass", argv)

    def test_refuses_overwrite_impossible_crop_and_filter_injection(self):
        with tempfile.TemporaryDirectory() as d:
            source, output = Path(d)/"in.mp4", Path(d)/"out.mp4"
            for subtitle in ["a,b.ass", "../captions.ass", "C:\\temp\\captions.ass", "a'b.ass", "x:force_style=evil.ass"]:
                with self.assertRaises(ValueError):
                    module.compose(source, output, 1920, 1080, 1080, 1080, 720, 720, subtitle)
            with self.assertRaises(ValueError):
                module.compose(source, source, 1920, 1080, 1080, 1080, 720, 720)
            with self.assertRaises(ValueError):
                module.compose(source, output, 1920, 1080, 2160, 2160, 720, 720)
            output.write_text("keep")
            with self.assertRaises(ValueError):
                module.compose(source, output, 1920, 1080, 1080, 1080, 720, 720)
            self.assertEqual(output.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
