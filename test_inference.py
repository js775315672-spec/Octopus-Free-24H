import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from inference_runner import digest, verify, infer
class InferenceTests(unittest.TestCase):
    def test_digest(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"file"
            p.write_bytes(b"test")
            verify(p,digest(p))
            with self.assertRaises(ValueError):
                verify(p,"0"*64)
    def test_reject_before_execution(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"file"
            p.write_bytes(b"test")
            with patch("inference_runner.subprocess.run") as run:
                with self.assertRaises(ValueError):
                    infer(p,p,digest(p),"0"*64,"test")
                run.assert_not_called()
