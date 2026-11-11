"""
Fixtures for testing a deployed Proxygen instance with pytest-nhsd-apim, in any environment.

Settings come from environment variables; the defaults target the long-lived internal-dev
instance, so `make proxygen-test` needs no setup. Tests are skipped, with the reason shown at
the end of the run, when what they need isn't available:

- apigee_token: APIGEE_ACCESS_TOKEN isn't set (see TOKEN_HELP).
- api_paths: the instance was deployed without the API's paths.
- nonprod: PROXYGEN_ENV is prod, which has no mock NHS login or test patients.
- backend: the environment's overlay has no target, so requests can't reach e-RS.
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
    "PROXYGEN_TARGET_IDENTIFIER": "2b3b21fd-fe9f-403c-9682-10b8d8a4eaf3",
}
# Environments where pytest-nhsd-apim can fetch APIM's shared /_status key through mock-jwks.
# Everywhere else STATUS_ENDPOINT_API_KEY must be set.
STATUS_KEY_FETCHABLE_ENVS = {"internal-dev", "internal-dev-sandbox", "internal-qa", "internal-qa-sandbox", "ref"}


def setting(name):
    return os.environ.get(name) or DEFAULTS[name]


def is_true(name):
    return setting(name).lower() == "true"


def overlay_settings(env):
    """The x-nhsd-apim block of the environment's overlay, or {} if it has none."""
    overlay_file = REPO_ROOT / "specification" / "proxygen" / f"{env}.yaml"
    if not overlay_file.exists():
        return {}
    return (yaml.safe_load(overlay_file.read_text()) or {}).get("x-nhsd-apim", {})


def pytest_configure(config):
    # pytest-nhsd-apim only reads these from CLI flags, so map them from the environment here.
    # Explicit flags still win.
    if setting("PROXYGEN_ENV") == "prod" and config.option.APIGEE_ORGANIZATION == "nhsd-nonprod":
        config.option.APIGEE_ORGANIZATION = "nhsd-prod"
    if not config.option.STATUS_ENDPOINT_API_KEY:
        config.option.STATUS_ENDPOINT_API_KEY = os.environ.get("STATUS_ENDPOINT_API_KEY", "")


def pytest_collection_modifyitems(config, items):
    env = setting("PROXYGEN_ENV")
    has_token = bool(os.environ.get("APIGEE_ACCESS_TOKEN"))
    if not has_token and is_true("PROXYGEN_REQUIRE_APIGEE_TOKEN"):
        raise pytest.UsageError(f"APIGEE_ACCESS_TOKEN is not set. {TOKEN_HELP}")

    skips = {
        "apigee_token": (not has_token, f"APIGEE_ACCESS_TOKEN is not set. {TOKEN_HELP}"),
        "api_paths": (
            not is_true("PROXYGEN_INCLUDE_PATHS"),
            "Instance deployed without paths (PROXYGEN_INCLUDE_PATHS=false)",
        ),
        "nonprod": (env == "prod", "Uses mock NHS login and test patients, which prod doesn't have"),
        "backend": (
            not overlay_settings(env).get("target"),
            f"No target in specification/proxygen/{env}.yaml, so requests can't reach e-RS",
        ),
    }
    for item in items:
        for marker, (should_skip, reason) in skips.items():
            if should_skip and marker in item.keywords:
                item.add_marker(pytest.mark.skip(reason=reason))


@pytest.fixture(scope="session")
def proxygen_env():
    return setting("PROXYGEN_ENV")


@pytest.fixture(scope="session")
def proxygen_base_url(proxygen_env):
    host = "api.service.nhs.uk" if proxygen_env == "prod" else f"{proxygen_env}.api.service.nhs.uk"
    return f"https://{host}/{setting('PROXYGEN_BASE_PATH').replace('_', '/')}"


@pytest.fixture(scope="session")
def proxygen_target_identifier():
    """The e-RS application ID that consumers send in NHSD-Target-Identifier."""
    return {"system": "urn:ietf:rfc:3986", "value": setting("PROXYGEN_TARGET_IDENTIFIER")}


@pytest.fixture()
def proxygen_status_api_key(proxygen_env, request):
    # Proxygen only serves /_status when monitoring is on, which defaults to true.
    if not overlay_settings(proxygen_env).get("monitoring", True):
        pytest.skip(f"Monitoring is off in specification/proxygen/{proxygen_env}.yaml, so /_status isn't served")
    if os.environ.get("STATUS_ENDPOINT_API_KEY"):
        return os.environ["STATUS_ENDPOINT_API_KEY"]
    if proxygen_env not in STATUS_KEY_FETCHABLE_ENVS:
        pytest.fail(f"STATUS_ENDPOINT_API_KEY must be set in {proxygen_env}")
    if not os.environ.get("APIGEE_ACCESS_TOKEN"):
        pytest.skip(f"Needs STATUS_ENDPOINT_API_KEY or APIGEE_ACCESS_TOKEN. {TOKEN_HELP}")
    return request.getfixturevalue("status_endpoint_auth_headers")["apikey"]


# Overrides of pytest-nhsd-apim's fixtures, so the suite needs no --api-name or
# --proxy-name flags (the plugin ignores environment variables for those).
@pytest.fixture()
def nhsd_apim_api_name():
    return setting("PROXYGEN_API_NAME")


@pytest.fixture()
def nhsd_apim_proxy_name(proxygen_env):
    # Proxygen names the Apigee proxy it generates <api name>--<env>--<base path>.
    return f"{setting('PROXYGEN_API_NAME')}--{proxygen_env}--{setting('PROXYGEN_BASE_PATH')}"
