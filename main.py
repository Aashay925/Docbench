"""
Production ASGI Entrypoint for DocBench on FastAPI Cloud, Docker, and Cloud Run.
"""

import sys
from pathlib import Path

# Add src to Python module path
root_dir = Path(__file__).resolve().parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from docbench.api.app import app, create_app

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
