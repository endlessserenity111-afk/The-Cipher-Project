from pathlib import Path
from typing import Iterable
import hashlib
import pandas as pd


def ensure_dirs(*paths: Path) -> None:
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    return pd.read_csv(path, low_memory=False)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_files(paths: Iterable[Path]) -> list[dict]:
    rows = []
    for path in paths:
        p = Path(path)
        rows.append({
            "file": p.name,
            "exists": p.exists(),
            "bytes": p.stat().st_size if p.exists() else None,
            "sha256": file_sha256(p) if p.exists() else None,
        })
    return rows
