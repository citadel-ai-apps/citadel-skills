#!/usr/bin/env python3
"""Controlla in locale una cartella di pacchetto Citadel, con le stesse regole del caricamento.

    python3 check_package.py <cartella pkg>

Stampa `ok` oppure un errore per riga, e in quel caso esce con 1.
"""
import ipaddress
import json
import os
import re
import stat
import sys

MAX_BYTES = 50 << 20
MAX_FILES = 2000
TOP = {"pbapp.json", "pb_hooks", "pb_migrations", "pb_public"}
METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
VERSION = re.compile(r"^\d+\.(\d+|x)(\.(\d+|x))?$")


def check_tree(root, errors):
    files = total = 0
    for name in sorted(os.listdir(root)):
        if name not in TOP:
            errors.append(f"{name}: fuori posto, il pacchetto ammette solo {', '.join(sorted(TOP))}")
    for dirpath, dirnames, filenames in os.walk(root):
        for n in dirnames + filenames:
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, root)
            st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode):
                errors.append(f"{rel}: link simbolico, non ammesso")
                continue
            if n in dirnames:
                continue
            files += 1
            total += st.st_size
            if st.st_mode & (stat.S_ISUID | stat.S_ISGID) or st.st_mode & 0o111:
                errors.append(f"{rel}: eseguibile o setuid, togli il permesso (chmod 644)")
            top = rel.split(os.sep)[0]
            if top in ("pb_hooks", "pb_migrations") and not n.endswith(".js"):
                errors.append(f"{rel}: in {top}/ sono ammessi solo file .js")
    if files > MAX_FILES:
        errors.append(f"{files} file: il massimo è {MAX_FILES}")
    if total > MAX_BYTES:
        errors.append(f"{total} byte: il massimo è {MAX_BYTES}")


def check_host(h):
    if not isinstance(h, str) or not h:
        return "deve essere un nome di host"
    try:
        ipaddress.ip_address(h.strip("[]"))
        return "indirizzo IP, servono nomi di host"
    except ValueError:
        pass
    labels = h.lower().split(".")
    wild = labels[0] == "*"
    if wild:
        labels = labels[1:]
        if len(labels) < 2:
            return "jolly sul dominio di primo livello, non ammesso"
    if len(labels) < 2 or not all(LABEL.match(l) for l in labels):
        return "non è un nome di host valido"
    if labels[-1] in ("localhost", "local", "internal", "lan", "home"):
        return "nome di rete interna, non raggiungibile"
    return None


def check_request(where, method, path, expect, errors):
    if method not in METHODS:
        errors.append(f"pbapp.json {where}: metodo {method!r} non valido")
    if not isinstance(path, str) or not path.startswith("/"):
        errors.append(f"pbapp.json {where}: path deve iniziare con /")
    if not isinstance(expect, int) or not 100 <= expect <= 599:
        errors.append(f"pbapp.json {where}: expectStatus deve essere un codice HTTP")


def check_manifest(root, errors):
    p = os.path.join(root, "pbapp.json")
    if not os.path.isfile(p):
        errors.append("pbapp.json: manca")
        return
    try:
        m = json.load(open(p, encoding="utf-8"))
    except ValueError as e:
        errors.append(f"pbapp.json: JSON non valido ({e})")
        return
    if m.get("schemaVersion") != 1:
        errors.append("pbapp.json: schemaVersion deve essere 1")
    for k in ("name", "version"):
        v = m.get(k)
        if not isinstance(v, str) or not v.strip() or len(v) > 64:
            errors.append(f"pbapp.json: {k} obbligatorio, al massimo 64 caratteri")
    pb = m.get("pocketbase") or {}
    for k in ("min", "max"):
        v = pb.get(k)
        if v is not None and not (isinstance(v, str) and VERSION.match(v) and not v.startswith("x")):
            errors.append(f"pbapp.json: pocketbase.{k} {v!r} non è una versione (es. 0.40.x)")
    eg = m.get("egress") or []
    if not isinstance(eg, list):
        errors.append("pbapp.json: egress deve essere una lista")
        eg = []
    if len(set(eg)) != len(eg):
        errors.append("pbapp.json: egress contiene doppioni")
    for h in eg:
        why = check_host(h)
        if why:
            errors.append(f"pbapp.json egress {h!r}: {why}")
    hc = m.get("healthcheck") or {}
    check_request("healthcheck", "GET", hc.get("path", "/api/health"), hc.get("expectStatus", 200), errors)
    for i, s in enumerate(m.get("smoke") or []):
        check_request(f"smoke[{i}]", str(s.get("method", "GET")).upper(), s.get("path"), s.get("expectStatus", 200), errors)


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__.strip())
        return 2
    errors = []
    check_tree(sys.argv[1], errors)
    check_manifest(sys.argv[1], errors)
    print("\n".join(errors) if errors else "ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
