"""Generate summary stats and charts from Spotify listening history."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from load_data import load_history

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def top_n(df: pd.DataFrame, by: str, n: int = 15) -> pd.DataFrame:
    return (
        df.groupby(by)
        .agg(plays=("track_name", "count"), minutes=("minutes_played", "sum"))
        .sort_values("minutes", ascending=False)
        .head(n)
    )


def minutes_per_year(df: pd.DataFrame) -> pd.Series:
    return df.groupby("year")["minutes_played"].sum().sort_index()


def listening_by_hour(df: pd.DataFrame) -> pd.Series:
    return df.groupby("hour")["minutes_played"].sum().sort_index()


def listening_by_weekday(df: pd.DataFrame) -> pd.Series:
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return df.groupby("weekday")["minutes_played"].sum().reindex(order)


def skip_rate_per_year(df: pd.DataFrame) -> pd.Series:
    return df.groupby("year")["skipped"].mean().sort_index()


def top_tracks_per_year(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    per_year = (
        df.groupby(["year", "track_name", "artist_name"])["minutes_played"]
        .sum()
        .reset_index()
    )
    return (
        per_year.sort_values(["year", "minutes_played"], ascending=[True, False])
        .groupby("year")
        .head(n)
    )


def new_artists_per_month(df: pd.DataFrame) -> pd.Series:
    first_seen = df.groupby("artist_name")["played_at"].min().dt.to_period("M")
    return first_seen.value_counts().sort_index()


def save_bar(series: pd.Series, title: str, ylabel: str, filename: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    series.plot(kind="bar", ax=ax)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = load_history()

    print(f"\nTotal plays: {len(df):,}")
    print(f"Total minutes: {df['minutes_played'].sum():,.0f} "
          f"(~{df['minutes_played'].sum() / 60 / 24:.1f} days)")
    print(f"Date range: {df['played_at'].min().date()} to {df['played_at'].max().date()}")
    print(f"Unique artists: {df['artist_name'].nunique():,}")
    print(f"Unique tracks: {df['track_name'].nunique():,}")

    print("\n== Top 15 artists (all-time, by minutes) ==")
    top_artists = top_n(df, "artist_name")
    print(top_artists)
    top_artists.to_csv(OUTPUT_DIR / "top_artists.csv")

    print("\n== Top 15 tracks (all-time, by minutes) ==")
    top_tracks = top_n(df, "track_name")
    print(top_tracks)
    top_tracks.to_csv(OUTPUT_DIR / "top_tracks.csv")

    print("\n== Minutes per year ==")
    mpy = minutes_per_year(df)
    print(mpy)
    save_bar(mpy, "Minutes listened per year", "minutes", "minutes_per_year.png")

    print("\n== Skip rate per year ==")
    spy = skip_rate_per_year(df)
    print(spy)

    print("\n== Listening by hour of day ==")
    lbh = listening_by_hour(df)
    save_bar(lbh, "Minutes listened by hour of day (UTC)", "minutes", "by_hour.png")

    print("\n== Listening by weekday ==")
    lbw = listening_by_weekday(df)
    save_bar(lbw, "Minutes listened by weekday", "minutes", "by_weekday.png")

    tpy = top_tracks_per_year(df)
    tpy.to_csv(OUTPUT_DIR / "top_tracks_per_year.csv", index=False)
    print("\n== Top 5 tracks per year saved to output/top_tracks_per_year.csv ==")

    df.to_parquet(OUTPUT_DIR / "history_clean.parquet", index=False)
    print(f"\nCleaned dataset saved to {OUTPUT_DIR / 'history_clean.parquet'}")


if __name__ == "__main__":
    main()
