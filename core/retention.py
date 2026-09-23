"""Deletes customer video files a set number of days after an order is finished, to keep storage small.

Used by `python reelflow.py cleanup` on this PC and by the daily Vercel Cron job (`/api/cron/cleanup`).
The order row itself (name, email, style, dates) is kept for accounting - only the video files go.
"""
import time

FINISHED = ("done", "failed")


def _finished_at(o):
    return next((h[0] for h in reversed(o["history"]) if h[1] in FINISHED), None)


def purge_old(queue, store, days=7, log=print):
    if not hasattr(store, "delete"):
        log("storage has no delete() - nothing to clean up")
        return 0
    cutoff = time.time() - days * 86400
    purged = 0
    for status in FINISHED:
        for o in queue.list(status):
            at = _finished_at(o)
            if o.get("purged") or not at or time.mktime(time.strptime(at, "%Y-%m-%d %H:%M:%S")) > cutoff:
                continue
            for key in (o["video"].get("key"), (o.get("output") or {}).get("key")):
                if key:
                    try:
                        store.delete(key)
                    except Exception as e:  # noqa: BLE001 - one missing file must not stop the rest
                        log("failed to delete %s - %s" % (key, e))
            o["purged"] = True
            o["history"].append([time.strftime("%Y-%m-%d %H:%M:%S"), o["status"], "files deleted after %d days" % days])
            queue.save(o)
            purged += 1
            log("purged " + o["id"])
    return purged
