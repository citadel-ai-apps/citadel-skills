#!/usr/bin/env python3
"""Local configuration for talking to Citadel.

    python3 connect.py init --url <portal> --apps-domain <domain> [--global]
    python3 connect.py set-token [--global]  # run it in the terminal: the token is typed hidden
    python3 connect.py add-app <short name> [--global]
    python3 connect.py check [--tenant <short name>]
    python3 connect.py apps [--dir <working folder>]
    python3 connect.py download <short name> --dir <app folder> [--release <id>]

Where the configuration lives (file with mode 600, the token is never printed):
- CITADEL_CONFIG, when set, wins over everything.
- Read: the nearest .citadel/config.json, from the current folder up to the root of
  the git repo; if there is none, ~/.config/citadel/config.json.
- Write: init creates .citadel/config.json at the repo root (or in the current
  folder, outside git) and adds .citadel/ to .gitignore. set-token and add-app
  write to the project file and stop if it is missing. With --global they use
  ~/.config/citadel/config.json.

download fetches the package of the release online (or --release) and unpacks it
into <app folder>/pkg. The spec and the tests are not part of a package.
"""
import argparse
import getpass
import io
import json
import os
import posixpath
import sys
import urllib.error
import urllib.request
import zipfile

GLOBAL = os.path.expanduser("~/.config/citadel/config.json")
LOCAL = os.path.join(".citadel", "config.json")
SPEC_FILES = ("spec.md", "scheda.md")  # scheda.md: apps made by the earlier, Italian skills
SHORT_NAME = ("- short name:", "- nome breve:")
# Citadel answers 404 both for an app that does not exist and for one this token has no role on.
NOT_FOUND = "does not exist, or you have no access to it: ask the operator"
FORBIDDEN = "your role on this app cannot publish or download: ask the operator for the deployer role"


def repo_root(start):
    """The root of the git repo containing start, or None."""
    d = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


def project_config(start="."):
    """The nearest .citadel/config.json, going up from start to the repo root."""
    d = os.path.abspath(start)
    stop = repo_root(d) or d
    while True:
        p = os.path.join(d, LOCAL)
        if os.path.isfile(p):
            return p
        if d == stop:
            return None
        d = os.path.dirname(d)


def config_path(write=False, use_global=False, create=False):
    """The file to use and its scope: variable, global or project."""
    env = os.environ.get("CITADEL_CONFIG")
    if env:
        return env, "CITADEL_CONFIG variable"
    if use_global:
        return GLOBAL, "global"
    found = project_config()
    if found:
        return found, "project"
    if create:
        return os.path.join(repo_root(".") or os.path.abspath("."), LOCAL), "project"
    if write:
        sys.exit("this project has no Citadel configuration yet: run "
                 "`connect.py init` here first, or add --global to use the global one")
    return GLOBAL, "global"


def ignore_in_git(path):
    """Adds .citadel/ to the .gitignore at the repo root, if the file is inside a repo."""
    root = repo_root(os.path.dirname(path))
    if not root:
        return
    gi = os.path.join(root, ".gitignore")
    text = open(gi, encoding="utf-8").read() if os.path.isfile(gi) else ""
    if any(l.strip().rstrip("/") in (".citadel", "/.citadel") for l in text.splitlines()):
        return
    with open(gi, "a", encoding="utf-8") as f:
        if text and not text.endswith("\n"):
            f.write("\n")
        f.write(".citadel/\n")


def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return {}


def save(path, c):
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)
    os.chmod(path, 0o600)


def get(c, path, token=True):
    req = urllib.request.Request(c["url"].rstrip("/") + path)
    if token:
        req.add_header("Authorization", "Bearer " + c.get("token", ""))
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read()
            try:
                return r.status, json.loads(raw or b"null")
            except ValueError:
                return r.status, None  # the login page is HTML
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except ValueError:
            return e.code, None
    except (urllib.error.URLError, OSError) as e:
        return 0, str(getattr(e, "reason", e))


def fetch(c, path):
    """GET returning (status, raw bytes); 0 and the reason if Citadel does not answer."""
    req = urllib.request.Request(c["url"].rstrip("/") + path)
    req.add_header("Authorization", "Bearer " + c.get("token", ""))
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except (urllib.error.URLError, OSError) as e:
        return 0, str(getattr(e, "reason", e)).encode()


def explain(st, body):
    """Plain words for a failed call; body is raw bytes, parsed JSON or a reason."""
    if st == 404:
        return NOT_FOUND
    if st == 403:
        return FORBIDDEN
    if st == 401:
        return "token not valid or expired: ask the operator for a new one"
    if isinstance(body, bytes):
        try:
            body = json.loads(body)
        except ValueError:
            body = body.decode("utf-8", "replace")[:300]
    if st == 0:
        return f"Citadel unreachable: {body}"
    msg = body.get("error") if isinstance(body, dict) else body
    return f"error {st}: {msg or ''}".strip()


def unpack(data, dest):
    """Unpacks a package zip into dest, refusing what the upload would refuse."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            name = info.filename
            clean = posixpath.normpath(name)
            if "\\" in name or name.startswith("/") or clean == ".." or clean.startswith("../"):
                sys.exit(f"the package contains an unsafe path: {name!r}")
        os.makedirs(dest)
        for info in z.infolist():
            if info.is_dir():
                continue
            target = os.path.join(dest, *posixpath.normpath(info.filename).split("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(info) as src, open(target, "wb") as out:
                out.write(src.read())


def download(c, slug, folder, release=None):
    dest = os.path.join(folder, "pkg")
    if os.path.exists(dest):
        sys.exit(f"{dest} already exists: download into a new folder")
    st, body = get(c, f"/api/v1/tenants/{slug}/releases")
    if st != 200:
        sys.exit(explain(st, body))
    rid = release or body.get("current")
    if not rid:
        sys.exit("no version published for this app yet")
    rel = next((r for r in body.get("releases") or [] if r.get("id") == rid), None)
    if rel is None:
        sys.exit(f"release {rid} not found for {slug}")
    st, data = fetch(c, f"/api/v1/tenants/{slug}/releases/{rid}/download")
    if st != 200:
        sys.exit(explain(st, data))
    unpack(data, dest)
    try:
        version = json.loads(rel.get("manifest") or "{}").get("version")
    except ValueError:
        version = None
    return {"folder": os.path.abspath(folder), "pkg": os.path.abspath(dest), "release": rid,
            "version": version, "current": rid == body.get("current")}


def local_apps(root):
    """App folders under root: they contain pkg/pbapp.json. The short name comes from the spec.

    spec.md is the current name; scheda.md (with "- Nome breve:") is read for apps
    created by earlier, Italian versions of the skills.
    """
    out = {}
    for d in sorted(os.listdir(root)):
        m = os.path.join(root, d, "pkg", "pbapp.json")
        if not os.path.isfile(m):
            continue
        slug = d
        for name in SPEC_FILES:
            spec = os.path.join(root, d, name)
            if not os.path.isfile(spec):
                continue
            for line in open(spec, encoding="utf-8"):
                if line.strip().lower().startswith(SHORT_NAME):
                    slug = line.split(":", 1)[1].strip() or d
                    break
            break
        try:
            version = json.load(open(m, encoding="utf-8")).get("version")
        except ValueError:
            version = None
        out[slug] = {"folder": os.path.join(root, d), "local_version": version}
    return out


def live(c, slug):
    st, body = get(c, f"/api/v1/tenants/{slug}/releases")
    if st != 200:
        return {"online": NOT_FOUND if st == 404 else FORBIDDEN if st == 403 else f"error {st}"}
    cur = next((r for r in body.get("releases") or [] if r.get("id") == body.get("current")), None)
    if not cur:
        return {"online": "no version published"}
    try:
        version = json.loads(cur.get("manifest") or "{}").get("version")
    except ValueError:
        version = None
    return {"online": "yes", "online_version": version, "published": cur.get("deployed_at")}


def summary(path, scope, c):
    return {"file": path, "scope": scope, "url": c.get("url"), "apps_domain": c.get("apps_domain"),
            "token": "present" if c.get("token") else "missing", "apps": c.get("apps", [])}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--url", required=True)
    i.add_argument("--apps-domain", required=True)
    s = sub.add_parser("set-token")
    a = sub.add_parser("add-app")
    a.add_argument("slug")
    for p in (i, s, a):
        p.add_argument("--global", dest="use_global", action="store_true",
                       help="use ~/.config/citadel/config.json instead of the project one")
    k = sub.add_parser("check")
    k.add_argument("--tenant")
    l = sub.add_parser("apps")
    l.add_argument("--dir", default=".")
    d = sub.add_parser("download")
    d.add_argument("slug")
    d.add_argument("--dir", required=True, help="the app folder: the package goes into <dir>/pkg")
    d.add_argument("--release", help="a release id; default: the one online")
    args = ap.parse_args()
    writing = args.cmd in ("init", "set-token", "add-app")
    path, scope = config_path(write=writing, use_global=getattr(args, "use_global", False),
                              create=args.cmd == "init")
    c = load(path)

    if args.cmd == "init":
        c.update(url=args.url.rstrip("/"), apps_domain=args.apps_domain)
        save(path, c)
        if scope == "project":
            ignore_in_git(path)
    elif args.cmd == "set-token":
        if not sys.stdin.isatty():
            # A chat tool's shell has no terminal: getpass would echo the token.
            print("Run this command in a terminal window (Terminal on Mac, PowerShell on Windows): "
                  "there the token is typed hidden.", file=sys.stderr)
            sys.exit(2)
        t = getpass.getpass("Paste the Citadel token and press Enter (nothing appears while you paste): ").strip()
        if not t:
            sys.exit("no token entered")
        c["token"] = t
        save(path, c)
        print("Token saved. Go back to the chat and write: done")
    elif args.cmd == "add-app":
        c["apps"] = sorted(set(c.get("apps", [])) | {args.slug})
        save(path, c)
    elif args.cmd == "download":
        if not (c.get("url") and c.get("token")):
            sys.exit("portal address or token missing: run citadel-connect first")
        print(json.dumps(download(c, args.slug, args.dir, args.release), ensure_ascii=False, indent=2))
        return 0
    elif args.cmd == "apps":
        apps = local_apps(args.dir)
        for slug in c.get("apps", []):
            apps.setdefault(slug, {"folder": None, "local_version": None})
        if c.get("url") and c.get("token"):
            for slug, a in apps.items():
                a.update(live(c, slug))
        print(json.dumps(apps, ensure_ascii=False, indent=2))
        return 0
    elif args.cmd == "check":
        out = summary(path, scope, c)
        if not c.get("url"):
            out["result"] = "portal address missing: run init"
        else:
            st, _ = get(c, "/login", token=False)
            out["portal"] = "reachable" if st == 200 else f"unreachable ({st or _})"
            app = args.tenant or (c.get("apps") or [None])[0]
            if st == 200 and c.get("token") and app:
                # A wrong token makes any call answer 401.
                st, body = get(c, f"/api/v1/tenants/{app}/releases")
                if st == 200:
                    out["token_valid"] = True
                    out["app_" + app] = {"current_release": body.get("current"), "releases": len(body.get("releases") or [])}
                elif st == 401:
                    out["token_valid"] = False
                elif st == 404:
                    out["token_valid"] = True
                    out["app_" + app] = NOT_FOUND
                else:
                    out["error"] = f"{st}: {body}"
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(summary(path, scope, c), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
