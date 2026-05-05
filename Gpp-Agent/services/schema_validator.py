import json
import jsonschema
from pathlib import Path

class SchemaValidator:
    def __init__(self, schemas_dir: str | Path):
        self.schemas_dir = Path(schemas_dir)

    def validate_oscal(self, data: dict, schema_name: str):
        schema_path = self.schemas_dir / f"{schema_name}.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema {schema_name} not found in {self.schemas_dir}")

        with open(schema_path, "r") as f:
            schema = json.load(f)

        jsonschema.validate(instance=data, schema=schema)
        return True
