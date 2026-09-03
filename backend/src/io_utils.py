from pathlib import Path
import pandas as pd


def ensure_dirs(*paths: Path) -> None:
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def read_csv(path: Path, usecols=None) -> pd.DataFrame:
    if not Path(path).exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    return pd.read_csv(path, low_memory=False, usecols=usecols)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
