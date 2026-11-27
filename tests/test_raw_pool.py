#!/usr/bin/env python3

import unittest

from analysis.practices import load_prereg
from analysis.raw_pool import (
    DRIVINE_QUERY_REPOS,
    _steps_from_yaml,
    classify_drivine_corpus,
    classify_drivine_path,
    classify_embabel_path,
    cleanse_text,
    extract_cypher_steps,
    kept_source_kind,
    size_report,
    split_withheld,
    validate_unit,
)

SPEC = """
cases:
  - name: "Returning nodes and properties"
    steps:
      - cypher: "MATCH (p:Person {name: $name}) RETURN properties(p)"
        parameters: {name: "Keanu"}
        rows: [{name: "Keanu", born: 1964}]
      - cypher: |
          MATCH (p:Person)
          RETURN p.name
        rows: ["Keanu"]
      - cypher: "RETURN 9223372036854775808"
        error: true
  - name: "Co-actors"
    steps:
      - note: "The same relationship is not read twice."
        cypher: "MATCH (a)-[:ACTED_IN]->(m) RETURN a"
        rows: ["Keanu"]
"""


class CleanseTests(unittest.TestCase):
    def test_secret_text_is_dropped(self):
        self.assertIsNone(cleanse_text("-----BEGIN PRIVATE KEY-----\nabc"))

    def test_blank_text_is_dropped(self):
        self.assertIsNone(cleanse_text(" \n\t"))

    def test_newlines_are_normalized(self):
        self.assertEqual(cleanse_text("MATCH (n)\r\nRETURN n\r"), "MATCH (n)\nRETURN n")


class SourceScopeTests(unittest.TestCase):
    def test_embabel_keeps_the_org_and_splits_literature(self):
        self.assertEqual(classify_embabel_path("embabel/guide", "docs/actions.md"), "documentation")
        self.assertEqual(classify_embabel_path("embabel/embabel-agent", "src/Action.java"), "code")
        self.assertEqual(classify_embabel_path("embabel/blogs", "posts/intro.md"), "literature")
        self.assertIsNone(classify_embabel_path("jmjava/embabel-v1-learning", "notes.md"))
        self.assertIsNone(classify_embabel_path("embabel/guide", "assets/logo.png"))
        self.assertEqual(classify_embabel_path("embabel/guide", "examples/load.cypher"), "code")
        self.assertIsNone(kept_source_kind("documentation"))
        self.assertIsNone(kept_source_kind("literature"))
        self.assertEqual(kept_source_kind("code"), "code")

    def test_drivine_keeps_the_query_language_only(self):
        spec = "liberation-data/drivine-cypher-spec"
        self.assertEqual(classify_drivine_path(spec, "queries.yaml"), "spec_yaml")
        self.assertEqual(
            classify_drivine_path(spec, "compiler/src/commonMain/antlr/Cypher.g4"),
            "grammar",
        )
        self.assertIsNone(classify_drivine_path(spec, "compiler/native/sqlite/sqlite3.h"))
        self.assertEqual(
            classify_drivine_path(
                "liberation-data/drivine-inspiration",
                "src/movies/moviesForActor.cypher",
            ),
            "cypher_file",
        )
        self.assertEqual(
            classify_drivine_path(
                "liberation-data/drivine",
                "docs/04-cypher-on-a-relational-database.md",
            ),
            "query_doc",
        )
        self.assertIsNone(classify_drivine_path("srrai786786-wq/drivine", "queries.yaml"))
        self.assertIsNone(classify_drivine_path("jmjava/drivine-slm", "data/drivine_instruct.json"))
        self.assertNotIn("jmjava/drivine-slm", DRIVINE_QUERY_REPOS)
        self.assertEqual(
            classify_drivine_corpus("liberation-data/drivine4j", "src/main/Query.kt"),
            "code",
        )
        self.assertIsNone(kept_source_kind("query_doc"))
        self.assertIsNone(kept_source_kind("documentation"))


class SpecExtractTests(unittest.TestCase):
    def test_steps_keep_statements_and_oracles(self):
        steps = extract_cypher_steps(SPEC)
        self.assertEqual(len(steps), 4)
        self.assertEqual(steps[0]["cypher"], "MATCH (p:Person {name: $name}) RETURN properties(p)")
        self.assertTrue(steps[0]["oracle"])
        self.assertEqual(steps[1]["cypher"], "MATCH (p:Person)\nRETURN p.name")
        self.assertTrue(steps[1]["oracle"])
        self.assertTrue(steps[2]["oracle"])
        self.assertEqual(steps[0]["case_name"], "Returning nodes and properties")
        self.assertEqual(steps[3]["cypher"], "MATCH (a)-[:ACTED_IN]->(m) RETURN a")
        self.assertEqual(steps[3]["case_name"], "Co-actors")

    def test_cypher_outside_steps_is_kept(self):
        text = """
cells:
  - name: "Hole"
    anchor: "where"
    cypher: "MATCH (p:Person) WHERE {hole} RETURN p.name"
"""
        steps = _steps_from_yaml(text)
        if steps is None:
            self.skipTest("PyYAML is not installed")
        self.assertEqual(len(steps), 1)
        self.assertIn("WHERE {hole}", str(steps[0]["cypher"]))
        self.assertFalse(steps[0]["oracle"])


class ValidationTests(unittest.TestCase):
    def test_area_labels_are_refused(self):
        reasons = validate_unit(
            {
                "domain": "drivine",
                "source_kind": "query",
                "source_repo": "liberation-data/drivine-cypher-spec",
                "source_file": "queries.yaml",
                "source_pin": "abc",
                "executable_oracle": True,
                "area": "query",
            }
        )
        self.assertIn("area_assigned_too_early", reasons)

    def test_name_collisions_are_not_the_query_language(self):
        reasons = validate_unit(
            {
                "domain": "drivine",
                "source_kind": "query",
                "source_repo": "per10621umt232243/A-data-drivine-exploration-of-Apples-iPhone-impact-in-india",
                "source_file": "notes.md",
                "source_pin": "abc",
                "executable_oracle": True,
            }
        )
        self.assertIn("not_query_language", reasons)

    def test_cypher_without_a_result_stays_out_of_the_dose(self):
        row = {"reasons": ["missing_query_oracle"], "cypher": "MATCH (n) RETURN n"}
        withheld, rejected = split_withheld([row, {"reasons": ["secret"]}])
        self.assertEqual(withheld, [row])
        self.assertEqual(len(rejected), 1)

    def test_a_spec_step_without_a_result_is_refused(self):
        reasons = validate_unit(
            {
                "domain": "drivine",
                "source_kind": "query",
                "source_repo": "liberation-data/drivine-cypher-spec",
                "source_file": "queries.yaml",
                "source_pin": "abc",
                "executable_oracle": False,
            }
        )
        self.assertEqual(reasons, ["missing_query_oracle"])

    def test_accepted_query_and_embabel_file(self):
        self.assertEqual(
            validate_unit(
                {
                    "domain": "drivine",
                    "source_kind": "query",
                    "source_repo": "liberation-data/drivine-cypher-spec",
                    "source_file": "queries.yaml",
                    "source_pin": "abc",
                    "executable_oracle": True,
                }
            ),
            [],
        )
        self.assertEqual(
            validate_unit(
                {
                    "domain": "embabel",
                    "source_kind": "code",
                    "source_repo": "embabel/embabel-agent",
                    "source_file": "src/Action.java",
                    "source_pin": "abc",
                }
            ),
            [],
        )


class SizeFloorTests(unittest.TestCase):
    def setUp(self):
        self.prereg = load_prereg()

    def test_shortfall_uses_the_preregistered_floor(self):
        report = size_report({"embabel": 20, "drivine": 100}, self.prereg)
        self.assertEqual(report["holdout_min_tasks"], 742)
        self.assertEqual(report["holdout_scope"], "combined")
        self.assertEqual(report["prefixes"], [500, 1000, 2000, 4000, 8000, 16000])
        self.assertEqual(report["labeled_units_needed_for_plan"], 16000)
        self.assertEqual(report["collected_units"], 120)
        self.assertEqual(report["shortfall"], 15880)
        self.assertFalse(report["covers_plan"])
        self.assertTrue(report["code_only"])
        self.assertFalse(report["labeling_allowed"])
        self.assertFalse(report["categories_determined"])

    def test_a_large_pool_covers_the_combined_plan(self):
        report = size_report({"embabel": 2000, "drivine": 16000}, self.prereg)
        self.assertTrue(report["covers_plan"])
        self.assertEqual(report["shortfall"], 0)
        self.assertFalse(report["labeling_allowed"])


if __name__ == "__main__":
    unittest.main()
