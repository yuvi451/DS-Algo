"""Load Spotify Extended Streaming History JSON exports into a single DataFrame."""

import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Extended Streaming History field -> normalized column name.
# Spotify has used a couple of different key sets over the years
# (endsong_*.json vs Streaming_History_Audio_*.json); map both.
COLUMN_ALIASES = {
    "ts": "played_at",
    "endTime": "played_at",
    "master_metadata_track_name": "track_name",
    "trackName": "track_name",
    "master_metadata_album_artist_name": "artist_name",
    "artistName": "artist_name",
    "master_metadata_album_album_name": "album_name",
    "ms_played": "ms_played",
    "msPlayed": "ms_played",
    "spotify_track_uri": "track_uri",
    "reason_start": "reason_start",
    "reason_end": "reason_end",
    "shuffle": "shuffle",
    "skipped": "skipped",
    "platform": "platform",
    "conn_country": "country",
}


def load_history(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    files = sorted(data_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(
            f"No JSON files found in {data_dir}. Drop your exported "
            "Streaming_History_Audio_*.json (or endsong_*.json) files there."
        )

    records = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            records.extend(json.load(fh))

    df = pd.DataFrame(records)
    df = df.rename(columns={k: v for k, v in COLUMN_ALIASES.items() if k in df.columns})

    df["played_at"] = pd.to_datetime(df["played_at"], utc=True)
    df["minutes_played"] = df["ms_played"] / 60000

    # Only keep actual music plays (drop podcast/audiobook rows if the
    # export bundles them and they lack a track name).
    df = df[df["track_name"].notna()].copy()

    df["year"] = df["played_at"].dt.year
    df["month"] = df["played_at"].dt.to_period("M").astype(str)
    df["hour"] = df["played_at"].dt.hour
    df["weekday"] = df["played_at"].dt.day_name()

    return df.sort_values("played_at").reset_index(drop=True)


if __name__ == "__main__":
    history = load_history()
    print(f"Loaded {len(history):,} plays across {history['year'].nunique()} years")
    print(history[["played_at", "artist_name", "track_name", "minutes_played"]].head())
