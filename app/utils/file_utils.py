"""Utility functions for file operations such as removing files."""

import os
from pathlib import Path
from typing import BinaryIO

import aiofiles

from app.core.logging import logger


def create_dir(path: os.PathLike):
    """Create a directory for the given path if it does not exist.

    Parameters
    ----------
    path : os.PathLike
        The path for which to create the directory.

    Returns.
    -------
    bool
        True if the directory was created or already exists.
    """
    path = _covert_to_path(path).absolute()
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error("failed_to_create_folder", folder=path, error=str(e), exc_info=True)
        raise e


async def save_file_by_chunks(file_path: os.PathLike, file: BinaryIO, chunk_size: int = 515 * 512):
    """Save a file in chunks asynchronously to the specified file path.

    Parameters
    ----------
    file_path : os.PathLike
        The path where the file will be saved.
    file : BinaryIO
        The file-like object to read data from.
    chunk_size : int, optional
        The size of each chunk to read and write (default is 515 * 512).

    Returns.
    -------
    bool
        True if the file was saved successfully.
    """
    file_path = _covert_to_path(file_path)
    create_dir(file_path.parent)

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(chunk_size):
                await f.write(chunk)
        return True
    except Exception as e:
        logger.error("failed_to_save_file", file=file_path, error=str(e), exc_info=True)
        raise e


def remove_file(file_path: os.PathLike) -> bool:
    """Delete a file by it's path."""
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        logger.error("failed_to_delete_file", file=file_path, error=str(e), exc_info=True)
        raise e
    

def _covert_to_path(p: os.PathLike) -> Path:
    if not isinstance(p, Path):
        p = Path(p)
    return p
