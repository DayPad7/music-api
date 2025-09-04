from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app import models
from app import schemas
from app.spotify import get_track_metadata_by_isrc

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Welcome to Music API"}

# post for creating tracks using ISRC
@app.post("/tracks/", response_model=schemas.TrackOut, status_code=status.HTTP_201_CREATED)
def create_track(track: schemas.TrackCreate, db: Session = Depends(get_db)):
    
    db_track = db.query(models.Track).filter(models.Track.isrc == track.isrc).first()
    if db_track:
        raise HTTPException(status_code=400, detail="Track with this ISRC already exists")
    # Consulta Spotify
    metadata = get_track_metadata_by_isrc(track.isrc)
    if not metadata:
        raise HTTPException(status_code=404, detail="Track not found in Spotify API")
    # Crea el track
    new_track = models.Track(
        isrc=track.isrc,
        title=metadata["title"],
        image_url=metadata["image_url"]
    )
    db.add(new_track)
    db.commit()
    db.refresh(new_track)
    # adding artists 
    for artist_name in metadata["artists"]:
        artist = models.Artist(name=artist_name, track_id=new_track.id)
        db.add(artist)
    db.commit()
    db.refresh(new_track)
    return new_track

# Endpoint for getting track by ISRC
@app.get("/tracks/{isrc}", response_model=schemas.TrackOut)
def get_track_by_isrc(isrc: str, db: Session = Depends(get_db)):
    track = db.query(models.Track).filter(models.Track.isrc == isrc).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track

# Endpoint for getting tracks by artist (LIKE search, pagination)
@app.get("/tracks/artist/{artist_name}", response_model=list[schemas.TrackOut])
def get_tracks_by_artist(
    artist_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Busca artistas con nombre LIKE
    artists = db.query(models.Artist).filter(models.Artist.name.ilike(f"%{artist_name}%")).all()
    track_ids = list({artist.track_id for artist in artists})
    if not track_ids:
        return []
    tracks = db.query(models.Track).filter(models.Track.id.in_(track_ids)).offset(skip).limit(limit).all()
    return tracks
