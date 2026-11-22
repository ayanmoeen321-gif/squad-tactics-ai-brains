"""Start the game: python run.py, then open http://127.0.0.1:8000"""
from pathlib import Path

import uvicorn

if __name__ == "__main__":
    if not (Path(__file__).parent / "web" / "dist").exists():
        print("The web page is not built yet. Run: cd web, npm install, npm run build")
        print("The API still starts, but the game page will be missing.")
    uvicorn.run("server.main:root", host="127.0.0.1", port=8000)