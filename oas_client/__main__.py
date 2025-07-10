import argparse
import json
import os
import re
import subprocess
from pathlib import Path

import httpx

from oas_client.renderers.client import render_client
from oas_client.renderers.params import render_params
from oas_client.renderers.queries import render_queries
from oas_client.renderers.requests import render_requests
from oas_client.renderers.responses import render_responses

BASE_DIR = Path(__file__).parent


def is_url(path: str) -> bool:
    return re.match(r"^https?://", path) is not None


def main():
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI client from an OpenAPI JSON spec."
    )
    parser.add_argument("openapi_json", help="Path or URL to the OpenAPI JSON file.")
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
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    template_dir = Path(args.template_dir)

    if is_url(args.openapi_json):
        res = httpx.get(args.openapi_json, timeout=30)
        res.raise_for_status()
        spec = res.json()
    else:
        openapi_json = Path(args.openapi_json)
        with open(openapi_json) as f:
            spec = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    responses = render_responses(spec, template_dir)
    requests = render_requests(spec, template_dir)
    queries = render_queries(spec, template_dir)
    params = render_params(spec, template_dir)
    client = render_client(spec, template_dir)

    (output_dir / "__init__.py").write_text("")
    (output_dir / "responses.py").write_text(responses)
    (output_dir / "requests.py").write_text(requests)
    (output_dir / "queries.py").write_text(queries)
    (output_dir / "params.py").write_text(params)
    (output_dir / "client.py").write_text(client)

    if not args.no_formatting:
        try:
            # linting
            subprocess.run(["ruff", "check", "--fix", "--quiet", output_dir])
            # formatting
            subprocess.run(["ruff", "format", "--quiet", output_dir])
        except FileNotFoundError:
            print("ruff not found in path. Skipping...")


if __name__ == "__main__":
    main()
