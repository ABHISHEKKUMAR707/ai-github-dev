from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api.routes import auth, agent, voice, repos
from api.middleware.rate_limit import RateLimitMiddleware
from config.settings import settings

app = FastAPI(
    title="AI GitHub Dev",
    description="Modify GitHub repos using natural language",
    version="0.1.0"
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(agent.router)
app.include_router(voice.router)
app.include_router(repos.router)

@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}

@app.get("/")
async def frontend():
    return FileResponse("sandbox/index.html")
