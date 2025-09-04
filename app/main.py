from fastapi import FastAPI
from app.database import engine, Base
from app import models
app = FastAPI()

Base.metadata.create_all(bind=engine)
@app.get("/")
def root():
    return {"message": "Welcome to Music API 🎶"}
