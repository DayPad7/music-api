from pydantic import BaseModel
from typing import List, Optional

class TrackCreate(BaseModel):
    isrc: str

class ArtistOut(BaseModel):
    id: int
    name: str
    class Config:
        orm_mode = True

class TrackOut(BaseModel):
    id: int
    isrc: str
    title: str
    image_url: Optional[str]
    artists: List[ArtistOut]
    class Config:
        orm_mode = True