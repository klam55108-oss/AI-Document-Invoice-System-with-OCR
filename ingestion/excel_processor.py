"""Excel and CSV processing via Pandas."""

from pathlib import Path
from typing import Any

import pandas as pd

from core.logging import get_logger

logger = get_logger(__name__)


async def process_excel(file_path: Path) -> dict[str, Any]:
    """Process Excel file and extract data.

    Args:
        file_path: Path to Excel file (.xlsx, .xls, .csv)

    Returns:
        Dictionary with extracted data:
        - text: Tabular data as text representation
        - dataframes: Dictionary of sheet names to DataFrames
        - metadata: File metadata
    """
    logger.info("Processing Excel/CSV file", path=str(file_path))

    try:
        file_ext = file_path.suffix.lower()

        if file_ext == ".csv":
            # Read CSV
            df = pd.read_csv(file_path)
            dataframes = {"Sheet1": df}
        elif file_ext in {".xlsx", ".xls"}:
            # Read Excel (all sheets)
            excel_file = pd.ExcelFile(file_path)
            dataframes = {sheet: excel_file.parse(sheet) for sheet in excel_file.sheet_names}
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        # Convert to text representation
        text_parts = []
        for sheet_name, df in dataframes.items():
            text_parts.append(f"Sheet: {sheet_name}\n")
            text_parts.append(df.to_string())
            text_parts.append("\n")

        text_content = "\n".join(text_parts)

        logger.info(
            "Excel/CSV processed",
            path=str(file_path),
            sheets=len(dataframes),
            rows=sum(len(df) for df in dataframes.values()),
        )

        return {
            "text": text_content,
            "dataframes": {name: df.to_dict("records") for name, df in dataframes.items()},
            "metadata": {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "processor": "pandas",
                "sheets": list(dataframes.keys()),
            },
        }

    except FileNotFoundError as e:
        error_msg = f"Excel/CSV file not found: {file_path}"
        logger.error("Excel/CSV processing failed - file not found", path=str(file_path), error=error_msg)
        raise FileNotFoundError(error_msg) from e
    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "Excel/CSV processing failed",
            path=str(file_path),
            error_type=error_type,
            error=str(e),
            exc_info=True,
        )
        raise RuntimeError(f"Excel/CSV processing failed ({error_type}): {str(e)}") from e

