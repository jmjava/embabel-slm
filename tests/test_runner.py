#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

from runner.extract import extract_fenced_files
from runner.reachability import check_reachability
from runner.runs import refuse_existing


class ExtractTests(unittest.TestCase):
    def test_paths_on_fence_label(self):
        text = """```java src/main/java/demo/X.java
package demo;
public class X {}
```"""
        files = extract_fenced_files(text)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].path.endswith("X.java"))


class RunDirTests(unittest.TestCase):
    def test_refuse_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run"
            path.mkdir()
            with self.assertRaises(FileExistsError):
                refuse_existing(path)


class ReachabilityTests(unittest.TestCase):
    def test_kb01_pattern_fails(self):
        java = """
        import com.embabel.agent.api.annotation.*;
        @Agent(description="x") class A {
          @Action Customer collect(String id) { return new Customer(id); }
          @AchievesGoal @Action LoanDecision decide(CreditAssessment c) { return null; }
        }
        """
        result = check_reachability(java, initial_types=["String"])
        self.assertFalse(result.reachable)
        self.assertIn("CreditAssessment", ",".join(result.missing))


class GenerateMetaTests(unittest.TestCase):
    def test_default_sample_seeds(self):
        samples = 5
        seeds = list(range(1, samples + 1))
        self.assertEqual(seeds, [1, 2, 3, 4, 5])

    def test_generate_writes_protocol_meta_fields(self):
        import json
        from unittest.mock import patch

        from runner.generate import generate_run

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "raw").mkdir()
            with patch("runner.generate._chat_once", return_value=("```java x\n```", 0.01)):
                with patch("runner.generate.model_digest", return_value="deadbeef"):
                    with patch("runner.generate.ollama_version", return_value="0.0.0"):
                        with patch("runner.generate.peak_memory_gb_for_model", return_value=8.0):
                            generate_run(
                                run_dir,
                                model="qwen2.5-coder:7b",
                                host_class="halo-395",
                                backend="vulkan",
                                quant="Q4_K_M",
                                task_ids=["E01"],
                                arm="S",
                                config="D",
                                split="holdout",
                                samples=2,
                                sample_seeds=[1, 2],
                            )
            meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["arm"], "S")
            self.assertEqual(meta["config"], "D")
            self.assertEqual(meta["split"], "holdout")
            self.assertEqual(meta["inference_backend"], "ollama")
            self.assertEqual(meta["decoding"]["sample_count"], 2)
            self.assertTrue((run_dir / "raw" / "E01.sample1.md").is_file())


if __name__ == "__main__":
    unittest.main()