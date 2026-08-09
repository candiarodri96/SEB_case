from pathlib import Path
from src.ingestion.eod_loader import read_csv


def load_events(date, directory="data/events"):
    path = Path(directory) / f"events_{date}.csv"
    if not path.exists():
        return []
    return read_csv(path)