#!/usr/bin/env python3

import unittest

from analysis.label_areas import balance_sheet, code_sections, cypher_literals, label_text
from analysis.practices import load_prereg


class SectionTests(unittest.TestCase):
    def test_a_class_becomes_one_section_per_function(self):
        text = """
class Other {
    fun noise(): String {
        return "noise-value"
    }
}

@EmbabelComponent
class Hello {
    @Action
    fun greet(name: String): String {
        return name
    }

    @Goal
    fun finish(): Boolean {
        return true
    }
}
"""
        sections = code_sections("Hello.kt", text)
        frames = {name: frame for name, _, _, frame in sections}
        self.assertEqual([name for name, _, _, _ in sections], ["noise", "greet", "finish"])
        self.assertEqual({grain for _, _, grain, _ in sections}, {"method"})
        greet = next(section for name, section, _, _ in sections if name == "greet")
        finish = next(section for name, section, _, _ in sections if name == "finish")
        self.assertIn("@Action", greet)
        self.assertIn("@Goal", finish)
        self.assertEqual(label_text("embabel", "Hello.kt#greet", greet)["area"], "generation")
        self.assertEqual(label_text("embabel", "Hello.kt#finish", finish)["area"], "planning")
        self.assertIn("class Hello", frames["greet"])
        self.assertNotIn("class Other", frames["greet"])
        self.assertNotIn("fun greet", frames["greet"])
        self.assertIn("class Other", frames["noise"])


class EmbabelLabelTests(unittest.TestCase):
    def test_one_repair_signal_is_repair(self):
        decision = label_text("embabel", "src/UnreachableTest.kt", "the action is unreachable")
        self.assertEqual(decision["area"], "repair")
        self.assertFalse(decision["admitted_example"])

    def test_two_signals_go_to_review(self):
        decision = label_text(
            "embabel",
            "src/Fix.kt",
            "@Goal unreachable and @RestController",
        )
        self.assertEqual(decision["reason"], "two_matches")
        self.assertCountEqual(decision["matches"], ["repair", "planning", "integration"])

    def test_action_with_no_other_signal_is_generation(self):
        decision = label_text("embabel", "src/Hello.kt", "@Action fun greet() {}")
        self.assertEqual(decision["area"], "generation")

    def test_no_signal_goes_to_review(self):
        decision = label_text("embabel", "src/Util.kt", "fun add(a: Int, b: Int) = a + b")
        self.assertEqual(decision["reason"], "zero_matches")
        self.assertEqual(decision["matches"], [])


class DrivineLabelTests(unittest.TestCase):
    def test_refusal_file_is_repair(self):
        decision = label_text("drivine", "refusals.yaml", "MATCH (n) RETURN n")
        self.assertEqual(decision["area"], "repair")

    def test_create_index_is_integration(self):
        decision = label_text("drivine", "schema.yaml", "CREATE INDEX FOR (n:Person) ON (n.name)")
        self.assertEqual(decision["area"], "integration")

    def test_merge_is_generation(self):
        decision = label_text("drivine", "writes.yaml", "MERGE (n:Person {name: $name})")
        self.assertEqual(decision["area"], "generation")

    def test_read_is_query_when_nothing_else_matches(self):
        decision = label_text("drivine", "queries.yaml", "MATCH (p:Person) RETURN p.name")
        self.assertEqual(decision["area"], "query")

    def test_double_quoted_client_cypher_is_extracted(self):
        text = 'pm.query(cypher_statement("MATCH (r:Racer) RETURN count(r)"))'
        self.assertEqual(cypher_literals(text), ["MATCH (r:Racer) RETURN count(r)"])

    def test_vector_write_goes_to_review(self):
        decision = label_text(
            "drivine",
            "vector.yaml",
            "CREATE (n:Chunk) RETURN n.loadNearest",
        )
        self.assertEqual(decision["reason"], "two_matches")
        self.assertCountEqual(decision["matches"], ["graph_rag", "generation"])


class BalanceTests(unittest.TestCase):
    def test_combined_plan_is_the_floor(self):
        prereg = load_prereg()
        labeled = [{"domain": "embabel", "area": "repair"}]
        sheet = balance_sheet(labeled, [{"reason": "zero_matches"}], prereg)
        repair = sheet["areas"]["embabel/repair"]
        self.assertEqual(repair["labeled"], 1)
        self.assertEqual(sheet["holdout_min_tasks"], 742)
        self.assertEqual(sheet["holdout_scope"], "combined")
        self.assertEqual(sheet["prefixes"], [500, 1000, 2000, 4000, 8000, 16000])
        self.assertEqual(sheet["needed_for_plan"], 16742)
        self.assertTrue(sheet["short_of_plan"])
        self.assertEqual(sheet["review"]["zero_matches"], 1)
        self.assertFalse(sheet["admitted_examples"])
        self.assertTrue(sheet["prefixes_locked"])
        self.assertEqual(len(sheet["areas"]), 11)


if __name__ == "__main__":
    unittest.main()
