import json
import logging
import os
from typing import Any, Dict, Optional
from google.cloud import storage
from enum import Enum

logger = logging.getLogger("GppContextMCP.storage")

BUCKET_NAME = os.getenv("BUCKET_NAME")
if not BUCKET_NAME:
    logger.warning("BUCKET_NAME environment variable not set. GCP Storage operations will fail.")

_client = None

def get_storage_client():
    global _client
    if _client is None:
        _client = storage.Client()
    return _client

class OscalModel(str, Enum):
    ASSESSMENT_PLAN = "assessment-plan"
    ASSESSMENT_RESULTS = "assessment-results"
    CATALOG = "catalog"
    COMPONENT = "component"
    MAPPING = "mapping"
    POAM = "poam"
    PROFILE = "profile"
    SSP = "ssp"

def _get_path(iv_id: str, model: OscalModel, version: Optional[str] = None) -> str:
    """Returns the GCS path for a given model and tenant (IV)."""
    if version:
        return f"ivs/{iv_id}/{model.value}/{version}.json"
    return f"ivs/{iv_id}/{model.value}/latest.json"

def read_oscal_model(iv_id: str, model: OscalModel, version: Optional[str] = None) -> Dict[str, Any]:
    """Reads an OSCAL model from GCP Storage."""
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    path = _get_path(iv_id, model, version)
    blob = bucket.blob(path)

    if not blob.exists():
        # If latest doesn't exist, try to find any version or return error
        raise FileNotFoundError(f"Model {model.value} not found for IV {iv_id} at {path}")

    content = blob.download_as_text()
    return json.loads(content)

def write_oscal_model(iv_id: str, model: OscalModel, data: Dict[str, Any]) -> str:
    """
    Writes an OSCAL model to GCP Storage.
    Implements versioned snapshots.
    """
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)

    # 1. Determine next version number
    prefix = f"ivs/{iv_id}/{model.value}/save_v"
    blobs = list(client.list_blobs(BUCKET_NAME, prefix=prefix))

    next_version_num = 1
    if blobs:
        # Extract version numbers and find max
        versions = []
        for b in blobs:
            try:
                # Expecting path like ivs/iv-123/ssp/save_v1.json
                v_part = b.name.split("/")[-1].replace("save_v", "").replace(".json", "")
                versions.append(int(v_part))
            except ValueError:
                continue
        if versions:
            next_version_num = max(versions) + 1

    version_name = f"save_v{next_version_num}"
    path = _get_path(iv_id, model, version_name)
    latest_path = _get_path(iv_id, model)

    # 2. Write snapshot
    blob = bucket.blob(path)
    content = json.dumps(data, indent=2)
    blob.upload_from_string(content, content_type="application/json")

    # 3. Update latest pointer (by copying or overwriting)
    latest_blob = bucket.blob(latest_path)
    latest_blob.upload_from_string(content, content_type="application/json")

    logger.info(f"Committed {model.value} for {iv_id} as {version_name}")
    return version_name

def list_snapshots(iv_id: str, model: OscalModel) -> list[str]:
    """Lists all available snapshot versions for a model."""
    client = get_storage_client()
    prefix = f"ivs/{iv_id}/{model.value}/save_v"
    blobs = client.list_blobs(BUCKET_NAME, prefix=prefix)
    return [b.name.split("/")[-1].replace(".json", "") for b in blobs]

def list_models(iv_id: str) -> list[str]:
    """Lists all initialized OSCAL models for a tenant (IV)."""
    client = get_storage_client()
    prefix = f"ivs/{iv_id}/"
    iterator = client.list_blobs(BUCKET_NAME, prefix=prefix, delimiter='/')
    # Consume iterator to populate prefixes
    list(iterator)

    models = []
    for p in iterator.prefixes:
        # p is like 'ivs/iv-123/ssp/'
        model_name = p.rstrip('/').split('/')[-1]
        try:
            OscalModel(model_name)
            models.append(model_name)
        except ValueError:
            # Not a valid OscalModel directory
            continue
    return models
