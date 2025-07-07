import argparse
import json
import os
from pathlib import Path

from oas_client.schemas import render_schemas


def main():
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI client from an OpenAPI JSON spec."
    )
    parser.add_argument("openapi_json", help="Path to the OpenAPI JSON file.")
    parser.add_argument("output_dir", help="Path to the output directory.")
    args = parser.parse_args()

    openapi_json = Path(args.openapi_json)
    output_dir = Path(args.output_dir)

    with open(openapi_json) as f:
        spec = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    (output_dir / "__init__.py").write_text("")
    (output_dir / "schemas.py").write_text(render_schemas(spec))


if __name__ == "__main__":
    main()
