import uvicorn
from fastapi import FastAPI
from src.routes import contacts, auth
from src.database.db import engine
from src.database.models import Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')

@app.get("/")
def read_root():
    return {"message": "Contacts API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)