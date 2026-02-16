"""
Simple landing page server - no external dependencies
"""

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

app = FastAPI(title="Lead Generation Services")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve landing page"""
    with open(os.path.join(TEMPLATES_DIR, "index.html"), "r") as f:
        return f.read()

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
