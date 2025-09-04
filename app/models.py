from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True, index=True)
    isrc = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    image_url = Column(String(500))
    artists = relationship("Artist", back_populates="track")

class Artist(Base):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"))
    track = relationship("Track", back_populates="artists")
