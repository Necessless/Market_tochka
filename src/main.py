from fastapi import FastAPI 
import uvicorn
from core.config import settings
from api import router as api_router

app = FastAPI()
app.include_router(
    api_router,
    prefix = settings.api.prefix,
)

if __name__ == "__main__":
    uvicorn.run("main:app", reload = True)