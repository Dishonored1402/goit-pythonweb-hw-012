import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.routes import contacts, auth
from src.database.db import engine
from src.database.models import Base

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Contacts REST API",
    description="Professional API for managing personal contacts with JWT Auth & Redis Cache",
    version="1.0.0",
    swagger_ui_parameters={"operationsSorter": "method"}
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix='/api', tags=["Authentication"])
app.include_router(contacts.router, prefix='/api', tags=["Contacts"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Contacts API is running", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)