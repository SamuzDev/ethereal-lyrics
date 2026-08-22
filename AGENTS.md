# ethereal-lyrics

Python terminal app displaying synced Spotify lyrics with Rich-based UI.

## Stack

- Python 3.10+
- Rich (terminal UI)
- Spotipy (Spotify API)
- httpx (HTTP client)
- Pydantic (settings)
- LRCLib (free lyrics API)

## Commands

```bash
pip install -e .          # install in dev mode
python -m src.main        # run app
ethereal-lyrics            # run via entry point
```

## Structure

- `src/` — application code
- `graphify-out/` — knowledge graph output
