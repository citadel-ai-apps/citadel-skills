#!/usr/bin/env python3
"""Configurazione locale per parlare con Citadel.

    python3 connect.py init --url <portale> --apps-domain <dominio> [--global]
    python3 connect.py set-token [--global]  # da lanciare nel terminale: il token si digita nascosto
    python3 connect.py add-app <nome breve> [--global]
    python3 connect.py check [--tenant <nome breve>]
    python3 connect.py apps [--dir <cartella di lavoro>]

Dove sta la configurazione (file con permessi 600, il token non viene mai stampato):
- CITADEL_CONFIG, se impostata, vale per tutto.
- Lettura: il .citadel/config.json più vicino, dalla cartella corrente fino alla radice
  del repo git; se non c'è, ~/.config/citadel/config.json.
- Scrittura: init crea .citadel/config.json nella radice del repo (o nella cartella
  corrente, fuori da git) e aggiunge .citadel/ al .gitignore. set-token e add-app
  scrivono nel file del progetto e si fermano se non c'è. Con --global si usa
  ~/.config/citadel/config.json.
"""
import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request

GLOBAL = os.path.expanduser("~/.config/citadel/config.json")
LOCAL = os.path.join(".citadel", "config.json")


def repo_root(start):
    """La radice del repo git che contiene start, oppure None."""
    d = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


def project_config(start="."):
    """Il .citadel/config.json più vicino, salendo da start fino alla radice del repo."""
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
    """Il file da usare e il suo ambito: variabile, globale o progetto."""
    env = os.environ.get("CITADEL_CONFIG")
    if env:
        return env, "variabile CITADEL_CONFIG"
    if use_global:
        return GLOBAL, "globale"
    found = project_config()
    if found:
        return found, "progetto"
    if create:
        return os.path.join(repo_root(".") or os.path.abspath("."), LOCAL), "progetto"
    if write:
        sys.exit("questo progetto non ha ancora una configurazione Citadel: lancia prima "
                 "`connect.py init` qui, oppure aggiungi --global per usare quella globale")
    return GLOBAL, "globale"


def ignore_in_git(path):
    """Aggiunge .citadel/ al .gitignore della radice del repo, se il file è dentro un repo."""
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
                return r.status, None  # la pagina di login è HTML
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except ValueError:
            return e.code, None
    except (urllib.error.URLError, OSError) as e:
        return 0, str(getattr(e, "reason", e))


def local_apps(root):
    """Cartelle di app sotto root: contengono pkg/pbapp.json. Il nome breve viene dalla scheda."""
    out = {}
    for d in sorted(os.listdir(root)):
        m = os.path.join(root, d, "pkg", "pbapp.json")
        if not os.path.isfile(m):
            continue
        slug = d
        scheda = os.path.join(root, d, "scheda.md")
        if os.path.isfile(scheda):
            for line in open(scheda, encoding="utf-8"):
                if line.strip().lower().startswith("- nome breve:"):
                    slug = line.split(":", 1)[1].strip() or d
                    break
        try:
            version = json.load(open(m, encoding="utf-8")).get("version")
        except ValueError:
            version = None
        out[slug] = {"cartella": os.path.join(root, d), "versione_locale": version}
    return out


def live(c, slug):
    st, body = get(c, f"/api/v1/tenants/{slug}/releases")
    if st != 200:
        return {"online": "non esiste" if st == 404 else f"errore {st}"}
    cur = next((r for r in body.get("releases") or [] if r.get("id") == body.get("current")), None)
    if not cur:
        return {"online": "nessuna versione pubblicata"}
    try:
        version = json.loads(cur.get("manifest") or "{}").get("version")
    except ValueError:
        version = None
    return {"online": "sì", "versione_online": version, "pubblicata": cur.get("deployed_at")}


def summary(path, scope, c):
    return {"file": path, "ambito": scope, "url": c.get("url"), "apps_domain": c.get("apps_domain"),
            "token": "presente" if c.get("token") else "mancante", "app": c.get("apps", [])}


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
                       help="usa ~/.config/citadel/config.json invece di quello del progetto")
    k = sub.add_parser("check")
    k.add_argument("--tenant")
    l = sub.add_parser("apps")
    l.add_argument("--dir", default=".")
    args = ap.parse_args()
    writing = args.cmd in ("init", "set-token", "add-app")
    path, scope = config_path(write=writing, use_global=getattr(args, "use_global", False),
                              create=args.cmd == "init")
    c = load(path)

    if args.cmd == "init":
        c.update(url=args.url.rstrip("/"), apps_domain=args.apps_domain)
        save(path, c)
        if scope == "progetto":
            ignore_in_git(path)
    elif args.cmd == "set-token":
        t = getpass.getpass("Token Citadel (non viene mostrato): ").strip()
        if not t:
            sys.exit("nessun token inserito")
        c["token"] = t
        save(path, c)
    elif args.cmd == "add-app":
        c["apps"] = sorted(set(c.get("apps", [])) | {args.slug})
        save(path, c)
    elif args.cmd == "apps":
        apps = local_apps(args.dir)
        for slug in c.get("apps", []):
            apps.setdefault(slug, {"cartella": None, "versione_locale": None})
        if c.get("url") and c.get("token"):
            for slug, a in apps.items():
                a.update(live(c, slug))
        print(json.dumps(apps, ensure_ascii=False, indent=2))
        return 0
    elif args.cmd == "check":
        out = summary(path, scope, c)
        if not c.get("url"):
            out["esito"] = "manca l'indirizzo: lancia init"
        else:
            st, _ = get(c, "/login", token=False)
            out["portale"] = "raggiungibile" if st == 200 else f"non raggiungibile ({st or _})"
            app = args.tenant or (c.get("apps") or [None])[0]
            if st == 200 and c.get("token") and app:
                # Un token sbagliato fa rispondere 401 a qualsiasi chiamata.
                st, body = get(c, f"/api/v1/tenants/{app}/releases")
                if st == 200:
                    out["token_valido"] = True
                    out["app_" + app] = {"release_corrente": body.get("current"), "release": len(body.get("releases") or [])}
                elif st == 401:
                    out["token_valido"] = False
                elif st == 404:
                    out["app_" + app] = "non esiste: chiedi all'operatore di crearla"
                else:
                    out["errore"] = f"{st}: {body}"
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(summary(path, scope, c), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
