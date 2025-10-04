import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from sqlalchemy.pool import StaticPool

# Using a testing database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False }, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db= TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# cleaning db before each test 

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
# tests
# 1
def test_list_tracks_empty():
    response = client.get("/tracks/")
    assert response.status_code == 200
    assert response.json() == []
# 2
def test_create_track(monkeypatch):
   

    # Mock  get_track_metadata_by_isrc
    def fake_spotify_lookup(isrc: str):
        return {
            "title": "Fake Song",
            "image_url": "https://fake.image/url",
            "artists": ["Fake Artist 1", "Fake Artist 2"]
        }

    monkeypatch.setattr("app.routes.tracks.get_track_metadata_by_isrc", fake_spotify_lookup)

    payload = {"isrc": "FAKE123"}

    response = client.post("/tracks/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["isrc"] == "FAKE123"
    assert data["title"] == "Fake Song"
    assert len(data["artists"]) == 2

# 3
# must failed when the track already exist
def test_create_track_duplicate(monkeypatch):

    def fake_spotify_lookup(isrc: str):
        return {
            "title": "Duplicate Song",
            "image_url": "https://fake.image/url",
            "artists": ["Fake Artist"]
        }

    monkeypatch.setattr("app.routes.tracks.get_track_metadata_by_isrc", fake_spotify_lookup)

    payload = {"isrc": "DUPLICATE123"}

    # create first track
    res1 = client.post("/tracks/", json=payload)
    assert res1.status_code == 201

    # try to create another with the same isrc
    res2 = client.post("/tracks/", json=payload)
    assert res2.status_code == 400
    assert res2.json()["detail"] == "Track with this ISRC already exists"

#  4
#  must get the correct track base on ISRC code
def test_get_track_by_isrc(monkeypatch):
   

    def fake_spotify_lookup(isrc: str):
        return {
            "title": "Lookup Song",
            "image_url": "https://fake.image/url",
            "artists": ["Lookup Artist"]
        }

    monkeypatch.setattr("app.routes.tracks.get_track_metadata_by_isrc", fake_spotify_lookup)

    payload = {"isrc": "LOOKUP123"}
    client.post("/tracks/", json=payload)

    response = client.get(f"/tracks/{payload['isrc']}")
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Lookup Song"
    assert data["isrc"] == "LOOKUP123"

# 5
# must search track based on artist name 
def test_get_tracks_by_artist(monkeypatch):
   

    def fake_spotify_lookup(isrc: str):
        return {
            "title": f"Song {isrc}",
            "image_url": "https://fake.image/url",
            "artists": ["Artist One"]
        }

    monkeypatch.setattr("app.routes.tracks.get_track_metadata_by_isrc", fake_spotify_lookup)

    # Creating 2 tracks with the same artist name
    client.post("/tracks/", json={"isrc": "ARTIST001"})
    client.post("/tracks/", json={"isrc": "ARTIST002"})

    response = client.get("/tracks/artist/Artist One")
    assert response.status_code == 200

    tracks = response.json()
    assert len(tracks) == 2
    assert all("Artist One" in [a["name"] for a in t["artists"]] for t in tracks)