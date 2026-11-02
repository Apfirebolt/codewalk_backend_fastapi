import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pathlib import Path
from auth.router import router as auth_router
from blog.router import router as blog_router


app = FastAPI(
    title="Codewalk Blogging API",
    docs_url="/docs",
    openapi_url="/openapi.json",
    version="0.0.1",
)

# Setup templates directory (looks for a folder named 'templates' in your project root)
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Allowed frontend origins
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://codewalk.in"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root_dashboard(request: Request):
    """Serves the Materialize CSS backend status dashboard."""
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/api/health")
async def health_check():
    return {"message": "API is healthy"}


app.include_router(auth_router, prefix="")
app.include_router(blog_router, prefix="")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)