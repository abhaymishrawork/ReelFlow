"""Turn a rendered style test into a light web preview + poster.

  python make_preview.py <render.mp4> <style_id> [poster_second=1.9]
"""
import os, subprocess, sys

src, sid = sys.argv[1], sys.argv[2]
at = sys.argv[3] if len(sys.argv) > 3 else "1.9"
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "static", "previews")
os.makedirs(out, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "scale=540:960", "-c:v", "libx264", "-preset", "slow",
                "-crf", "27", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
                os.path.join(out, sid + ".mp4")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", at, "-i", src, "-frames:v", "1", "-vf", "scale=540:960", "-q:v", "4",
                os.path.join(out, sid + ".jpg")], check=True)
print("preview ->", os.path.join(out, sid + ".mp4"), "%.1f MB" % (os.path.getsize(os.path.join(out, sid + ".mp4")) / 1e6))
