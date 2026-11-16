#!/usr/bin/env python3
"""Check a Citadel package folder locally, with the same rules as the upload.

    python3 check_package.py <pkg folder>

Prints `ok`, or one error per line and then exits with 1. Warnings go to stderr.
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
METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"}
LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
VERSION = re.compile(r"^\d+\.(\d+|x|\*)(\.(\d+|x|\*))?$")
# Runtimes the platform builds (images/pb-hardened/versions.txt in the Citadel repo).
# 0.22.55 is there too, but it has a different JS API and these skills do not use it.
PLATFORM_PB = ("0.38.2", "0.40.4", "0.41.1", "0.42.2")
# Top-level names that never resolve publicly: the server refuses them.
RESERVED_TLDS = {"internal", "local", "localdomain", "localhost", "home", "lan", "corp",
                 "intranet", "test", "example", "invalid", "onion"}
# A few public suffixes where anyone gets a name. The server checks the full Public
# Suffix List; this short list only catches the common mistakes locally.
PUBLIC_SUFFIXES = {"github.io", "gitlab.io", "herokuapp.com", "netlify.app", "vercel.app",
                   "pages.dev", "workers.dev", "azurewebsites.net", "cloudfront.net",
                   "appspot.com", "web.app", "firebaseapp.com", "blogspot.com"}
SECOND_LEVEL = {"co", "com", "org", "net", "gov", "edu", "ac", "ne", "or", "go"}


def check_tree(root, errors):
    files = total = 0
    for name in sorted(os.listdir(root)):
        if name not in TOP:
            errors.append(f"{name}: not allowed here, the package only accepts {', '.join(sorted(TOP))}")
    for dirpath, dirnames, filenames in os.walk(root):
        for n in dirnames + filenames:
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, root)
            st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode):
                errors.append(f"{rel}: symbolic link, not allowed")
                continue
            if n in dirnames:
                continue
            files += 1
            total += st.st_size
            if st.st_mode & (stat.S_ISUID | stat.S_ISGID) or st.st_mode & 0o111:
                errors.append(f"{rel}: executable or setuid, remove the permission (chmod 644)")
            top = rel.split(os.sep)[0]
            if top in ("pb_hooks", "pb_migrations") and not n.endswith(".js"):
                errors.append(f"{rel}: only .js files are allowed in {top}/")
    if files > MAX_FILES:
        errors.append(f"{files} files: the maximum is {MAX_FILES}")
    if total > MAX_BYTES:
        errors.append(f"{total} bytes: the maximum is {MAX_BYTES}")


def public_suffix(bare):
    """Roughly: is bare a suffix under which strangers register names?"""
    labels = bare.split(".")
    if bare in PUBLIC_SUFFIXES or len(labels) < 2:
        return True
    # co.uk, com.au, ac.jp…: a generic second level under a two-letter country code.
    return len(labels) == 2 and len(labels[1]) == 2 and labels[0] in SECOND_LEVEL


def check_host(h, apps_domain=None):
    if not isinstance(h, str) or not h:
        return "must be a host name"
    if h != h.lower():
        return "must be lowercase"
    if any(c in h for c in "/:@ \t"):
        return "a host name only, not a URL, port or user@host"
    if len(h) > 253:
        return "longer than 253 characters"
    wild = h.startswith("*.")
    bare = h[2:] if wild else h
    if "*" in bare:
        return "only the leftmost label may be a wildcard, as *.example.com"
    try:
        ipaddress.ip_address(bare.strip("[]"))
        return "IP address, host names are required"
    except ValueError:
        pass
    labels = bare.split(".")
    if labels[-1].isdigit():
        return "IP address in shorthand form, host names are required"
    if len(labels) < 2:
        return "wildcard on a top-level domain, not allowed" if wild else "not a fully qualified host name"
    if not all(LABEL.match(l) for l in labels):
        return "not a valid host name"
    if wild and public_suffix(bare):
        return "wildcard on a public suffix, where anyone can register names"
    if apps_domain:
        d = apps_domain.rpartition("://")[2].strip(".").lower()
        if d and (bare == d or bare.endswith("." + d)):
            return "Citadel's own apps domain, not reachable from an app"
    if labels[-1] in RESERVED_TLDS:
        return "reserved name that never resolves on the internet"
    return None


def check_request(where, method, path, expect, errors):
    if method not in METHODS:
        errors.append(f"pbapp.json {where}: invalid method {method!r}")
    if not isinstance(path, str) or not path.startswith("/"):
        errors.append(f"pbapp.json {where}: path must start with /")
    elif ".." in path:
        errors.append(f"pbapp.json {where}: path must not contain ..")
    if not isinstance(expect, int) or not 100 <= expect <= 599:
        errors.append(f"pbapp.json {where}: expectStatus must be an HTTP status code")


def parse_version(v):
    """(major, minor, patch) with None for a wildcard part; None if not a version."""
    if not isinstance(v, str) or not VERSION.match(v):
        return None
    parts = [None if p in ("x", "*") else int(p) for p in v.split(".")]
    if len(parts) == 2:
        parts.append(None)
    if parts[1] is None:
        parts[2] = None
    return tuple(parts)


def low(v):
    return tuple(0 if p is None else p for p in v)


def high(v):
    return tuple(1 << 30 if p is None else p for p in v)


def check_range(pb, errors, warnings):
    lo, hi = pb.get("min"), pb.get("max")
    parsed = {}
    for k, v in (("min", lo), ("max", hi)):
        if v is None or v == "":
            continue  # an absent bound is open, as on the server
        parsed[k] = parse_version(v)
        if parsed[k] is None:
            errors.append(f"pbapp.json: pocketbase.{k} {v!r} is not a version (e.g. 0.42.x)")
    if None in parsed.values():
        return
    if "min" in parsed and "max" in parsed and low(parsed["min"]) > high(parsed["max"]):
        errors.append(f"pbapp.json: pocketbase.min {lo} is above max {hi}")
        return
    ok = [r for r in PLATFORM_PB
          if ("min" not in parsed or low(parse_version(r)) >= low(parsed["min"]))
          and ("max" not in parsed or low(parse_version(r)) <= high(parsed["max"]))]
    if not ok:
        errors.append(f"pbapp.json: pocketbase range matches none of the platform's versions ({', '.join(PLATFORM_PB)})")
    elif ok[-1] != PLATFORM_PB[-1]:
        warnings.append(f"pbapp.json: pocketbase.max excludes {PLATFORM_PB[-1]}: an app created on it, "
                        "or upgraded to it, will refuse this package")


def check_manifest(root, errors, warnings, apps_domain=None):
    p = os.path.join(root, "pbapp.json")
    if not os.path.isfile(p):
        errors.append("pbapp.json: missing")
        return
    try:
        m = json.load(open(p, encoding="utf-8"))
    except ValueError as e:
        errors.append(f"pbapp.json: invalid JSON ({e})")
        return
    if m.get("schemaVersion") != 1:
        errors.append("pbapp.json: schemaVersion must be 1")
    for k in ("name", "version"):
        v = m.get(k)
        if not isinstance(v, str) or not v.strip() or len(v) > 64:
            errors.append(f"pbapp.json: {k} is required, at most 64 characters")
        elif not v.isprintable():
            errors.append(f"pbapp.json: {k} contains a non-printable character")
    check_range(m.get("pocketbase") or {}, errors, warnings)
    eg = m.get("egress") or []
    if not isinstance(eg, list):
        errors.append("pbapp.json: egress must be a list")
        eg = []
    if len(set(eg)) != len(eg):
        errors.append("pbapp.json: egress has duplicates")
    for h in eg:
        why = check_host(h, apps_domain)
        if why:
            errors.append(f"pbapp.json egress {h!r}: {why}")
    hc = m.get("healthcheck") or {}
    check_request("healthcheck", "GET", hc.get("path", "/api/health"), hc.get("expectStatus", 200), errors)
    for i, s in enumerate(m.get("smoke") or []):
        check_request(f"smoke[{i}]", str(s.get("method", "GET")).upper(), s.get("path"), s.get("expectStatus", 200), errors)


def apps_domain_for(start):
    """apps_domain from the citadel-connect configuration, if any (same lookup as publish.py)."""
    if os.environ.get("CITADEL_APPS_DOMAIN"):
        return os.environ["CITADEL_APPS_DOMAIN"]
    path = os.environ.get("CITADEL_CONFIG")
    if not path:
        d = os.path.abspath(start)
        path = os.path.expanduser("~/.config/citadel/config.json")
        while True:
            p = os.path.join(d, ".citadel", "config.json")
            if os.path.isfile(p):
                path = p
                break
            if os.path.exists(os.path.join(d, ".git")) or os.path.dirname(d) == d:
                break
            d = os.path.dirname(d)
    try:
        return json.load(open(path, encoding="utf-8")).get("apps_domain")
    except (OSError, ValueError):
        return None


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__.strip())
        return 2
    errors, warnings = [], []
    check_tree(sys.argv[1], errors)
    check_manifest(sys.argv[1], errors, warnings, apps_domain_for(sys.argv[1]))
    print("\n".join(errors) if errors else "ok")
    for w in warnings:
        print("warning: " + w, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
