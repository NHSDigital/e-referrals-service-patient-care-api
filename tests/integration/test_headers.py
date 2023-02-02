# flake8: noqa
import pytest
import requests
import base64
import json
from tests.data import RenamedHeader
from tests.data import InternalHeader

_HEADER_AUTHORIZATION = "Authorization"
_HEADER_ECHO = "echo"  # enable echo target
_HEADER_REQUEST_ID = "x-request-id"
_HEADER_NHSD_TARGET_IDENTIFIER = "nhsd-target-identifier"
_VALID_NHSD_TARGET_IDENTIFIER = {
    "system": "urn:ietf:rfc:3986",
    "value": "2b3b21fd-fe9f-403c-9682-10b8d8a4eaf3"
}
_INVALID_SYSTEM_NHSD_TARGET_IDENTIFIER = {
    "value": "2b3b21fd-fe9f-403c-9682-10b8d8a4eaf3"
}
_INVALID_VALUE_NHSD_TARGET_IDENTIFIER = {
    "system": "urn:ietf:rfc:3986"
}

_VALID_NHSD_TARGET_IDENTIFIER_BASE_64 = base64.b64encode(bytes(json.dumps(_VALID_NHSD_TARGET_IDENTIFIER), 'utf-8'))

_EXPECTED_CORRELATION_ID = "123123-123123-123123-123123"
_MATCH_PATIENT_NHS_NUMBER = "9912003888"
_DUMMY_VALUE = "DUMMY"

@pytest.mark.contract_test
class TestHeaders:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("send_apim_headers", [True, False ])
    async def test_headers_on_echo_target(
        self, patient_care_app, service_url, patient_access_token, send_apim_headers
    ):
        """
        Happy path to exercise the policies on the Request part of the flow using the echo target.
        There are some headers that are controlled by APIM policies (i.e. they delete and set the header value, such us nhsd-nhs-number),
        so in order to exercise this the parameter send_apim_headers is used:
            * False: the client does not send the headers (which is the normal scenario)
            * True: the client sends the headers

        """
        client_request_headers = {
            _HEADER_ECHO: "",  # enable echo target
            _HEADER_AUTHORIZATION: "Bearer " + patient_access_token,
            _HEADER_REQUEST_ID: "Request-1234",
            _HEADER_NHSD_TARGET_IDENTIFIER: _VALID_NHSD_TARGET_IDENTIFIER_BASE_64,
            RenamedHeader.CORRELATION_ID.original: _EXPECTED_CORRELATION_ID
        }

        if send_apim_headers:
            client_request_headers[InternalHeader.NHS_NUMBER.name] = _DUMMY_VALUE
            client_request_headers[InternalHeader.BASE_URL.name] = _DUMMY_VALUE
            client_request_headers[InternalHeader.APPLICATION_ID.name] = _DUMMY_VALUE
            client_request_headers[InternalHeader.ACCESS_TOKEN.name] = _DUMMY_VALUE
            client_request_headers[RenamedHeader.CORRELATION_ID.renamed] = _DUMMY_VALUE

        # Make the API call
        response = requests.get(service_url, headers=client_request_headers)
        assert (
            response.status_code == 200
        ), "Expected a 200 when accesing the api but got " + (str)(response.status_code)

        # Verify the response headers
        client_response_headers = response.headers
        assert _HEADER_REQUEST_ID not in client_response_headers
        assert (
            client_response_headers[RenamedHeader.CORRELATION_ID.original]
            == _EXPECTED_CORRELATION_ID
        )

        for renamed_header in RenamedHeader:
            assert renamed_header.renamed not in client_response_headers

        # Verify the received headers by the target
        json_response = response.json()
        target_request_headers = json_response["headers"]

        # Verify the headers are in or out
        for renamed_header in RenamedHeader:
            assert renamed_header.original not in target_request_headers
            assert renamed_header.renamed in target_request_headers

        assert _HEADER_REQUEST_ID not in target_request_headers

        # Verify the header values
        assert target_request_headers[RenamedHeader.CORRELATION_ID.renamed].startswith(
            _EXPECTED_CORRELATION_ID
        )

        assert target_request_headers[InternalHeader.NHS_NUMBER.name] == _MATCH_PATIENT_NHS_NUMBER
        assert target_request_headers[InternalHeader.BASE_URL.name] == service_url
        assert target_request_headers[InternalHeader.ACCESS_TOKEN.name] == patient_access_token

        app_details = await patient_care_app.get_app_details()
        assert target_request_headers[InternalHeader.APPLICATION_ID.name] == app_details["appId"]


    @pytest.mark.parametrize(
        "auth_header",
        [("Bearer 99999999999999999999999999999999"), (None), (""), ("Bearer ")],
    )
    def test_unknown_access_code(self, service_url, auth_header):
        client_request_headers = {
            _HEADER_ECHO: "",  # enable echo target
            _HEADER_REQUEST_ID: "DUMMY",
            _HEADER_NHSD_TARGET_IDENTIFIER: _VALID_NHSD_TARGET_IDENTIFIER_BASE_64,
            RenamedHeader.CORRELATION_ID.original: _EXPECTED_CORRELATION_ID
        }

        if auth_header is not None:
            client_request_headers[_HEADER_AUTHORIZATION] = auth_header

        response = requests.get(service_url, headers=client_request_headers)

        # Verify the status
        assert (
            response.status_code == 401
        ), "Expected a 401 when accesing the api but got " + (str)(response.status_code)

        response_data = response.json()
        assert (response_data['resourceType'] == 'OperationOutcome')
        assert (response_data['meta']['lastUpdated'] is not None)
        assert (response_data['meta']['profile'][0] == 'https://fhir.nhs.uk/StructureDefinition/NHSDigital-OperationOutcome')
        assert (len(response_data['issue']) == 1)
        issue = response_data['issue'][0]
        assert (issue['severity'] == 'error')
        assert (issue['code'] == 'forbidden')
        assert (issue['diagnostics'].lower() == 'invalid access token')
        assert (len(issue['details']['coding']) == 1)
        issue_details = issue['details']['coding'][0]
        assert (issue_details['system'] == 'https://fhir.nhs.uk/CodeSystem/NHSD-API-ErrorOrWarningCode')
        assert (issue_details['code'] == 'ACCESS_DENIED')


    @pytest.mark.parametrize(
        "target_identifier",
        [(base64.b64encode(bytes(json.dumps(_INVALID_SYSTEM_NHSD_TARGET_IDENTIFIER), 'utf-8'))),
        (base64.b64encode(bytes(json.dumps(_INVALID_VALUE_NHSD_TARGET_IDENTIFIER), 'utf-8'))),
        (None), (""), ("AA")],
    )
    def test_invalid_target_application(self, service_url, patient_access_token, target_identifier):
        client_request_headers = {
            _HEADER_ECHO: "",  # enable echo target
            _HEADER_REQUEST_ID: "DUMMY",
            _HEADER_AUTHORIZATION: "Bearer " + patient_access_token,
            RenamedHeader.CORRELATION_ID.original: _EXPECTED_CORRELATION_ID
        }

        if target_identifier is not None:
            client_request_headers[_HEADER_NHSD_TARGET_IDENTIFIER] = target_identifier

        response = requests.get(service_url, headers=client_request_headers)

        # Verify the status
        assert (
            response.status_code == 404
        ), "Expected a 404 when accesing the api but got " + (str)(response.status_code)

        response_data = response.json()
        assert (response_data['resourceType'] == 'OperationOutcome')
        assert (response_data['meta']['lastUpdated'] is not None)
        assert (response_data['meta']['profile'][0] == 'https://fhir.nhs.uk/StructureDefinition/NHSDigital-OperationOutcome')
        assert (len(response_data['issue']) == 1)
        issue = response_data['issue'][0]
        assert (issue['severity'] == 'error')
        assert (issue['code'] == 'not-found')
        assert (issue['diagnostics'] == 'Unknown value')
        assert (issue['expression'] == 'http.\"NHSD-Target-Identifier\"')
        assert (len(issue['details']['coding']) == 1)
        issue_details = issue['details']['coding'][0]
        assert (issue_details['system'] == 'https://fhir.nhs.uk/CodeSystem/NHSD-API-ErrorOrWarningCode')
        assert (issue_details['code'] == 'VALIDATION_ERROR')


