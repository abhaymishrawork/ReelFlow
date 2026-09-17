"""Order queue. Swap providers in config.json -> "queue". Every provider exposes the same 5 methods.

Order lifecycle: new -> editing -> done   (or -> failed)
"""
import json, os, secrets, tempfile, threading, time
from . import config

STATUSES = ("new", "editing", "done", "failed")


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


class LocalQueue:
    """One folder per order: <dir>/<id>/order.json. Works offline, zero cost."""

    def __init__(self, cfg):
        self.dir = config.path(cfg["queue"]["dir"])
        try:
            os.makedirs(self.dir, exist_ok=True)
        except OSError:
            # Read-only deployment (e.g. Vercel's serverless filesystem): fall back to /tmp.
            # Orders won't persist across requests there - a real deploy needs hosted storage.
            self.dir = os.path.join(tempfile.gettempdir(), "reelflow-" + os.path.basename(cfg["queue"]["dir"]))
            os.makedirs(self.dir, exist_ok=True)
        self.lock = threading.Lock()

    def _file(self, oid):
        if not oid or not oid.replace("-", "").isalnum():
            raise ValueError("bad order id")
        return os.path.join(self.dir, oid, "order.json")

    def new_id(self):
        return time.strftime("%y%m%d") + "-" + secrets.token_hex(6)

    def create(self, oid, data):
        order = dict(data, id=oid, status="new", created=_now(), history=[[_now(), "new", "order received"]])
        os.makedirs(os.path.dirname(self._file(oid)), exist_ok=True)
        self.save(order)
        return order

    def get(self, oid):
        try:
            f = self._file(oid)
        except ValueError:
            return None
        return json.load(open(f, encoding="utf-8")) if os.path.exists(f) else None

    def save(self, order):
        with self.lock:
            tmp = self._file(order["id"]) + ".tmp"
            json.dump(order, open(tmp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            os.replace(tmp, self._file(order["id"]))

    def set_status(self, oid, status, note="", **fields):
        assert status in STATUSES
        o = self.get(oid)
        o.update(fields)
        o["status"] = status
        o["history"].append([_now(), status, note])
        self.save(o)
        return o

    def list(self, status=None):
        out = []
        for d in os.listdir(self.dir):
            if os.path.isdir(os.path.join(self.dir, d)):
                o = self.get(d)
                if o and (status is None or o["status"] == status):
                    out.append(o)
        return sorted(out, key=lambda o: o["created"])


PROVIDERS = {"local": LocalQueue}
# Hosted queue later (Supabase, Firebase, Airtable ...): write a class with
# new_id/create/get/save/set_status/list, register it here, change config.json -> queue.provider.


def get(cfg=None):
    cfg = cfg or config.load()
    return PROVIDERS[cfg["queue"]["provider"]](cfg)
