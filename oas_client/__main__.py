import argparse
import json
import os
from pathlib import Path

from oas_client.client import render_client
from oas_client.schemas import render_schemas

BASE_DIR = Path(__file__).parent

import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI client from an OpenAPI JSON spec."
    )
    parser.add_argument("openapi_json", help="Path to the OpenAPI JSON file.")
    parser.add_argument(
        "--output-dir", help="Path to the output directory.", default="client"
    )
    parser.add_argument(
        "--template-dir",
        help="Path to the template directory.",
        default=BASE_DIR / "templates",
    )
    parser.add_argument(
        "--no-formatting",
        help="Disables code formatting (black)",
        action="store_true",
    )
    parser.add_argument(
        "--no-import-sorting",
        help="Disables import sorting (isort)",
        action="store_true",
    )
    args = parser.parse_args()

    openapi_json = Path(args.openapi_json)
    output_dir = Path(args.output_dir)
    template_dir = Path(args.template_dir)

    with open(openapi_json) as f:
        spec = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    (output_dir / "__init__.py").write_text("")
    (output_dir / "schemas.py").write_text(render_schemas(spec, template_dir))
    (output_dir / "client.py").write_text(render_client(spec, template_dir))

    if not args.no_import_sorting:
        try:
            subprocess.run(["isort", str(output_dir)], check=True)
        except FileNotFoundError:
            print("isort not found in path. Skipping...")

    if not args.no_formatting:
        try:
            subprocess.run(["black", str(output_dir)], check=True)
        except FileNotFoundError:
            print("black not found in path. Skipping...")


if __name__ == "__main__":
    main()
