#!/usr/bin/env python3
"""Configurazione locale per parlare con Citadel.

    python3 connect.py init --url <portale> --apps-domain <dominio>
    python3 connect.py set-token            # da lanciare nel terminale: il token si digita nascosto
    python3 connect.py add-app <nome breve>
    python3 connect.py check [--tenant <nome breve>]
    python3 connect.py apps [--dir <cartella di lavoro>]

Il file è ~/.config/citadel/config.json (o CITADEL_CONFIG), con permessi 600. Il token non viene mai stampato.
"""
import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request

PATH = os.environ.get("CITADEL_CONFIG") or os.path.expanduser("~/.config/citadel/config.json")


def load():
    try:
        return json.load(open(PATH, encoding="utf-8"))
    except FileNotFoundError:
        return {}


def save(c):
    os.makedirs(os.path.dirname(PATH), mode=0o700, exist_ok=True)
    fd = os.open(PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)
    os.chmod(PATH, 0o600)


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


def summary(c):
    return {"file": PATH, "url": c.get("url"), "apps_domain": c.get("apps_domain"),
            "token": "presente" if c.get("token") else "mancante", "app": c.get("apps", [])}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--url", required=True)
    i.add_argument("--apps-domain", required=True)
    sub.add_parser("set-token")
    a = sub.add_parser("add-app")
    a.add_argument("slug")
    k = sub.add_parser("check")
    k.add_argument("--tenant")
    l = sub.add_parser("apps")
    l.add_argument("--dir", default=".")
    args = ap.parse_args()
    c = load()

    if args.cmd == "init":
        c.update(url=args.url.rstrip("/"), apps_domain=args.apps_domain)
        save(c)
    elif args.cmd == "set-token":
        t = getpass.getpass("Token Citadel (non viene mostrato): ").strip()
        if not t:
            sys.exit("nessun token inserito")
        c["token"] = t
        save(c)
    elif args.cmd == "add-app":
        c["apps"] = sorted(set(c.get("apps", [])) | {args.slug})
        save(c)
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
        out = summary(c)
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
    print(json.dumps(summary(c), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
