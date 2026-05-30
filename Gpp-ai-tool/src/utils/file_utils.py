"""
File Utilities

This module provides utility functions for file and directory operations,
such as creating directories and reading/writing JSON and CSV files.
"""

import os
import io
import json
import csv
import logging
import urllib.request

logger = logging.getLogger(__name__)


def is_url(path):
    """Returns True if the given path is an HTTP(S) URL."""
    return isinstance(path, str) and path.startswith(("http://", "https://"))


def read_source_text(path):
    """
    Reads text content from either a local file path or an HTTP(S) URL.

    Args:
        path (str): A local filesystem path or an http(s) URL.

    Returns:
        str: The decoded UTF-8 content of the source.

    Raises:
        Propagates urllib errors for URLs and OSError for local files so
        callers can decide how to handle missing/unreachable sources.
    """
    if is_url(path):
        logger.debug(f"Downloading source from URL: {path}")
        with urllib.request.urlopen(path) as response:
            return response.read().decode("utf-8")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


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

def read_json_file(file_path):
    """
    Reads a JSON file and returns its content.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The content of the JSON file, or None if an error occurs.
    """
    try:
        return json.loads(read_source_text(file_path))
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading JSON source {file_path}: {e}")
        return None

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
