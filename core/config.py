"""Loads config.json. Any string value "env:NAME" is read from the environment, so secrets never live in the file."""
import json, os

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))


def _resolve(v):
    if isinstance(v, str) and v.startswith("env:"):
        return os.environ.get(v[4:], "")
    if isinstance(v, dict):
        return {k: _resolve(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_resolve(x) for x in v]
    return v


def load():
    cfg = _resolve(json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8")))
    lib = json.load(open(os.path.join(ROOT, "styles.json"), encoding="utf-8"))
    cfg["styles"], cfg["categories"], cfg["before_after"] = lib["styles"], lib["categories"], lib.get("before_after")
    cfg["caption_styles"], cfg["tiers"] = lib.get("caption_styles", []), lib.get("tiers", [])
    # On Vercel (VERCEL is set automatically) or when this PC is set to process real live orders
    # (REELFLOW_REMOTE=1 in .env), switch to the shared Supabase queue + Vercel Blob storage instead
    # of this machine's local orders/ folder - the live site's serverless functions have no disk.
    if os.environ.get("VERCEL") or os.environ.get("REELFLOW_REMOTE"):
        cfg["queue"]["provider"] = "supabase"
        cfg["storage"]["provider"] = "blob"
    return cfg


def path(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)
