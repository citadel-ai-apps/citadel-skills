#!/usr/bin/env python3
"""Pubblica un pacchetto su Citadel: zip, caricamento, deploy, stato dei collegamenti.

    python3 publish.py <cartella pkg> --tenant <nome breve> [--dry-run]

Configurazione, nell'ordine: variabili CITADEL_URL, CITADEL_TOKEN, CITADEL_APPS_DOMAIN,
poi ~/.config/citadel/config.json con le chiavi url, token, apps_domain.
Il token non viene mai stampato. Esce con 0 solo se il deploy è riuscito.
"""
import argparse
import io
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
import zipfile

TOP = ("pbapp.json", "pb_hooks", "pb_migrations", "pb_public")
SKIP = {".DS_Store", "Thumbs.db"}
EPOCH = (1980, 1, 1, 0, 0, 0)


def config():
    path = os.path.expanduser("~/.config/citadel/config.json")
    try:
        f = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        f = {}
    c = {
        "url": os.environ.get("CITADEL_URL") or f.get("url"),
        "token": os.environ.get("CITADEL_TOKEN") or f.get("token"),
        "apps_domain": os.environ.get("CITADEL_APPS_DOMAIN") or f.get("apps_domain"),
    }
    missing = [k for k in ("url", "token") if not c[k]]
    if missing:
        sys.exit(f"configurazione mancante: {', '.join(missing)} (variabili CITADEL_* o {path})")
    c["url"] = c["url"].rstrip("/")
    return c


def build_zip(root):
    """Zip riproducibile: ordine fisso, data fissa, permessi 644, niente file di sistema."""
    buf = io.BytesIO()
    names = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for top in TOP:
            p = os.path.join(root, top)
            if os.path.isfile(p):
                paths = [p]
            elif os.path.isdir(p):
                paths = []
                for d, dirs, files in os.walk(p):
                    dirs.sort()
                    paths += [os.path.join(d, n) for n in sorted(files) if n not in SKIP]
            else:
                continue
            for fp in paths:
                rel = os.path.relpath(fp, root).replace(os.sep, "/")
                info = zipfile.ZipInfo(rel, EPOCH)
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, open(fp, "rb").read())
                names.append(rel)
    return buf.getvalue(), names


def call(c, method, path, body=None, ctype=None):
    req = urllib.request.Request(c["url"] + path, data=body, method=method)
    req.add_header("Authorization", "Bearer " + c["token"])
    if ctype:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"error": raw.decode("utf-8", "replace")[:500]}
    except urllib.error.URLError as e:
        sys.exit(f"Citadel non raggiungibile a {c['url']}: {e.reason}")


def multipart(field, filename, data):
    b = uuid.uuid4().hex
    head = (f"--{b}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\n"
            "Content-Type: application/zip\r\n\r\n").encode()
    return head + data + f"\r\n--{b}--\r\n".encode(), f"multipart/form-data; boundary={b}"


def fail(step, status, body):
    msg = body.get("error") if isinstance(body, dict) else body
    print(json.dumps({"ok": False, "passo": step, "stato_http": status, "errore": msg}, ensure_ascii=False, indent=2))
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg")
    ap.add_argument("--tenant", required=True)
    ap.add_argument("--dry-run", action="store_true", help="crea solo lo zip e ne elenca il contenuto")
    a = ap.parse_args()

    data, names = build_zip(a.pkg)
    manifest = json.load(open(os.path.join(a.pkg, "pbapp.json"), encoding="utf-8"))
    if a.dry_run:
        print(json.dumps({"file": names, "byte": len(data), "versione": manifest.get("version")}, indent=2))
        return 0

    c = config()
    t = a.tenant
    body, ctype = multipart("package", f"{t}-{manifest.get('version', 'x')}.zip", data)
    st, rel = call(c, "POST", f"/api/v1/tenants/{t}/releases", body, ctype)
    if st != 201:
        fail("caricamento", st, rel)

    st, dep = call(c, "POST", f"/api/v1/tenants/{t}/releases/{rel['id']}/deploy")
    if st not in (200, 422):
        fail("deploy", st, dep)

    _, eg = call(c, "GET", f"/api/v1/tenants/{t}/egress")
    entries = eg.get("hosts", eg.get("entries", eg)) if isinstance(eg, dict) else eg

    out = {
        "ok": bool(dep.get("deployed")),
        "versione": manifest.get("version"),
        "release": rel["id"],
        "tornato_indietro": dep.get("rolled_back", False),
        "passo_fallito": dep.get("failed_step"),
        "errore": dep.get("error"),
        "autorizzazioni": [
            {"host": g.get("subject"), "tier": g.get("tier"), "decisione": g.get("decision"), "motivo": g.get("reason")}
            for g in dep.get("grants") or []
        ],
        "collegamenti": entries,
    }
    if c["apps_domain"]:
        out["indirizzo"] = f"https://{t}.{c['apps_domain']}/"
    if not out["ok"] and dep.get("logs"):
        out["log"] = dep["logs"][-3000:]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
