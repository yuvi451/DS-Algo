"""Language/genre/mood analysis layered on top of the artist classification
in classify.py. Produces the monthly phase chart and per-bucket track rankings
used to build language-segregated, genre/mood-aware playlists."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from classify import ARTIST_TAGS, GHAZAL_QAWALI_ARTISTS, UNCERTAIN_ARTISTS
from load_data import load_history

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def tag_artist(artist: str):
    if artist in UNCERTAIN_ARTISTS:
        return ("Unclassified", "Unclassified", None)
    return ARTIST_TAGS.get(artist, ("Unclassified", "Unclassified", None))


def add_tags(df: pd.DataFrame) -> pd.DataFrame:
    tags = df["artist_name"].apply(tag_artist)
    df = df.copy()
    df["language"] = tags.apply(lambda t: t[0])
    df["genre"] = tags.apply(lambda t: t[1])
    df["mood"] = tags.apply(lambda t: t[2])
    df["is_ghazal_qawali"] = df["artist_name"].isin(GHAZAL_QAWALI_ARTISTS)
    return df


def monthly_language_share(df: pd.DataFrame) -> pd.DataFrame:
    pivot = (
        df[df["language"] != "Unclassified"]
        .groupby(["month", "language"])["minutes_played"]
        .sum()
        .unstack(fill_value=0)
    )
    return pivot


def plot_phases(pivot: pd.DataFrame, filename: str) -> None:
    fig, ax = plt.subplots(figsize=(16, 6))
    pivot.plot(kind="area", stacked=True, ax=ax, linewidth=0)
    ax.set_title("Listening 'phases': minutes per month by language")
    ax.set_ylabel("minutes")
    ax.set_xlabel("month")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.close(fig)


def top_tracks(df: pd.DataFrame, language=None, mood=None, n=20) -> pd.DataFrame:
    sub = df
    if language:
        sub = sub[sub["language"] == language]
    if mood:
        sub = sub[sub["mood"] == mood]
    return (
        sub.groupby(["track_name", "artist_name"])["minutes_played"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
    )


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = add_tags(load_history())

    pivot = monthly_language_share(df)
    plot_phases(pivot, "language_phases.png")
    pivot.to_csv(OUTPUT_DIR / "monthly_language_share.csv")

    for lang in ["English", "Punjabi", "Hindi"]:
        print(f"\n{'='*10} {lang} {'='*10}")
        if lang == "English":
            print("\n-- Top by genre --")
            for genre in df[df["language"] == "English"]["genre"].value_counts().head(6).index:
                t = top_tracks(df[df["genre"] == genre], n=10)
                print(f"\n[{genre}]")
                print(t.to_string())
        else:
            for mood in ["Energetic", "Romantic-Soft", "Deep-Soulful", "Nostalgic-Classic"]:
                t = top_tracks(df, language=lang, mood=mood, n=12)
                print(f"\n-- {mood} --")
                print(t.to_string())

    print(f"\n{'='*10} Ghazals & Qawalis (cross-language deep/spiritual) {'='*10}")
    print(top_tracks(df[df["is_ghazal_qawali"]], n=20).to_string())


if __name__ == "__main__":
    main()
