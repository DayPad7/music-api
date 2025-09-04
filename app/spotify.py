import requests
import os

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    resp = requests.post(
        url,
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def get_track_metadata_by_isrc(isrc):
    token = get_spotify_token()
    url = f"https://api.spotify.com/v1/search?q=isrc:{isrc}&type=track"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    items = resp.json()["tracks"]["items"]
    if not items:
        return None
    # Elige el de mayor popularidad
    best = max(items, key=lambda x: x.get("popularity", 0))
    return {
        "title": best["name"],
        "image_url": best["album"]["images"][0]["url"] if best["album"]["images"] else None,
        "artists": [a["name"] for a in best["artists"]],
    }