"""Video storage. Swap providers in config.json -> "storage". Every provider exposes:

  save_upload(oid, stream, filename) -> key      customer upload
  fetch(oid, key, dest_path)                      raw video -> editing project folder
  put_output(oid, local_path) -> key              publish the finished reel
  output_url(oid, key) -> str                     link the customer downloads from
  local_path(oid, key) -> str | None              lets the website stream a local file
"""
import os, shutil, tempfile
from . import config


def _safe(name):
    base = "".join(c if c.isalnum() or c in "._-" else "_" for c in os.path.basename(name))
    return base[-120:] or "video.mp4"


class LocalStorage:
    """Files stay on this PC in <dir>/<order id>/. The website serves the finished reel."""

    def __init__(self, cfg):
        self.dir = config.path(cfg["storage"]["dir"])
        if not os.access(os.path.dirname(self.dir) or self.dir, os.W_OK):
            # Read-only deployment (e.g. Vercel's serverless filesystem): fall back to /tmp.
            # Uploads won't persist across requests there - a real deploy needs hosted storage.
            self.dir = os.path.join(tempfile.gettempdir(), "reelflow-" + os.path.basename(cfg["storage"]["dir"]))
        self.public = cfg["public_url"].rstrip("/")

    def _p(self, oid, key):
        return os.path.join(self.dir, oid, key)

    def save_upload(self, oid, stream, filename):
        key = "raw_" + _safe(filename)
        os.makedirs(os.path.join(self.dir, oid), exist_ok=True)
        with open(self._p(oid, key), "wb") as f:
            shutil.copyfileobj(stream, f, 8 * 1024 * 1024)
        return key

    def fetch(self, oid, key, dest):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest):
            return dest
        try:
            os.link(self._p(oid, key), dest)       # same drive: instant, no extra disk space
        except OSError:
            shutil.copy2(self._p(oid, key), dest)
        return dest

    def put_output(self, oid, path):
        key = "final_" + _safe(path)
        shutil.copy2(path, self._p(oid, key))
        return key

    def output_url(self, oid, key):
        return "%s/download/%s/%s" % (self.public, oid, key)

    def local_path(self, oid, key):
        p = self._p(oid, key)
        return p if os.path.exists(p) else None


class R2Storage(LocalStorage):
    """Cloudflare R2 or any S3-compatible bucket (R2 free tier: 10 GB, no download fees). Needs `pip install boto3`.
    NOT TESTED YET - switch to it only after one test order."""

    def __init__(self, cfg):
        super().__init__(cfg)
        import boto3
        r = cfg["storage"]["r2"]
        self.bucket = r["bucket"]
        self.s3 = boto3.client("s3", endpoint_url=r["endpoint"], aws_access_key_id=r["access_key"],
                               aws_secret_access_key=r["secret_key"], region_name="auto")

    def save_upload(self, oid, stream, filename):
        key = super().save_upload(oid, stream, filename)
        self.s3.upload_file(self._p(oid, key), self.bucket, "%s/%s" % (oid, key))
        return key

    def fetch(self, oid, key, dest):
        if os.path.exists(self._p(oid, key)):
            return super().fetch(oid, key, dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        self.s3.download_file(self.bucket, "%s/%s" % (oid, key), dest)
        return dest

    def put_output(self, oid, path):
        key = super().put_output(oid, path)
        self.s3.upload_file(self._p(oid, key), self.bucket, "%s/%s" % (oid, key))
        return key

    def output_url(self, oid, key):
        return self.s3.generate_presigned_url("get_object", Params={"Bucket": self.bucket, "Key": "%s/%s" % (oid, key)},
                                              ExpiresIn=7 * 24 * 3600)


class BlobStorage:
    """Videos live in Vercel Blob, so the live site (serverless, no disk) and this PC share storage.
    Customer uploads go straight from the browser to Blob (see web/templates/index.html + api/blob-upload-token.js) -
    save_upload is never called for those orders; the order's video "key" is the full Blob URL instead of a filename.
    fetch/put_output (used by reelflow.py on this PC) use the official `vercel` pip package - run `pip install vercel`
    once locally. Not needed on Vercel itself: the deployed Flask app never calls fetch/put_output, only output_url."""

    def __init__(self, cfg):
        self.token = cfg["storage"]["blob"]["token"]

    def save_upload(self, oid, stream, filename):
        raise NotImplementedError("videos upload directly to Blob from the browser - see api/blob-upload-token.js")

    def fetch(self, oid, key, dest):
        import vercel.blob as blob
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest):
            return dest
        return blob.download_file(key, dest, token=self.token, overwrite=True)

    def put_output(self, oid, path):
        import vercel.blob as blob
        name = "final_" + os.path.basename(path)
        with open(path, "rb") as f:
            result = blob.put("%s/%s" % (oid, name), f.read(), access="public",
                              content_type="video/mp4", add_random_suffix=False,
                              overwrite=True, token=self.token)
        return result.url

    def output_url(self, oid, key):
        return key  # key is already the full Blob URL, set by fetch/put_output above

    def local_path(self, oid, key):
        return None  # never on this machine's disk - the Flask app links straight to the Blob URL


PROVIDERS = {"local": LocalStorage, "r2": R2Storage, "blob": BlobStorage}


def get(cfg=None):
    cfg = cfg or config.load()
    return PROVIDERS[cfg["storage"]["provider"]](cfg)
