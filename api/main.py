from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth, agent
from api.middleware.rate_limit import RateLimitMiddleware
from config.settings import settings

app = FastAPI(
    title="AI GitHub Dev",
    description="Modify GitHub repos using natural language",
    version="0.1.0"
)

# Rate limiting — must be first
app.add_middleware(RateLimitMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(agent.router)

@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}
