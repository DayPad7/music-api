from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.spotify import get_track_metadata_by_isrc

router = APIRouter()

@router.get("/tracks/", response_model=list[schemas.TrackOut])
def list_tracks(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    tracks = db.query(models.Track).offset(skip).limit(limit).all()
    return tracks

@router.post("/tracks/", response_model=schemas.TrackOut, status_code=status.HTTP_201_CREATED)
def create_track(track: schemas.TrackCreate, session: Session = Depends(get_db)):
    db_track = session.query(models.Track).filter(models.Track.isrc == track.isrc).first()
    if db_track:
        raise HTTPException(status_code=400, detail="Track with this ISRC already exists")
    metadata = get_track_metadata_by_isrc(track.isrc)
    if not metadata:
        raise HTTPException(status_code=404, detail="Track not found in Spotify API")
    new_track = models.Track(
        isrc=track.isrc,
        title=metadata["title"],
        image_url=metadata["image_url"]
    )
    session.add(new_track)
    session.commit()
    session.refresh(new_track)
    for artist_name in metadata["artists"]:
        artist = models.Artist(name=artist_name, track_id=new_track.id)
        session.add(artist)
    session.commit()
    session.refresh(new_track)
    return new_track

@router.get("/tracks/{isrc}", response_model=schemas.TrackOut)
def get_track_by_isrc(isrc: str, session: Session = Depends(get_db)):
    track = session.query(models.Track).filter(models.Track.isrc == isrc).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track

@router.get("/tracks/artist/{artist_name}", response_model=list[schemas.TrackOut])
def get_tracks_by_artist(
    artist_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_db)
):
    artists = session.query(models.Artist).filter(models.Artist.name.ilike(f"%{artist_name}%")).all()
    track_ids = list({artist.track_id for artist in artists})
    if not track_ids:
        return []
    tracks = session.query(models.Track).filter(models.Track.id.in_(track_ids)).offset(skip).limit(limit).all()
    return tracks