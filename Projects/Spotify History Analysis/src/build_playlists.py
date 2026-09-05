"""Assemble final playlist track lists from the merged song classifications.

Each playlist is defined by a filter over (song_language, era, mood).
Tracks within a playlist are ranked by the listener's own total minutes
played (their real favorites first) and capped so the playlist stays a
focused, curated length while always clearing a 120-minute floor.
"""

from pathlib import Path

import pandas as pd

from classify import ARTIST_TAGS, UNCERTAIN_ARTISTS
from merge_classifications import build_dataset

MIN_PLAYLIST_MINUTES = 120
MAX_TRACKS_CAP = 45  # keeps playlists focused rather than dumping hundreds of songs


def english_genre(artist: str) -> str:
    if artist in UNCERTAIN_ARTISTS:
        return None
    tag = ARTIST_TAGS.get(artist)
    if not tag or tag[0] != "English":
        return None
    return tag[1]


def rank_tracks(df: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    sub = df[mask]
    agg = (
        sub.groupby(["track_name", "artist_name"])
        .agg(user_minutes=("minutes_played", "sum"), duration=("est_duration_min", "first"))
        .sort_values("user_minutes", ascending=False)
    )
    return agg


def build_playlist(df: pd.DataFrame, mask: pd.Series, label: str):
    ranked = rank_tracks(df, mask)
    selected = ranked.head(MAX_TRACKS_CAP)
    total_min = selected["duration"].sum()
    # grow selection if still short of the floor and more tracks exist
    i = MAX_TRACKS_CAP
    while total_min < MIN_PLAYLIST_MINUTES and i < len(ranked):
        selected = ranked.head(i + 10)
        total_min = selected["duration"].sum()
        i += 10
    return selected, total_min


def main():
    df = build_dataset()
    df["english_genre"] = df["artist_name"].apply(english_genre)

    playlists = {}

    lang_mood = df[["song_language", "era", "mood"]]

    defs = [
        ("Punjabi - Old Classics", (df["song_language"] == "Punjabi") & (df["era"] == "Classic")),
        ("Punjabi - Energetic & Party", (df["song_language"] == "Punjabi") & (df["mood"] == "Energetic-Party")),
        ("Punjabi - Romantic", (df["song_language"] == "Punjabi") & (df["mood"] == "Romantic-Happy")),
        ("Punjabi - Heartbreak & Longing", (df["song_language"] == "Punjabi") & (df["mood"] == "Heartbreak-Sad")),
        ("Punjabi - Deep & Soulful", (df["song_language"] == "Punjabi") & (df["mood"] == "Deep-Introspective")),
        ("Hindi - Old Bollywood Classics", (df["song_language"] == "Hindi") & (df["era"] == "Classic")),
        ("Hindi - Romantic", (df["song_language"] == "Hindi") & (df["mood"] == "Romantic-Happy")),
        ("Hindi - Heartbreak & Longing", (df["song_language"] == "Hindi") & (df["mood"] == "Heartbreak-Sad")),
        ("Hindi - Deep & Soulful", (df["song_language"] == "Hindi") & (df["mood"] == "Deep-Introspective")),
        ("Hindi - Energetic & Party", (df["song_language"] == "Hindi") & (df["mood"] == "Energetic-Party")),
        ("Ghazals, Qawalis & Devotional", df["mood"] == "Devotional-Spiritual"),
        ("English - Pop", df["english_genre"].isin(["Pop", "Pop/R&B", "Pop/Rock", "Pop/Soul", "EDM/Pop"])),
        ("English - Rock", df["english_genre"].isin(["Rock", "Rock/Pop", "Alt Rock", "Classic Rock", "Classic Rock/Pop", "Rock/Indie"])),
    ]

    for label, mask in defs:
        selected, total_min = build_playlist(df, mask, label)
        playlists[label] = (selected, total_min)
        hrs = total_min / 60
        print(f"\n=== {label} === {len(selected)} tracks, {total_min:.0f} min ({hrs:.1f} hrs)")
        for (track, artist), row in selected.iterrows():
            print(f"  {track} — {artist}  ({row.user_minutes:.0f} min played)")

    prompts_path = Path(
        "/tmp/claude-0/-home-user-DS-Algo/126be2cf-9d70-5d12-99e8-5095a5a57d94/scratchpad/playlist_prompts.txt"
    )
    with open(prompts_path, "w", encoding="utf-8") as f:
        for label, (selected, total_min) in playlists.items():
            song_list = ", ".join(f"{track} by {artist}" for track, artist in selected.index)
            prompt = (
                f'Create a playlist called "{label}" made up of exactly these songs '
                f"from my Spotify listening history, in this order: {song_list}."
            )
            f.write(f"### {label}\n{prompt}\n\n")
    print(f"\nWrote ready-to-use prompts to {prompts_path}")

    return playlists


if __name__ == "__main__":
    main()
