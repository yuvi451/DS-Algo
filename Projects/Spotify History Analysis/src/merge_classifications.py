"""Merge the per-song era/mood classifications produced by the research
agents into one lookup, join back onto the full listening history, and
report bucket sizes/durations so we can pick which playlists are viable."""

import glob
from pathlib import Path

import pandas as pd

from load_data import load_history

SCRATCH = Path(
    "/tmp/claude-0/-home-user-DS-Algo/126be2cf-9d70-5d12-99e8-5095a5a57d94/scratchpad"
)


def load_song_tags() -> dict:
    tags = {}
    for f in sorted(glob.glob(str(SCRATCH / "*_chunk_*_out.tsv"))):
        language = "Hindi" if Path(f).name.startswith("hindi_") else "Punjabi"
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                parts = [p.strip() for p in line.rstrip("\n").split("|")]
                if len(parts) < 4:
                    continue
                track, artist, era, mood = parts[0], parts[1], parts[2], parts[3]
                tags[(track, artist)] = (era, mood, language)
    return tags


def build_dataset() -> pd.DataFrame:
    df = load_history()
    song_tags = load_song_tags()

    def get_tag(row):
        return song_tags.get((row["track_name"], row["artist_name"]), (None, None, None))

    tagged = df.apply(get_tag, axis=1, result_type="expand")
    df["era"] = tagged[0]
    df["mood"] = tagged[1]
    df["song_language"] = tagged[2]

    # duration estimate: longest single play we observed for this track
    dur = df.groupby(["track_name", "artist_name"])["ms_played"].max() / 60000
    df = df.join(dur.rename("est_duration_min"), on=["track_name", "artist_name"])

    return df


if __name__ == "__main__":
    df = build_dataset()
    classified = df[df["era"].notna()]
    print(f"Classified plays: {len(classified):,} / {len(df):,}")
    print(f"Unique classified tracks: {classified.drop_duplicates(['track_name','artist_name']).shape[0]}")

    tracks = classified.drop_duplicates(["track_name", "artist_name"])[
        ["track_name", "artist_name", "song_language", "era", "mood", "est_duration_min"]
    ]

    print("\n=== Bucket sizes (unique tracks) and total estimated duration ===")
    summary = tracks.groupby(["song_language", "era", "mood"]).agg(
        n_tracks=("track_name", "count"),
        total_minutes=("est_duration_min", "sum"),
    ).sort_values("total_minutes", ascending=False)
    print(summary)

    df.to_parquet(
        Path(__file__).resolve().parent.parent / "output" / "history_with_song_tags.parquet",
        index=False,
    )
    print("\nSaved output/history_with_song_tags.parquet")
