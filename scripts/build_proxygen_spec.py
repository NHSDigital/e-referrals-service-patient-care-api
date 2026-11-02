#!/usr/bin/env python3
"""
build_proxygen_spec.py

Turns the OAS produced by `make publish` into a Proxygen instance spec for one environment.

Proxygen's PaasOpenAPI schema needs `openapi: 3.0.3`, a single server and an `x-nhsd-apim`
block. Top-level keys in `specification/proxygen/<ENV>.yaml` replace those in the published
spec. By default `paths` is emptied so only Proxygen's own `/_ping` and `/_status` are
exposed, because no Proxygen access or target is configured yet. When paths are included,
our security schemes are swapped for the Proxygen-managed equivalents.

Usage:
  build_proxygen_spec.py <env> [--base-path=<path>] [--include-paths] [--input=<file>]
                         [--output=<file>] [--schema=<file>]
  build_proxygen_spec.py (-h | --help)

Options:
  --base-path=<path>  Proxygen instance base path [default: e-referrals-service-patient-care-api-proxygen]
  --include-paths     Keep the API's paths instead of deploying with `paths: {}`.
  --input=<file>      Published spec [default: build/e-referrals-service-patient-care-api.json]
  --output=<file>     Instance spec to write (default: build/proxygen/<env>.json)
  --schema=<file>     Proxygen OpenAPI document (openapi.json) to validate against.
"""
import copy
import json
import pathlib
import sys

import yaml
from docopt import docopt

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
OVERLAY_DIR = REPO_ROOT / "specification" / "proxygen"
PROXYGEN_OPENAPI_VERSION = "3.0.3"
PROD_PROXYGEN_ENVS = {"int", "sandbox", "prod"}
# Our scheme name -> Proxygen-managed scheme. bearerAuth carries the NHS login P9 scope.
SECURITY_SCHEME_MAP = {"bearerAuth": "nhs-login-p9"}


def server_url(env, base_path):
    host = "api.service.nhs.uk" if env == "prod" else f"{env}.api.service.nhs.uk"
    # Proxygen uses '_' in base paths to represent '/'.
    return f"https://{host}/{base_path.replace('_', '/')}"


def proxygen_url(env):
    platform = "prod" if env in PROD_PROXYGEN_ENVS else "ptl"
    return f"https://proxygen.{platform}.api.platform.nhs.uk"


def map_security(requirements):
    return [
        {SECURITY_SCHEME_MAP.get(name, name): scopes for name, scopes in req.items()}
        for req in requirements
    ]


def use_proxygen_security(spec, env):
    for path_item in spec.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "security" in operation:
                operation["security"] = map_security(operation["security"])
    if "security" in spec:
        spec["security"] = map_security(spec["security"])

    schemes = spec.get("components", {}).get("securitySchemes", {})
    spec["components"]["securitySchemes"] = {
        SECURITY_SCHEME_MAP.get(name, name): (
            {"$ref": f"{proxygen_url(env)}/components/securitySchemes/{SECURITY_SCHEME_MAP[name]}"}
            if name in SECURITY_SCHEME_MAP
            else scheme
        )
        for name, scheme in schemes.items()
    }


def build(spec, overlay, env, base_path, include_paths):
    spec = copy.deepcopy(spec)
    spec.update(copy.deepcopy(overlay))
    spec["openapi"] = PROXYGEN_OPENAPI_VERSION
    spec["servers"] = [{"url": server_url(env, base_path)}]

    if include_paths:
        if spec.get("components", {}).get("securitySchemes"):
            use_proxygen_security(spec, env)
    else:
        spec["paths"] = {}
        spec.pop("security", None)
        components = spec.get("components", {})
        components.pop("securitySchemes", None)
        if not components:
            spec.pop("components", None)

    return spec


def validate(spec, proxygen_openapi):
    import jsonschema

    schema = {
        "$ref": "#/components/schemas/PaasOpenAPI",
        "components": proxygen_openapi["components"],
    }
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(spec),
        key=lambda e: list(e.absolute_path),
    )
    for error in errors:
        location = "/".join(str(p) for p in error.absolute_path) or "<root>"
        print(f"Proxygen schema error at {location}: {error.message}", file=sys.stderr)
    return not errors


def main(argv=None):
    args = docopt(__doc__, argv=argv)
    env = args["<env>"]
    base_path = args["--base-path"]

    if "/" in base_path:
        sys.exit("Base path must use '_' instead of '/' (Proxygen convention).")

    overlay_file = OVERLAY_DIR / f"{env}.yaml"
    if not overlay_file.exists():
        sys.exit(f"No Proxygen overlay for environment '{env}': {overlay_file}")

    spec = json.loads(pathlib.Path(args["--input"]).read_text())
    overlay = yaml.safe_load(overlay_file.read_text()) or {}

    instance_spec = build(spec, overlay, env, base_path, args["--include-paths"])

    if args["--schema"]:
        proxygen_openapi = json.loads(pathlib.Path(args["--schema"]).read_text())
        if not validate(instance_spec, proxygen_openapi):
            sys.exit("Instance spec does not match Proxygen's PaasOpenAPI schema.")

    output = pathlib.Path(args["--output"] or f"build/proxygen/{env}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(instance_spec, indent=2))
    print(f"Wrote {output} ({'with' if args['--include-paths'] else 'without'} paths)")


if __name__ == "__main__":
    main()
