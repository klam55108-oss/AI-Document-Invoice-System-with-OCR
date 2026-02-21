"""File path resolution utility for dashboard file preview."""

from pathlib import Path
from typing import TypedDict


class ResolvedFileInfo(TypedDict, total=False):
    """Result of file path resolution attempt."""

    original_path: str
    resolved_path: Path | None
    exists: bool
    location: str | None  # "original", "encrypted", or None
    error: str | None


def resolve_file_path(
    file_path: str | None,
    file_hash: str | None = None,
    data_dir: Path | str = "data",
) -> ResolvedFileInfo:
    """Resolve file path with fallback to encrypted directory.

    Attempts to locate a file by:
    1. Resolving relative path from data/ directory
    2. If not found and hash provided, checking data/encrypted/ directory
    3. Returning error information if neither location found

    Args:
        file_path: Relative file path from database (e.g., "invoice-1.png")
        file_hash: Optional file hash for encrypted file lookup
        data_dir: Base data directory path (default: "data")

    Returns:
        ResolvedFileInfo dictionary with resolution results
    """
    if not file_path:
        return ResolvedFileInfo(
            original_path="",
            resolved_path=None,
            exists=False,
            location=None,
            error="No file path provided",
        )

    data_path = Path(data_dir) if isinstance(data_dir, str) else data_dir

    # Try original location first
    # Handle both relative paths (hf_datasets/...) and paths with data/ prefix (data/hf_datasets/...)
    file_path_obj = Path(file_path)
    
    # If file_path starts with data/, strip it to avoid data/data/ duplication
    if file_path_obj.parts and file_path_obj.parts[0] == "data":
        # Strip the leading "data" part
        relative_path = Path(*file_path_obj.parts[1:])
        original_resolved = data_path / relative_path
    else:
        original_resolved = data_path / file_path
    
    if original_resolved.exists() and original_resolved.is_file():
        return ResolvedFileInfo(
            original_path=file_path,
            resolved_path=original_resolved,
            exists=True,
            location="original",
            error=None,
        )

    # Try encrypted location if hash provided
    if file_hash:
        encrypted_dir = data_path / "encrypted"
        encrypted_file = encrypted_dir / f"{file_hash}.encrypted"
        if encrypted_file.exists() and encrypted_file.is_file():
            return ResolvedFileInfo(
                original_path=file_path,
                resolved_path=encrypted_file,
                exists=True,
                location="encrypted",
                error=None,
            )

    # File not found in either location
    error_msg = f"File not found at expected location: {original_resolved}"
    if file_hash:
        error_msg += f" or encrypted location: {encrypted_dir / f'{file_hash}.encrypted'}"

    return ResolvedFileInfo(
        original_path=file_path,
        resolved_path=None,
        exists=False,
        location=None,
        error=error_msg,
    )

