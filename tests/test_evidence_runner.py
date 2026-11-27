#!/usr/bin/env python3

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from analysis.evidence_runner import build_evidence_record, run_fixed_argv, verify_git_pin


class EvidenceRunnerTests(unittest.TestCase):
    def test_safe_argv_exit_nonzero(self):
        result = run_fixed_argv([sys.executable, "-c", "raise SystemExit(3)"])
        self.assertEqual(result["exit_code"], 3)

    def test_build_evidence_with_temp_git_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "t@test"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True, capture_output=True)
            (repo / "README").write_text("x\n", encoding="utf-8")
            subprocess.run(["git", "add", "README"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)
            pin = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            verify_git_pin(repo, pin)
            record = build_evidence_record(
                evidence_id="unit",
                source_repo="local/repo",
                source_pin=pin,
                oracle_kind="test",
                argv=[sys.executable, "-c", "print('ok')"],
                covered_examples=[{"example_id": "a" * 64, "code_sha256": "b" * 64}],
                cwd=repo,
            )
            self.assertEqual(record["exit_code"], 0)
            self.assertEqual(len(record["command_argv"]), 3)


if __name__ == "__main__":
    unittest.main()