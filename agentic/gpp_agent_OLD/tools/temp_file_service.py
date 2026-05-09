import os
import uuid
import tempfile
import logging

logger = logging.getLogger(__name__)

TEMP_DIR = os.path.join(tempfile.gettempdir(), "gpp_agent_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

def save_temp_file(filename: str, content: str | bytes) -> str:
    """
    Speichert den Dateiinhalt temporär ab.
    Der tatsächliche Dateiname wird mit einer UUID versehen, um Kollisionen zu vermeiden.
    Gibt den absoluten Dateipfad zurück.
    """
    safe_id = str(uuid.uuid4())
    safe_filename = f"{safe_id}_{os.path.basename(filename)}"
    filepath = os.path.join(TEMP_DIR, safe_filename)

    mode = "wb" if isinstance(content, bytes) else "w"

    try:
        with open(filepath, mode) as f:
            f.write(content)
        return filepath
    except Exception as e:
        logger.error(f"Fehler beim Speichern der temporären Datei {filepath}: {e}")
        raise

def read_temp_file(filepath: str) -> str:
    """
    Liest den Inhalt einer temporären Datei, falls diese im temp-Verzeichnis liegt.
    """
    abs_filepath = os.path.abspath(filepath)
    abs_temp_dir = os.path.abspath(TEMP_DIR)

    if os.path.commonpath([abs_temp_dir, abs_filepath]) != abs_temp_dir:
        raise ValueError("Security Error: Path traversal attempt or invalid directory.")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Die Datei {filepath} wurde nicht gefunden.")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Fehler beim Lesen der temporären Datei {filepath}: {e}")
        raise

def delete_temp_file(filepath: str) -> bool:
    """
    Löscht eine temporäre Datei, um Speicherplatz freizugeben.
    """
    abs_filepath = os.path.abspath(filepath)
    abs_temp_dir = os.path.abspath(TEMP_DIR)

    if os.path.commonpath([abs_temp_dir, abs_filepath]) != abs_temp_dir:
        raise ValueError("Security Error: Path traversal attempt or invalid directory.")

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Datei {filepath}: {e}")
            return False
    return False
