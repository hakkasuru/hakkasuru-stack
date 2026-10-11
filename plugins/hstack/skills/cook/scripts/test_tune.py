# plugins/hstack/skills/cook/scripts/test_tune.py
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("tune.py")
SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def run(args, home, stdin=None):
    env = dict(os.environ, HSTACK_HOME=str(home))
    out = subprocess.run([sys.executable, str(SCRIPT)] + args, input=stdin, capture_output=True, text=True, env=env)
    return out.returncode, json.loads(out.stdout) if out.stdout.strip() else None, out.stderr


def run_record(home, **overrides):
    rec = {"repo": "github.com/o/r", "date": "2026-10-11", "outcome": "green", "gauge_tier": 1, "final_tier": 1,
           "escalations": [], "units_planned": 3, "units_used": 3, "attempts": [1, 1, 2], "stuck_units": 0,
           "review_rounds": 0, "fix_rounds": 0, "gauge_ops": 8, "tier_override": None}
    rec.update(overrides)
    return run(["record"], home, json.dumps(rec))


class TuneTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "hstack"

    def tearDown(self):
        self.tmp.cleanup()

    def test_caps_without_repo(self):
        rc, out, _ = run(["caps"], self.home)
        self.assertEqual(rc, 0)
        self.assertEqual(out["caps"]["units"], {"0": 1, "1": 3, "2": 8, "3": 20})
        self.assertEqual(out["caps"]["attempts"], 3)
        self.assertEqual(out["caps"]["gauge_backstop"], 25)
        self.assertEqual(out["sources"]["units.2"], "default")
        self.assertEqual(out["warnings"], [])

    def test_caps_override_and_repo_precedence(self):
        self.home.mkdir(parents=True)
        (self.home / "cook.json").write_text(json.dumps({
            "version": 1,
            "caps": {"units": {"2": 10}, "gauge_backstop": 30},
            "repos": {"gitlab.com/g/p": {"caps": {"gauge_backstop": 40}}},
            "history": []}))
        rc, out, _ = run(["caps", "--repo", "gitlab.com/g/p"], self.home)
        self.assertEqual(out["caps"]["units"]["2"], 10)
        self.assertEqual(out["sources"]["units.2"], "override")
        self.assertEqual(out["caps"]["gauge_backstop"], 40)
        self.assertEqual(out["sources"]["gauge_backstop"], "repo")
        self.assertEqual(out["caps"]["units"]["1"], 3)

    def test_caps_ignores_invalid_values(self):
        self.home.mkdir(parents=True)
        (self.home / "cook.json").write_text(json.dumps({"caps": {"units": {"2": "ten", "1": 4}, "bogus": 1}}))
        rc, out, _ = run(["caps"], self.home)
        self.assertEqual(rc, 0)
        self.assertEqual(out["caps"]["units"]["2"], 8)
        self.assertEqual(out["caps"]["units"]["1"], 4)
        self.assertTrue(any("units.2" in w for w in out["warnings"]))
        self.assertTrue(any("bogus" in w for w in out["warnings"]))

    def test_caps_broken_file_falls_back(self):
        self.home.mkdir(parents=True)
        (self.home / "cook.json").write_text("{not json")
        rc, out, _ = run(["caps"], self.home)
        self.assertEqual(rc, 0)
        self.assertEqual(out["caps"]["units"]["0"], 1)
        self.assertTrue(out["warnings"])

    def test_caps_tolerates_wrong_shapes(self):
        self.home.mkdir(parents=True)
        shapes = [
            ({"repos": "x"}, "repos"),
            ({"repos": {"gitlab.com/g/p": "x"}}, "repos.gitlab.com/g/p"),
            ({"repos": {"gitlab.com/g/p": {"caps": 5}}}, "repos.gitlab.com/g/p"),
            ({"caps": "str"}, "caps"),
            ({"caps": [1]}, "caps"),
            ({"caps": {"units": 7}}, "units"),
        ]
        for shape, path in shapes:
            (self.home / "cook.json").write_text(json.dumps(shape))
            rc, out, err = run(["caps", "--repo", "gitlab.com/g/p"], self.home)
            self.assertEqual(rc, 0, f"{shape}: {err}")
            self.assertEqual(out["caps"]["units"]["0"], 1)
            self.assertTrue(any(path in w for w in out["warnings"]), f"{shape}: {out['warnings']}")

    def test_apply_refuses_wrong_shapes(self):
        self.home.mkdir(parents=True)
        (self.home / "cook.json").write_text(json.dumps({"history": {}}))
        rc, out, err = run(["apply", "--change", "units.2=10", "--evidence", "x"], self.home)
        self.assertNotEqual(rc, 0)
        self.assertIn("history", out["error"])
        self.assertEqual(json.loads((self.home / "cook.json").read_text()), {"history": {}})

    def test_record_rejects_each_bad_field(self):
        bad = [
            {"tier_override": True},
            {"attempts": ["x"]},
            {"escalations": ["junk"]},
            {"date": "20261011"},
            {"gauge_tier": 4},
            {"units_used": True},
        ]
        for override in bad:
            rc, out, _ = run_record(self.home, **override)
            self.assertNotEqual(rc, 0, f"accepted {override}")
            self.assertIn("error", out or {}, f"no error message for {override}")
        rec = {"repo": "r", "date": "2026-10-11", "outcome": "green", "gauge_tier": 1, "final_tier": 1, "escalations": [],
               "units_planned": 1, "units_used": 1, "attempts": [1], "stuck_units": 0, "review_rounds": 0, "fix_rounds": 0, "gauge_ops": 1}
        rc, out, _ = run(["record"], self.home, json.dumps(rec))
        self.assertNotEqual(rc, 0, "accepted a run with no tier_override key")
        self.assertIn("tier_override", (out or {}).get("error", ""))
        self.assertFalse((self.home / "cook-runs.jsonl").exists())

    def test_record_creates_ledger_and_rejects_bad_runs(self):
        rc, out, _ = run_record(self.home)
        self.assertEqual(rc, 0)
        self.assertEqual(len((self.home / "cook-runs.jsonl").read_text().splitlines()), 1)
        rc, out, _ = run_record(self.home, outcome="maybe")
        self.assertNotEqual(rc, 0)
        self.assertEqual(len((self.home / "cook-runs.jsonl").read_text().splitlines()), 1)

    def test_suggest_needs_enough_runs(self):
        for _ in range(4):
            run_record(self.home, final_tier=2, units_used=10)
        rc, out, _ = run(["suggest"], self.home)
        self.assertEqual(out["runs"], 4)
        self.assertEqual(out["suggestions"], [])

    def test_suggest_unit_cap_at_p80(self):
        for used in [6, 9, 10, 10, 11]:
            run_record(self.home, gauge_tier=2, final_tier=2, units_used=used)
        rc, out, _ = run(["suggest"], self.home)
        caps = {s["cap"]: s for s in out["suggestions"]}
        self.assertEqual(caps["units.2"]["suggested"], 10)
        self.assertEqual(caps["units.2"]["current"], 8)

    def test_suggest_skips_bad_lines(self):
        for _ in range(5):
            run_record(self.home, final_tier=1, units_used=3)
        with open(self.home / "cook-runs.jsonl", "a") as f:
            f.write("{truncated\n")
        rc, out, _ = run(["suggest"], self.home)
        self.assertEqual(rc, 0)
        self.assertEqual(out["skipped_lines"], 1)
        self.assertEqual(out["runs"], 5)

    def test_suggest_escalation_note(self):
        for i in range(5):
            run_record(self.home, gauge_tier=1, final_tier=2 if i < 2 else 1)
        rc, out, _ = run(["suggest"], self.home)
        self.assertTrue(any("tier 1" in n and "escalat" in n for n in out["notes"]))

    def test_apply_writes_override_with_history(self):
        rc, out, _ = run(["apply", "--change", "units.2=10", "--evidence", "p80 10 across 14 runs"], self.home)
        self.assertEqual(rc, 0)
        data = json.loads((self.home / "cook.json").read_text())
        self.assertEqual(data["caps"]["units"]["2"], 10)
        self.assertEqual(data["history"][-1]["change"], "units.2: 8 -> 10")
        rc, out, _ = run(["apply", "--change", "gauge_backstop=40", "--repo", "gitlab.com/g/p", "--evidence", "monorepo"], self.home)
        data = json.loads((self.home / "cook.json").read_text())
        self.assertEqual(data["repos"]["gitlab.com/g/p"]["caps"]["gauge_backstop"], 40)

    def test_apply_rejects_unknown_cap(self):
        rc, out, _ = run(["apply", "--change", "nonsense=3", "--evidence", "x"], self.home)
        self.assertNotEqual(rc, 0)
        self.assertIn("unknown cap", (out or {}).get("error", ""))
        self.assertFalse((self.home / "cook.json").exists())

    def test_skill_table_matches_defaults(self):
        if not SKILL.exists():
            self.skipTest("SKILL.md not written yet (Task 9)")
        text = SKILL.read_text()
        rc, out, _ = run(["caps"], self.home)
        for tier, cap in out["caps"]["units"].items():
            self.assertRegex(text, rf"\|\s*{tier} [A-Z][a-z]+ \|.*\|\s*{cap}\s*\|")


if __name__ == "__main__":
    unittest.main()
