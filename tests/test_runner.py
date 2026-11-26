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


if __name__ == "__main__":
    unittest.main()