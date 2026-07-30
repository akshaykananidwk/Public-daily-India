"""વિડિયો પોસ્ટર — સ્થિર પોસ્ટર PNG માંથી ટૂંકો MP4 (ધીમો ઝૂમ + વોઈસ-ઓવર).

Reels/Shorts માટે. ffmpeg જોઈએ (સિસ્ટમમાં કે FFMPEG_PATH માં).
વોઈસ-ઓવર વૈકલ્પિક — edge-tts હોય તો ગુજરાતી અવાજ ઉમેરાય.
"""
import asyncio
import os
import shutil
from pathlib import Path

from .paths import STORAGE_DIR

VIDEO_DIR = STORAGE_DIR / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def ffmpeg_path() -> str | None:
    for c in (os.environ.get("FFMPEG_PATH", ""),
              "/opt/pw-browsers/ffmpeg-1011/ffmpeg-linux",
              shutil.which("ffmpeg") or ""):
        if c and Path(c).exists():
            return c
    return shutil.which("ffmpeg")


async def _run(*args) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT)
    out, _ = await proc.communicate()
    return proc.returncode, out.decode(errors="ignore")[-500:]


async def tts_gujarati(text: str, out_path: Path) -> bool:
    """ગુજરાતી વોઈસ-ઓવર (edge-tts). ન હોય તો False."""
    try:
        import edge_tts
    except Exception:
        return False
    try:
        v = "gu-IN-DhwaniNeural"
        communicate = edge_tts.Communicate(text[:600], v)
        await communicate.save(str(out_path))
        return out_path.exists() and out_path.stat().st_size > 0
    except Exception:
        return False


async def make_video(poster_path: str, duration: int = 8,
                     voice_text: str = "") -> dict:
    """પોસ્ટરમાંથી MP4 — ધીમો ઝૂમ; voice_text હોય તો વોઈસ-ઓવર."""
    ff = ffmpeg_path()
    if not ff:
        return {"error": "ffmpeg મળ્યું નથી — ffmpeg.org પરથી ઈન્સ્ટોલ કરો"}
    poster_path = str(poster_path)
    out = VIDEO_DIR / (Path(poster_path).stem + ".mp4")

    # PNG → JPG (વ્યાપક રીતે ડીકોડ થાય): PIL હોય તો
    src = poster_path
    try:
        from PIL import Image
        jpg = VIDEO_DIR / (Path(poster_path).stem + "_src.jpg")
        Image.open(poster_path).convert("RGB").save(jpg, quality=92)
        src = str(jpg)
    except Exception:
        pass

    # વોઈસ-ઓવર બનાવો (વૈકલ્પિક)
    audio = None
    if voice_text:
        a = VIDEO_DIR / (Path(poster_path).stem + ".mp3")
        if await tts_gujarati(voice_text, a):
            audio = a

    # ધીમો ઝૂમ (Ken Burns) — 25fps, 1080x1080
    fps = 25
    frames = duration * fps
    vf = (f"scale=2160:2160,zoompan=z='min(zoom+0.0008,1.15)':"
          f"d={frames}:s=1080x1080:fps={fps},format=yuv420p")
    args = [ff, "-y", "-loop", "1", "-i", src]
    if audio:
        args += ["-i", str(audio)]
    args += ["-t", str(duration), "-vf", vf, "-c:v", "libx264",
             "-pix_fmt", "yuv420p"]
    if audio:
        args += ["-c:a", "aac", "-shortest"]
    args += [str(out)]

    code, log = await _run(*args)
    if code != 0 or not out.exists():
        return {"error": f"ffmpeg ભૂલ: {log[-200:]}"}
    return {"ok": True, "file": str(out),
            "voice": bool(audio), "ms": duration * 1000}
