"""Behaviour checks for the citadel-skills scripts (stdlib only)."""
import json, os, re, subprocess, sys, tempfile, unittest
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills")
CONNECT = os.path.join(REPO, "citadel-connect/connect.py")
PUBLISH = os.path.join(REPO, "citadel-publish/publish.py")
CHECK = os.path.join(REPO, "citadel-new-app/check_package.py")

def run(*args, env=None, cwd=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, env=e, cwd=cwd)

class Connect(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.cfg = os.path.join(self.d, "cfg.json")
        for folder, specname, line in [("new", "spec.md", "- Short name: newapp"), ("old", "scheda.md", "- Nome breve: oldapp")]:
            os.makedirs(os.path.join(self.d, folder, "pkg"))
            json.dump({"version": "1.0.0"}, open(os.path.join(self.d, folder, "pkg", "pbapp.json"), "w"))
            open(os.path.join(self.d, folder, specname), "w").write(f"# X\n\n{line}\n")
    def test_apps_reads_spec_and_legacy_scheda(self):
        r = run(CONNECT, "apps", "--dir", self.d, env={"CITADEL_CONFIG": self.cfg})
        out = json.loads(r.stdout)
        self.assertEqual(set(out), {"newapp", "oldapp"})
        self.assertEqual(out["newapp"]["local_version"], "1.0.0")
        self.assertTrue(out["oldapp"]["folder"].endswith("old"))
    def test_check_reports_scope_in_english(self):
        r = run(CONNECT, "check", env={"CITADEL_CONFIG": self.cfg})
        out = json.loads(r.stdout)
        self.assertIn("scope", out)
        self.assertEqual(out["token"], "missing")
        self.assertIn("result", out)

class Publish(unittest.TestCase):
    def test_dry_run_in_english(self):
        r = run(PUBLISH, os.path.join(REPO, "citadel-new-app/template/pkg"), "--tenant", "x", "--dry-run")
        out = json.loads(r.stdout)
        self.assertEqual(set(out), {"files", "bytes", "version"})

class Check(unittest.TestCase):
    def test_template_ok(self):
        self.assertEqual(run(CHECK, os.path.join(REPO, "citadel-new-app/template/pkg")).stdout.strip(), "ok")
    def test_errors_in_english(self):
        d = tempfile.mkdtemp()
        open(os.path.join(d, "stray.txt"), "w").write("x")
        r = run(CHECK, d)
        self.assertEqual(r.returncode, 1)
        self.assertIn("pbapp.json: missing", r.stdout)
        self.assertIn("not allowed", r.stdout)

ITALIAN = re.compile(r"\b(della|degli|delle|perché|quando|anche|questo|questa|chiedi|scheda|utente|pacchetto|collegamenti)\b", re.I)
LEGACY_OK = re.compile(r"scheda\.md|Nome breve|Dati toccati|Per chi la costruisce|Modifiche|chiaro|scuro|grafici|raggio_px|Email o password non corretti")

class Language(unittest.TestCase):
    def skill_files(self):
        for root, _, files in os.walk(REPO):
            for n in files:
                if n.endswith((".md", ".py", ".js", ".mjs", ".html", ".json")):
                    yield os.path.join(root, n)

    def test_skills_are_written_in_english(self):
        for f in self.skill_files():
            for i, line in enumerate(open(f, encoding="utf-8"), 1):
                hit = ITALIAN.search(LEGACY_OK.sub("", line))
                self.assertIsNone(hit, f"{os.path.relpath(f, REPO)}:{i}: Italian word {hit and hit.group(0)!r}")

    def test_every_skill_states_the_language_rule(self):
        for name in os.listdir(REPO):
            text = open(os.path.join(REPO, name, "SKILL.md"), encoding="utf-8").read()
            self.assertIn("in the user's language", text, name)
            self.assertIn("`language` setting", text, name)

if __name__ == "__main__":
    unittest.main()
