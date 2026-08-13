import csv
from pathlib import Path
from typing import Union, Dict, Any
from app.loaders.base import BaseLoader
from app.models.internal import Document
from app.core.errors import InvalidFileError
from app.core.logging import logger


class CSVLoader(BaseLoader):
    """CSV tabular loader producing structured row representations with column metadata."""

    def load(self, source: Union[str, Path], metadata: Dict[str, Any] = None) -> Document:
        file_path = Path(source)
        if not file_path.exists():
            raise InvalidFileError(f"CSV file not found: {source}")

        try:
            rows_formatted = []
            columns = []
            total_rows = 0

            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    columns = [col.strip() for col in header]

                for row_idx, row in enumerate(reader, start=1):
                    total_rows += 1
                    row_dict = []
                    for c_idx, val in enumerate(row):
                        col_name = columns[c_idx] if c_idx < len(columns) else f"col_{c_idx+1}"
                        row_dict.append(f"{col_name}: {val.strip()}")
                    rows_formatted.append(f"[Row {row_idx}] " + " | ".join(row_dict))

            full_content = f"Columns: {', '.join(columns)}\n\n" + "\n".join(rows_formatted)

            meta = {
                "source_type": "csv",
                "file_name": file_path.name,
                "columns": columns,
                "row_range": f"1-{total_rows}",
                "total_rows": total_rows,
                "file_size": file_path.stat().st_size,
                **(metadata or {})
            }

            return Document(
                source_type="csv",
                source_name=file_path.name,
                source_uri=str(file_path.absolute()),
                content=full_content,
                metadata=meta
            )
        except Exception as e:
            logger.error(f"Failed to load CSV file {source}: {e}")
            raise InvalidFileError(f"Failed to read CSV file {source}: {str(e)}")
