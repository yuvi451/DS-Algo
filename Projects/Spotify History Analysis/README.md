# Spotify History Analysis

Analysis of ~6 years of personal Spotify listening history (Extended Streaming
History export), used to surface trends and build new playlists.

## Setup

1. Request your data from Spotify: account.spotify.com/privacy/settings ->
   "Extended streaming history". It arrives as a ZIP a few days later.
2. Unzip it and drop the `Streaming_History_Audio_*.json` (or older
   `endsong_*.json`) files into `data/raw/`.
3. `pip install -r requirements.txt`
4. `python src/load_data.py` to sanity-check the loader.

Raw data and generated CSVs are gitignored — nothing personal gets committed.

## Planned analysis

- Listening volume over time (minutes/year, minutes/month)
- Top artists/tracks per year, and all-time
- Listening habits: time of day, day of week, seasonal patterns
- Skip rate and how it's changed over time
- "Discovery" rate: new artists/tracks per month vs. repeat listens
- Longest streaks, biggest binge days
- Playlist generation from the above (e.g. yearly recaps, late-night
  listening, most-replayed deep cuts, rediscovered old favorites) pushed to
  Spotify directly.

## Status

Scaffold only — waiting on the exported data to run the actual analysis.
