"""
Tests against a deployed Proxygen instance that don't need an Apigee access token.
"""
import os

import pytest
import requests

pytestmark = pytest.mark.proxygen

TIMEOUT = 30
SERVICE_REQUEST = "FHIR/R4/ServiceRequest"
HEALTHCARE_SERVICE = "FHIR/R4/HealthcareService/12345"


def test_ping_reports_the_deployed_version(proxygen_base_url):
    response = requests.get(f"{proxygen_base_url}/_ping", timeout=TIMEOUT)

    assert response.status_code == 200
    assert {"version", "spec_hash", "proxygen_version"} <= response.json().keys()


@pytest.mark.api_paths
def test_undeclared_path_is_not_found(proxygen_base_url):
    response = requests.get(f"{proxygen_base_url}/_undeclared", timeout=TIMEOUT)

    assert response.status_code == 404


@pytest.mark.api_paths
@pytest.mark.parametrize("path", [SERVICE_REQUEST, HEALTHCARE_SERVICE])
@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer not-a-real-token"}],
    ids=["no-token", "invalid-token"],
)
def test_unauthenticated_requests_are_rejected(proxygen_base_url, path, headers):
    response = requests.get(f"{proxygen_base_url}/{path}", headers=headers, timeout=TIMEOUT)

    # Proxygen writes the body, not our spec, so only the status is ours to assert.
    assert response.status_code == 401


def test_status_is_healthy(proxygen_base_url, proxygen_monitoring_enabled, request):
    api_key = os.environ.get("STATUS_ENDPOINT_API_KEY")
    if not api_key:
        if not os.environ.get("APIGEE_ACCESS_TOKEN"):
            pytest.skip("Needs STATUS_ENDPOINT_API_KEY or APIGEE_ACCESS_TOKEN")
        # In internal-dev the plugin fetches APIM's shared status key via mock-jwks.
        api_key = request.getfixturevalue("status_endpoint_auth_headers")["apikey"]

    response = requests.get(f"{proxygen_base_url}/_status", headers={"apikey": api_key}, timeout=TIMEOUT)

    assert response.status_code == 200
    assert response.json()["status"] == "pass"
