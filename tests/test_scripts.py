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

    def test_set_token_outside_a_terminal_points_to_one(self):
        # From a chat tool the input is not a terminal: the token would be echoed, so refuse.
        r = subprocess.run([sys.executable, CONNECT, "set-token", "--global"], input="secret\n",
                           capture_output=True, text=True, env=dict(os.environ, CITADEL_CONFIG=self.cfg))
        self.assertEqual(r.returncode, 2)
        self.assertIn("PowerShell", r.stderr)
        self.assertFalse(os.path.exists(self.cfg) and "secret" in open(self.cfg).read())

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

def package(manifest):
    d = tempfile.mkdtemp()
    base = {"schemaVersion": 1, "name": "x", "version": "1.0.0", "pocketbase": {"min": "0.38.0", "max": "0.42.x"}}
    base.update(manifest)
    json.dump(base, open(os.path.join(d, "pbapp.json"), "w"))
    return d

class CheckServerRules(unittest.TestCase):
    """check_package.py must refuse what Citadel's pkgvalidate refuses."""
    def errors(self, manifest, env=None):
        r = run(CHECK, package(manifest), env=dict({"CITADEL_CONFIG": os.devnull}, **(env or {})))
        return r.returncode, r.stdout, r.stderr
    def assertRefused(self, manifest, text, env=None):
        code, out, _ = self.errors(manifest, env)
        self.assertEqual(code, 1, out)
        self.assertIn(text, out)
    def test_good_manifest(self):
        code, out, err = self.errors({"egress": ["api.example.com", "*.example.co.uk"]})
        self.assertEqual((code, out.strip(), err), (0, "ok", ""))
    def test_options_is_not_a_smoke_method(self):
        self.assertRefused({"smoke": [{"method": "OPTIONS", "path": "/"}]}, "invalid method")
    def test_dotdot_in_path(self):
        self.assertRefused({"smoke": [{"path": "/a/../b"}]}, "..")
    def test_uppercase_host(self):
        self.assertRefused({"egress": ["API.Example.com"]}, "lowercase")
    def test_wildcard_public_suffix(self):
        self.assertRefused({"egress": ["*.co.uk"]}, "public suffix")
        self.assertRefused({"egress": ["*.github.io"]}, "public suffix")
    def test_reserved_tld(self):
        self.assertRefused({"egress": ["erp.corp"]}, "reserved")
    def test_ip_shorthand(self):
        self.assertRefused({"egress": ["10.1"]}, "IP address")
    def test_url_not_host(self):
        self.assertRefused({"egress": ["https://api.example.com"]}, "not a URL")
    def test_apps_domain(self):
        self.assertRefused({"egress": ["other.apps.company.com"]}, "apps domain",
                           env={"CITADEL_APPS_DOMAIN": "https://apps.company.com"})
    def test_range(self):
        self.assertRefused({"pocketbase": {"min": "0.41.0", "max": "0.40.x"}}, "above max")
        self.assertRefused({"pocketbase": {"min": "0.19.0", "max": "0.19.x"}}, "none of the platform")
        code, _, err = self.errors({"pocketbase": {"min": "0.38.0", "max": "0.41.x"}})
        self.assertEqual(code, 0)
        self.assertIn("0.42.2", err)
    def test_open_bounds(self):
        code, out, _ = self.errors({"pocketbase": {"min": "", "max": "0.*"}})
        self.assertEqual((code, out.strip()), (0, "ok"))

class Download(unittest.TestCase):
    """connect.py download against a stub of the Citadel API."""
    def serve(self, entries, status=200):
        import http.server, io, threading, zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for name, data in entries.items():
                z.writestr(name, data)
        zipped = buf.getvalue()
        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_GET(self):
                if self.headers.get("Authorization") != "Bearer t":
                    self.send_response(401); self.end_headers(); return
                if self.path == "/api/v1/tenants/app/releases":
                    body = json.dumps({"current": "r2", "releases": [
                        {"id": "r2", "manifest": json.dumps({"version": "1.2.0"})}, {"id": "r1", "manifest": "{}"}]}).encode()
                    self.send_response(200); self.end_headers(); self.wfile.write(body)
                elif self.path == "/api/v1/tenants/app/releases/r2/download":
                    self.send_response(status); self.end_headers()
                    self.wfile.write(zipped if status == 200 else b'{"error":"x"}')
                else:
                    self.send_response(404); self.end_headers(); self.wfile.write(b'{"error":"tenant not found"}')
        srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.shutdown)
        cfg = os.path.join(tempfile.mkdtemp(), "cfg.json")
        json.dump({"url": f"http://127.0.0.1:{srv.server_port}", "token": "t"}, open(cfg, "w"))
        return {"CITADEL_CONFIG": cfg}
    def test_unpacks_current_release(self):
        env = self.serve({"pbapp.json": '{"version":"1.2.0"}', "pb_public/index.html": "<p>hi</p>"})
        d = os.path.join(tempfile.mkdtemp(), "app")
        r = run(CONNECT, "download", "app", "--dir", d, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual((out["release"], out["version"], out["current"]), ("r2", "1.2.0", True))
        self.assertTrue(os.path.isfile(os.path.join(d, "pkg", "pb_public", "index.html")))
        r = run(CONNECT, "download", "app", "--dir", d, env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already exists", r.stderr)
    def test_refuses_traversal(self):
        env = self.serve({"../evil.js": "x"})
        d = os.path.join(tempfile.mkdtemp(), "app")
        r = run(CONNECT, "download", "app", "--dir", d, env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unsafe path", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(d, "pkg")))
    def test_unknown_app_and_forbidden(self):
        env = self.serve({})
        r = run(CONNECT, "download", "other", "--dir", os.path.join(tempfile.mkdtemp(), "a"), env=env)
        self.assertIn("no access", r.stderr)
        env = self.serve({}, status=403)
        r = run(CONNECT, "download", "app", "--dir", os.path.join(tempfile.mkdtemp(), "a"), env=env)
        self.assertIn("deployer", r.stderr)

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

class Structure(unittest.TestCase):
    """Every skill is well formed, linked for local use and listed in the README."""
    ROOT = os.path.join(REPO, "..")

    def test_frontmatter_names_match_folders(self):
        for name in os.listdir(REPO):
            text = open(os.path.join(REPO, name, "SKILL.md"), encoding="utf-8").read()
            m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
            self.assertIsNotNone(m, f"{name}: frontmatter must be name + description")
            self.assertEqual(m.group(1), name)
            self.assertIn("Use it when", m.group(2), f"{name}: description must say when to use it")

    def test_linked_and_listed(self):
        readme = open(os.path.join(self.ROOT, "README.md"), encoding="utf-8").read()
        for name in os.listdir(REPO):
            self.assertIn(f"| `{name}` |", readme, f"{name}: missing from the README skills table")
            link = os.path.join(self.ROOT, ".claude", "skills", name)
            self.assertTrue(os.path.isfile(os.path.join(link, "SKILL.md")), f"{name}: .claude/skills link missing")

    def test_wizard_offers_install(self):
        text = open(os.path.join(REPO, "citadel", "SKILL.md"), encoding="utf-8").read()
        ask = text.index("Do you already have a Citadel in your company?")
        self.assertLess(ask, text.index("Step 4 of 7"))
        self.assertIn("`citadel-install`", text[ask:])

if __name__ == "__main__":
    unittest.main()
