"""
Local dev server with auto-reload.

Use this instead of `uvicorn main:app --reload` so `.venv` is excluded using an
absolute path. A relative `--reload-exclude '.venv'` often fails to match
WatchFiles' absolute paths, which causes endless reloads while pip touches
site-packages (looks like “glitching”).
"""

from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    venv = ROOT / ".venv"
    excludes = [str(venv.resolve())] if venv.is_dir() else []
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_excludes=excludes,
    )
