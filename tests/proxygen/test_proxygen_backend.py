"""
End-to-end smoke tests through Proxygen and the adapter to the e-RS backend.

They need a token, test patients from APIM's mock NHS login (so not prod), and a target in
the environment's overlay. Until the adapter is deployed as the target, they're skipped.
Expected errors follow the adapter design's error catalogue (PROXYGEN_ADAPTER_DESIGN.md).
A forced backend failure isn't tested here: it can't be triggered in a shared environment, so
it's covered by the adapter's contract tests against a backend stub.
"""
import base64
import json

import pytest
import requests

from tests.proxygen.test_proxygen_smoke import TIMEOUT

pytestmark = [
    pytest.mark.proxygen,
    pytest.mark.apigee_token,
    pytest.mark.api_paths,
    pytest.mark.nonprod,
    pytest.mark.backend,
]

P9_NHS_NUMBER = "9900000285"
# In APIM's mock NHS login this patient authenticates with the P9.Cp vector of trust, which the
# API doesn't accept.
UNSUPPORTED_VOT_NHS_NUMBER = "5900068196"
CORRELATION_ID = "proxygen-smoke-0000-0000-000000000000"
SERVICE_REQUEST_SEARCH = f"FHIR/R4/ServiceRequest?patient:identifier={P9_NHS_NUMBER}&category=3457005"
P9_PATIENT = pytest.mark.nhsd_apim_authorization(
    access="patient", level="P9", login_form={"username": P9_NHS_NUMBER}
)


def encode_target_identifier(identifier):
    return base64.b64encode(json.dumps(identifier).encode()).decode()


@pytest.fixture()
def request_headers(nhsd_apim_auth_headers, proxygen_target_identifier):
    return {
        **nhsd_apim_auth_headers,
        "NHSD-Target-Identifier": encode_target_identifier(proxygen_target_identifier),
        "X-Correlation-ID": CORRELATION_ID,
    }


def get(base_url, path, headers):
    return requests.get(f"{base_url}/{path}", headers=headers, timeout=TIMEOUT)


def assert_fhir_error(response, status, code, coding, diagnostics=None, expression=None):
    assert response.status_code == status, response.text
    body = response.json()
    assert body["resourceType"] == "OperationOutcome"
    [issue] = body["issue"]
    assert issue["severity"] == "error"
    assert issue["code"] == code
    assert issue["details"]["coding"][0]["code"] == coding
    if diagnostics is not None:
        assert issue["diagnostics"] == diagnostics
    if expression is not None:
        assert issue["expression"] == expression


def assert_response_headers(response):
    assert response.headers["X-Correlation-ID"] == CORRELATION_ID
    assert response.headers.get("X-Request-ID")
    # The backend's internal headers, including nhsd-correlation-id, must not reach consumers.
    assert not [name for name in response.headers if name.lower().startswith("nhsd-")]


@P9_PATIENT
def test_service_request_search_returns_the_patients_referrals(proxygen_base_url, request_headers):
    response = get(proxygen_base_url, SERVICE_REQUEST_SEARCH, request_headers)

    assert response.status_code == 200, response.text
    assert response.json()["resourceType"] == "Bundle"
    assert_response_headers(response)


@P9_PATIENT
def test_unknown_healthcare_service_is_not_found(proxygen_base_url, request_headers):
    response = get(proxygen_base_url, "FHIR/R4/HealthcareService/1", request_headers)

    assert response.status_code == 404, response.text
    assert_response_headers(response)


@pytest.mark.nhsd_apim_authorization(
    access="patient", level="P9", login_form={"username": UNSUPPORTED_VOT_NHS_NUMBER}
)
def test_unsupported_vector_of_trust_is_rejected(proxygen_base_url, request_headers):
    response = get(proxygen_base_url, SERVICE_REQUEST_SEARCH, request_headers)

    assert_fhir_error(
        response,
        401,
        "login",
        "ACCESS_DENIED",
        diagnostics="Unsupported Vector of Trust value utilised for authentication.",
    )


@P9_PATIENT
@pytest.mark.parametrize(
    "target_identifier",
    [
        None,
        "",
        "not-base64-json",
        encode_target_identifier({"value": "2b3b21fd-fe9f-403c-9682-10b8d8a4eaf3"}),
        encode_target_identifier({"system": "urn:ietf:rfc:3986"}),
        encode_target_identifier({"system": "urn:ietf:rfc:3986", "value": "00000000-0000-0000-0000-000000000000"}),
    ],
    ids=["missing", "empty", "not-encoded", "no-system", "no-value", "unknown-application"],
)
def test_invalid_target_identifier_is_rejected(proxygen_base_url, request_headers, target_identifier):
    if target_identifier is None:
        del request_headers["NHSD-Target-Identifier"]
    else:
        request_headers["NHSD-Target-Identifier"] = target_identifier

    response = get(proxygen_base_url, SERVICE_REQUEST_SEARCH, request_headers)

    assert_fhir_error(
        response,
        404,
        "not-found",
        "VALIDATION_ERROR",
        diagnostics="Unknown value",
        expression='http."NHSD-Target-Identifier"',
    )


@P9_PATIENT
def test_spoofed_internal_headers_are_ignored(proxygen_base_url, request_headers):
    expected = get(proxygen_base_url, SERVICE_REQUEST_SEARCH, request_headers)

    # A consumer trying to act as another patient, or to set the backend's internal headers.
    spoofed = {
        **request_headers,
        "nhsd-nhs-number": "9912003072",
        "nhsd-application-id": "spoofed",
        "nhsd-access-token": "spoofed",
        "nhsd-ers-network-baseurl": "https://example.com",
        "nhsd-correlation-id": "spoofed",
        "NHSD-NHSlogin-NHS-Number": "9912003072",
    }
    response = get(proxygen_base_url, SERVICE_REQUEST_SEARCH, spoofed)

    # The adapter builds the backend request from verified values only, so the result is the
    # same as without the spoofed headers.
    assert response.status_code == expected.status_code == 200, response.text
    assert response.json().get("total") == expected.json().get("total")
    assert_response_headers(response)
