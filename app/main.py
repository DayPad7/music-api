from fastapi import FastAPI

from app.database import engine, Base

from app.routes.tracks import router as tracks_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Welcome to Music API"}


app.include_router(tracks_router)