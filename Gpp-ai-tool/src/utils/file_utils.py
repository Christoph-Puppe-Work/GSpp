"""
File Utilities

This module provides utility functions for file and directory operations,
such as creating directories and reading/writing JSON and CSV files.
"""

import os
import io
import json
import csv
import time
import hashlib
import logging
import urllib.request

logger = logging.getLogger(__name__)

# Network behaviour for remote (GitHub-hosted) source downloads. Without an explicit
# timeout, urlopen can block the entire pipeline indefinitely if the upstream host hangs.
URL_FETCH_TIMEOUT_SECONDS = float(os.environ.get("URL_FETCH_TIMEOUT_SECONDS", "30"))
URL_FETCH_RETRIES = int(os.environ.get("URL_FETCH_RETRIES", "3"))
URL_FETCH_BACKOFF_SECONDS = float(os.environ.get("URL_FETCH_BACKOFF_SECONDS", "2"))


def is_url(path):
    """Returns True if the given path is an HTTP(S) URL."""
    return isinstance(path, str) and path.startswith(("http://", "https://"))


def read_source_bytes(path):
    """
    Reads raw bytes from either a local file path or an HTTP(S) URL.

    URL downloads use an explicit timeout and a short retry-with-backoff so a slow or
    flaky upstream host cannot block the pipeline indefinitely.

    Args:
        path (str): A local filesystem path or an http(s) URL.

    Returns:
        bytes: The raw content of the source.

    Raises:
        Propagates the last urllib/OS error for URLs (after exhausting retries) and
        OSError for local files so callers can decide how to handle missing/unreachable
        sources.
    """
    if is_url(path):
        logger.debug(f"Downloading source from URL: {path}")
        last_error = None
        for attempt in range(1, URL_FETCH_RETRIES + 1):
            try:
                with urllib.request.urlopen(path, timeout=URL_FETCH_TIMEOUT_SECONDS) as response:
                    return response.read()
            except Exception as e:  # noqa: BLE001 - retry on any transient network failure
                last_error = e
                logger.warning(
                    f"Download attempt {attempt}/{URL_FETCH_RETRIES} failed for {path}: {e}"
                )
                if attempt < URL_FETCH_RETRIES:
                    time.sleep(URL_FETCH_BACKOFF_SECONDS * attempt)
        logger.error(f"All {URL_FETCH_RETRIES} download attempts failed for {path}")
        raise last_error
    with open(path, "rb") as f:
        return f.read()


def read_source_text(path):
    """Reads text content (UTF-8) from a local file path or an HTTP(S) URL."""
    return read_source_bytes(path).decode("utf-8")


def sha256_matches(data: bytes, expected_sha256: str, source: str) -> bool:
    """Checks raw content against a pinned SHA-256 (Grundregel 8 supply-chain gate).

    Logs an error with both digests on mismatch so a failed pin check is diagnosable
    from the pipeline log alone.
    """
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_sha256:
        logger.error(
            f"SHA-256 mismatch for {source}: expected {expected_sha256}, got {actual}. "
            "The pinned source has changed — refusing to use it."
        )
        return False
    return True


def create_dir_if_not_exists(directory_path):
    """
    Creates a directory if it does not already exist.

    Args:
        directory_path (str): The path to the directory.
    """
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            logger.info(f"Directory created: {directory_path}")
        except OSError as e:
            logger.error(f"Error creating directory {directory_path}: {e}")

def read_text_file(file_path):
    """
    Reads a text file and returns its content.

    Args:
        file_path (str): The path to the text file.

    Returns:
        str: The content of the file, or None if an error occurs.
    """
    try:
        return read_source_text(file_path)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
        return None

def read_json_file(file_path, expected_sha256=None):
    """
    Reads a JSON file and returns its content.

    Args:
        file_path (str): The path to the JSON file.
        expected_sha256 (str): Optional pinned SHA-256 of the raw content. On mismatch
            the content is discarded and None is returned, so callers treat a failed
            pin check exactly like an unloadable source.

    Returns:
        dict: The content of the JSON file, or None if an error occurs.
    """
    try:
        data = read_source_bytes(file_path)
        if expected_sha256 and not sha256_matches(data, expected_sha256, file_path):
            return None
        return json.loads(data)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading JSON source {file_path}: {e}")
        return None

def json_mapping_is_populated(file_path, key):
    """Return True only if `file_path` exists and holds a non-empty `data[key]`.

    Pipeline idempotency guards use this so an empty or corrupt output file (e.g. one left
    behind by a manual "clear") is regenerated instead of being treated as already complete.
    A simply-missing file returns False quietly (no error log).
    """
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    return bool(isinstance(data, dict) and data.get(key))

def write_json_file(file_path, data):
    """
    Writes data to a JSON file.

    Args:
        file_path (str): The path to the JSON file.
        data (dict): The data to write to the file.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            # Trailing newline keeps pipeline output byte-identical with files
            # normalized by scripts/pin_profile_imports.py.
            f.write("\n")
        logger.debug(f"Successfully wrote to {file_path}")
    except IOError as e:
        logger.error(f"Error writing to file {file_path}: {e}")

def read_csv_file(file_path):
    """
    Reads a CSV file and returns its content as a list of dictionaries.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        list: A list of dictionaries representing the rows of the CSV file,
              or None if an error occurs.
    """
    try:
        return list(csv.DictReader(io.StringIO(read_source_text(file_path))))
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {e}")
        return None
