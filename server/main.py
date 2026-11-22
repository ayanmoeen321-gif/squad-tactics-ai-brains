from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from server.app import app as api

root = FastAPI(title="Squad Tactics (game + API)")
root.mount("/api", api)

DIST = Path(__file__).resolve().parent.parent / "web" / "dist"
if DIST.exists():
    root.mount("/", StaticFiles(directory=DIST, html=True), name="web")