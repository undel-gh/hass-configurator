"""Regression for Docker layer diffs when archive member paths are reused."""
import contextlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from scripts.diagnose_docker_layers import main


def image_tar(path, payload):
    layer_buffer = io.BytesIO()
    with tarfile.open(fileobj=layer_buffer, mode="w") as layer:
        member = tarfile.TarInfo("opt/example.txt")
        member.size = len(payload)
        member.mtime = 315532800
        layer.addfile(member, io.BytesIO(payload))
    layer_bytes = layer_buffer.getvalue()
    with tarfile.open(path, mode="w") as image:
        manifest = json.dumps([{"Layers": ["same-layer.tar"]}]).encode("utf8")
        for name, body in (("manifest.json", manifest),
                           ("same-layer.tar", layer_bytes)):
            info = tarfile.TarInfo(name)
            info.size = len(body)
            image.addfile(info, io.BytesIO(body))


class DockerLayerDiagnosticsTests(unittest.TestCase):
    def test_identical_layer_paths_do_not_hide_changed_file_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / "a.tar", Path(temp) / "b.tar"
            image_tar(a, b"reviewed first build")
            image_tar(b, b"unexpected next build")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(a, b)
            report = output.getvalue()
            self.assertIn("Layer 0:", report)
            self.assertIn("1 changed contents", report)
            self.assertIn("same_bytes=False", report)

    def test_identical_layer_payload_does_not_claim_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / "a.tar", Path(temp) / "b.tar"
            image_tar(a, b"unchanged")
            image_tar(b, b"unchanged")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(a, b)
            self.assertNotIn("changed paths", output.getvalue())


if __name__ == "__main__":
    unittest.main()
