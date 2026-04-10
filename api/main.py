from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth
from config.settings import settings

app = FastAPI(
    title='AI GitHub Dev',
    description='Modify GitHub repos using natural language',
    version='0.1.0'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)

@app.get('/health')
async def health():
    return {'status': 'ok', 'env': settings.app_env}
