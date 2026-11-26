#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

from scripts import check_prereg as prereg


class PaperTrackGuardTests(unittest.TestCase):
    def test_kiln_mention_fails_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "docs" / "protocol" / "note.md"
            path.parent.mkdir(parents=True)
            path.write_text("Do not ship the kiln runtime here.\n", encoding="utf-8")
            problems = prereg.scan_paper_track_forbidden(
                repo_root=root,
                relative_dirs=("docs/protocol",),
            )
            self.assertTrue(problems)
            self.assertIn("kiln", problems[0])

    def test_jasper_mention_fails_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "experiments" / "paper-v1" / "x.md"
            path.parent.mkdir(parents=True)
            path.write_text("jasper must review\n", encoding="utf-8")
            problems = prereg.scan_paper_track_forbidden(
                repo_root=root,
                relative_dirs=("experiments/paper-v1",),
            )
            self.assertTrue(problems)

    def test_clean_file_passes_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "docs" / "paper" / "outline.md"
            path.parent.mkdir(parents=True)
            path.write_text("Ollama on halo-395 only.\n", encoding="utf-8")
            problems = prereg.scan_paper_track_forbidden(
                repo_root=root,
                relative_dirs=("docs/paper",),
            )
            self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()