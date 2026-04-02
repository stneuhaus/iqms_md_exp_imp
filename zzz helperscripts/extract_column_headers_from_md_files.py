"""
General Purpose
- Scan all CSV files under the master-data source directory and extract column headers.
- Build three outputs: base header inventory, mapping-joined view, and aggregated headers
    by `object_type` + `file_intent`.
- Apply data cleanup rules during aggregation (e.g., ignore markers and row drop conditions).

Input Prerequisites
- Source directory containing CSV files: `../master-data/data`.
- Mapping file: `config/loader-file_object-type_mapping.csv` with required columns
    `relative_path`, `filename`, and `object_type`.
- Python environment with `pandas` installed.

Output
- `logs/csv_column_headers_<timestamp>.csv` (base extraction).
- `logs/csv_column_headers_joined_<timestamp>.csv` (after mapping join).
- `logs/csv_column_headers_by_object_type_<timestamp>.csv` (final aggregation).

Start Parameter
- No CLI parameters. Paths are resolved from script location.

Function
- `read_csv_headers`: robust header read with multiple encoding fallbacks.
- `infer_file_intent`: classifies filename intent (`upsert`, `updated`, `update`, `addition`).
- `create_joined_dataframe`: merges extracted rows with object-type mapping.
- `aggregate_headers_by_object_type`: consolidates unique headers per object type and intent.
- `main`: executes end-to-end extraction, join, aggregation, and output writing.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


def get_project_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "config" / "loader-file_object-type_mapping.csv").exists():
            return candidate
    raise FileNotFoundError("Could not locate project root containing config/loader-file_object-type_mapping.csv")


def is_text_header(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return bool(value.strip())


def read_csv_headers(csv_path: Path) -> list[str]:
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    last_error: Exception | None = None

    for encoding in encodings:
        try:
            dataframe = pd.read_csv(csv_path, nrows=0, encoding=encoding)
            headers = [column.strip() for column in dataframe.columns if is_text_header(column)]
            return sorted(set(headers), key=lambda header: header.lower())
        except Exception as error:
            last_error = error

    raise RuntimeError(f"Unable to read headers from {csv_path}: {last_error}")


def collect_csv_files(source_dir: Path) -> list[Path]:
    return sorted(source_dir.rglob("*.csv"), key=lambda path: path.name.lower())


def infer_file_intent(filename: str) -> str:
    filename_lower = filename.lower()
    if "_upsert_" in filename_lower:
        return "upsert"
    if "_ups_" in filename_lower:
        return "upsert"
    if "_update_" in filename_lower:
        return "updated"
    if "_upd_" in filename_lower:
        return "update"
    if "_add_" in filename_lower:
        return "addition"
    return "addition"


def get_relative_path(csv_path: Path, source_dir: Path) -> str:
    relative_dir = csv_path.parent.relative_to(source_dir).as_posix()
    return relative_dir if relative_dir else "."


def to_row(csv_path: Path, source_dir: Path, headers: list[str]) -> dict[str, str]:
    row: dict[str, str] = {
        "relative_path": get_relative_path(csv_path, source_dir),
        "file_intent": infer_file_intent(csv_path.name),
        "filename": csv_path.name,
    }
    for index, header in enumerate(headers, start=1):
        row[f"HEAD{index}"] = header
    return row


def build_dataframe(rows: Iterable[dict[str, str]]) -> pd.DataFrame:
    dataframe = pd.DataFrame(list(rows))
    if dataframe.empty:
        return pd.DataFrame(columns=["relative_path", "file_intent", "filename"])

    head_columns = sorted(
        [column for column in dataframe.columns if column.startswith("HEAD")],
        key=lambda column: int(column[4:]),
    )
    ordered_columns = ["relative_path", "file_intent", "filename", *head_columns]
    dataframe = dataframe.reindex(columns=ordered_columns)
    dataframe = dataframe.sort_values(
        by=["filename", "relative_path"],
        key=lambda series: series.fillna("").astype(str).str.lower(),
    ).reset_index(drop=True)
    return dataframe


def get_head_columns(dataframe: pd.DataFrame) -> list[str]:
    return sorted(
        [column for column in dataframe.columns if column.startswith("HEAD")],
        key=lambda column: int(column[4:]),
    )


def load_object_type_mapping(mapping_file: Path) -> pd.DataFrame:
    if not mapping_file.exists():
        raise FileNotFoundError(f"Mapping file does not exist: {mapping_file}")

    mapping = pd.read_csv(mapping_file, encoding="utf-8")
    required_columns = {"relative_path", "filename", "object_type"}
    missing_columns = required_columns - set(mapping.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Mapping file is missing required columns: {missing_list}")

    mapping = mapping.copy()
    mapping["relative_path"] = mapping["relative_path"].fillna("").astype(str).str.strip()
    mapping["filename"] = mapping["filename"].fillna("").astype(str).str.strip()
    mapping["object_type"] = mapping["object_type"].fillna("").astype(str).str.strip()

    mapping = mapping.drop_duplicates(subset=["relative_path", "filename"], keep="first")
    return mapping[["relative_path", "filename", "object_type"]]


def create_joined_dataframe(headers_df: pd.DataFrame, mapping_df: pd.DataFrame) -> pd.DataFrame:
    joined = headers_df.copy()
    joined["relative_path"] = joined["relative_path"].fillna("").astype(str).str.strip()
    joined["filename"] = joined["filename"].fillna("").astype(str).str.strip()

    joined = joined.merge(mapping_df, on=["relative_path", "filename"], how="left")

    head_columns = get_head_columns(joined)
    ordered_columns = ["relative_path", "filename", "object_type", "file_intent", *head_columns]
    joined = joined.reindex(columns=ordered_columns)
    return joined


def aggregate_headers_by_object_type(joined_df: pd.DataFrame) -> pd.DataFrame:
    if joined_df.empty:
        return pd.DataFrame(columns=["object_type", "file_intent"])

    head_columns = get_head_columns(joined_df)
    if not head_columns:
        return pd.DataFrame(columns=["object_type", "file_intent"])

    grouped_rows: list[dict[str, str]] = []
    grouped = joined_df.groupby(["object_type", "file_intent"], dropna=False, sort=True)

    for (object_type, file_intent), group in grouped:
        object_type_value = "" if pd.isna(object_type) else str(object_type).strip()
        if not object_type_value:
            continue
        if object_type_value.upper() == "DROP_ROW":
            continue

        headers: set[str] = set()
        drop_row = False
        for column in head_columns:
            values = group[column].dropna().astype(str).str.strip()
            for value in values:
                if not value:
                    continue
                value_lower = value.lower()
                if "verketten" in value_lower:
                    drop_row = True
                    break
                if "ignore." in value_lower:
                    continue
                if "ignore_" in value_lower:
                    continue
                headers.add(value)
            if drop_row:
                break

        if drop_row:
            continue

        sorted_headers = sorted(headers, key=lambda header: header.lower())
        row: dict[str, str] = {
            "object_type": object_type_value,
            "file_intent": "" if pd.isna(file_intent) else str(file_intent),
        }
        for index, header in enumerate(sorted_headers, start=1):
            row[f"HEAD{index}"] = header
        grouped_rows.append(row)

    aggregated = pd.DataFrame(grouped_rows)
    if aggregated.empty:
        return pd.DataFrame(columns=["object_type", "file_intent"])

    aggregated_head_columns = get_head_columns(aggregated)
    aggregated = aggregated.reindex(columns=["object_type", "file_intent", *aggregated_head_columns])
    aggregated = aggregated.sort_values(
        by=["object_type", "file_intent"],
        key=lambda series: series.fillna("").astype(str).str.lower(),
    ).reset_index(drop=True)
    return aggregated


def main() -> None:
    project_root = get_project_root()
    source_dir = (project_root.parent / "master-data" / "data").resolve()
    logs_dir = (project_root / "logs").resolve()
    mapping_file = (project_root / "config" / "loader-file_object-type_mapping.csv").resolve()

    logs_dir.mkdir(parents=True, exist_ok=True)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    csv_files = collect_csv_files(source_dir)
    rows: list[dict[str, str]] = []
    failed_files: list[tuple[Path, str]] = []

    for csv_file in csv_files:
        try:
            headers = read_csv_headers(csv_file)
            rows.append(to_row(csv_file, source_dir, headers))
        except Exception as error:
            failed_files.append((csv_file, str(error)))

    dataframe = build_dataframe(rows)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = logs_dir / f"csv_column_headers_{timestamp}.csv"
    joined_output_file = logs_dir / f"csv_column_headers_joined_{timestamp}.csv"
    aggregated_output_file = logs_dir / f"csv_column_headers_by_object_type_{timestamp}.csv"

    dataframe.to_csv(output_file, index=False, encoding="utf-8")

    mapping_df = load_object_type_mapping(mapping_file)
    joined_df = create_joined_dataframe(dataframe, mapping_df)
    joined_df.to_csv(joined_output_file, index=False, encoding="utf-8")

    aggregated_df = aggregate_headers_by_object_type(joined_df)
    aggregated_df.to_csv(aggregated_output_file, index=False, encoding="utf-8")

    print(f"CSV files discovered: {len(csv_files)}")
    print(f"CSV files processed: {len(rows)}")
    print(f"CSV files failed: {len(failed_files)}")
    print(f"Output file (base): {output_file}")
    print(f"Output file (interim joined): {joined_output_file}")
    print(f"Output file (aggregated): {aggregated_output_file}")

    if failed_files:
        print("Failed files:")
        for path, reason in failed_files:
            print(f"- {path}: {reason}")


if __name__ == "__main__":
    main()
