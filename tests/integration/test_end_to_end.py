# flake8: noqa
import pytest
import requests
import base64
import json
from tests.data import RenamedHeader
from tests.data import InternalHeader

_HEADER_AUTHORIZATION = "Authorization"
_HEADER_REQUEST_ID = "x-request-id"
_HEADER_NHSD_TARGET_IDENTIFIER = "nhsd-target-identifier"
_HEADER_NHSD_ERS_TRANSACTION_ID = "nhsd-ers-transaction-id"
_VALID_NHSD_TARGET_IDENTIFIER = {
    "system": "urn:ietf:rfc:3986",
    "value": "2b3b21fd-fe9f-403c-9682-10b8d8a4eaf3"
}

_VALID_NHSD_TARGET_IDENTIFIER_BASE_64 = base64.b64encode(bytes(json.dumps(_VALID_NHSD_TARGET_IDENTIFIER), 'utf-8'))

_EXPECTED_CORRELATION_ID = "123123-123123-123123-123123"
_MATCH_PATIENT_NHS_NUMBER = "9900000285"
_FHIR_R4 = "/FHIR/R4"
_HEALTHCARE_SERVICE_URL = _FHIR_R4 + "/HealthcareService"
_SERVICE_REQUESTS_URL = _FHIR_R4 + "/ServiceRequest"

@pytest.mark.e2e
class TestEndToEnd:
    

    @pytest.mark.parametrize(
        "endpoint_with_params, http_status",
        [(f"{_HEALTHCARE_SERVICE_URL}/1", 404), 
        (f"{_SERVICE_REQUESTS_URL}?patient:identifier={_MATCH_PATIENT_NHS_NUMBER}&category=3457005", 200)]
    )
    def test_headers_on_endpoint_response(
        self, endpoint_with_params, http_status, service_url, patient_access_token
    ):
        client_request_headers = {
            _HEADER_AUTHORIZATION: "Bearer " + patient_access_token,
            _HEADER_REQUEST_ID: "DUMMY-VALUE",
            _HEADER_NHSD_TARGET_IDENTIFIER: _VALID_NHSD_TARGET_IDENTIFIER_BASE_64,
            RenamedHeader.CORRELATION_ID.original: _EXPECTED_CORRELATION_ID
        }

        # Make the API call
        response = requests.get(
            f"{service_url}{endpoint_with_params}", headers=client_request_headers
        )

        # Verify the status
        assert (
            response.status_code == http_status
        ), f"Expected a {http_status} when accesing the api but got {response.status_code}"

        # Verify the received headers
        response_headers = response.headers

        # Verify the headers are in or out
        for renamed_header in RenamedHeader:
            assert renamed_header.original in response_headers
            assert renamed_header.renamed not in response_headers

        for internal_header in InternalHeader:
            assert internal_header.name not in response_headers

        assert _HEADER_REQUEST_ID in response_headers
        assert len(response_headers[_HEADER_REQUEST_ID]) > 15
        assert _HEADER_NHSD_ERS_TRANSACTION_ID not in response_headers

        # Verify the header values
        assert (response_headers[RenamedHeader.CORRELATION_ID.original] 
            == _EXPECTED_CORRELATION_ID
        )

