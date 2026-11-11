"""
Fixtures for testing a deployed Proxygen instance with pytest-nhsd-apim.

Settings come from environment variables; the defaults target the long-lived internal-dev
instance. See tests/proxygen/README.md.
"""
import os
import pathlib

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOKEN_HELP = (
    "export APIGEE_ACCESS_TOKEN=$(proxygen pytest-nhsd-apim get-token | jq -r .pytest_nhsd_apim_token)"
)
DEFAULTS = {
    "PROXYGEN_ENV": "internal-dev",
    "PROXYGEN_API_NAME": "e-referrals-service-patient-care-api-proxygen",
    # Proxygen uses '_' in base paths to represent '/'.
    "PROXYGEN_BASE_PATH": "e-referrals-service-patient-care-api-proxygen",
    "PROXYGEN_INCLUDE_PATHS": "true",
    "PROXYGEN_REQUIRE_APIGEE_TOKEN": "false",
}


def setting(name):
    return os.environ.get(name) or DEFAULTS[name]


def is_true(name):
    return setting(name).lower() == "true"


def pytest_collection_modifyitems(config, items):
    has_token = bool(os.environ.get("APIGEE_ACCESS_TOKEN"))
    if not has_token and is_true("PROXYGEN_REQUIRE_APIGEE_TOKEN"):
        raise pytest.UsageError(f"APIGEE_ACCESS_TOKEN is not set. {TOKEN_HELP}")

    skip_token = pytest.mark.skip(reason=f"APIGEE_ACCESS_TOKEN is not set. {TOKEN_HELP}")
    skip_paths = pytest.mark.skip(reason="Instance deployed without paths (PROXYGEN_INCLUDE_PATHS=false)")
    for item in items:
        if "apigee_token" in item.keywords and not has_token:
            item.add_marker(skip_token)
        if "api_paths" in item.keywords and not is_true("PROXYGEN_INCLUDE_PATHS"):
            item.add_marker(skip_paths)


@pytest.fixture(scope="session")
def proxygen_env():
    return setting("PROXYGEN_ENV")


@pytest.fixture(scope="session")
def proxygen_base_url(proxygen_env):
    host = "api.service.nhs.uk" if proxygen_env == "prod" else f"{proxygen_env}.api.service.nhs.uk"
    return f"https://{host}/{setting('PROXYGEN_BASE_PATH').replace('_', '/')}"


@pytest.fixture(scope="session")
def proxygen_monitoring_enabled(proxygen_env):
    overlay_file = REPO_ROOT / "specification" / "proxygen" / f"{proxygen_env}.yaml"
    overlay = yaml.safe_load(overlay_file.read_text()) if overlay_file.exists() else {}
    # Proxygen only serves /_status when monitoring is on, which defaults to true.
    if not (overlay or {}).get("x-nhsd-apim", {}).get("monitoring", True):
        pytest.skip(f"Monitoring is off in {overlay_file.name}, so /_status isn't served")


# Overrides of pytest-nhsd-apim's fixtures, so the suite needs no --api-name or
# --proxy-name flags (the plugin ignores environment variables for those).
@pytest.fixture()
def nhsd_apim_api_name():
    return setting("PROXYGEN_API_NAME")


@pytest.fixture()
def nhsd_apim_proxy_name(proxygen_env):
    # Proxygen names the Apigee proxy it generates <api name>--<env>--<base path>.
    return f"{setting('PROXYGEN_API_NAME')}--{proxygen_env}--{setting('PROXYGEN_BASE_PATH')}"
