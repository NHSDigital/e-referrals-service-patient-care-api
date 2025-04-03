from typing import Callable, Collection, Generator
import pytest
import requests

from tests.data import RenamedHeader
from tests.utils import PatientAuthenticator, generate_valid_target_identifier


class TestUserAuthentication:

    # These users are housed within the API-M dataset
    @pytest.mark.parametrize(
            "nhs_number",
            [
                "9912003072",  # P5 Patient
                "9912003073"   # P0 Patient
            ])
    @pytest.mark.asyncio
    async def test_unsupported_identity_proofing(
        self,
        service_url: str,
        patient_authenticator: PatientAuthenticator,
        nhs_number: str,
        update_product: Callable[[Collection[str]], Generator[dict[str, str], None, None]]
    ):
        # As our product does not allow for anything lower than P9 in its scopes by default, we need to add support for P5 and P0 temporarily to be able
        # to test this level of authentication.
        with update_product(append_scopes=[
            "urn:nhsd:apim:user-nhs-login:P5:e-referrals-service-patient-care-api",
            "urn:nhsd:apim:user-nhs-login:P0:e-referrals-service-patient-care-api"
        ]):
            access_code = patient_authenticator.auth(nhs_number)

            request_headers = {
                "echo": "",  # enable echo header
                "nhsd-target-identifier": generate_valid_target_identifier(),
                "Authorization": "Bearer " + access_code,
                RenamedHeader.CORRELATION_ID.original: "test_insupported_identity_proofing",
            }

            response = requests.get(service_url, headers=request_headers)
            assert (
                response.status_code == 401
            ), "Expected 401 when accessing the API but instead received " + str(response.status_code)

            response_data = response.json()

            assert response_data["resourceType"] == "OperationOutcome"
            assert len(response_data["issue"]) == 1

            issue = response_data["issue"][0]

            assert issue["severity"] == "error"
            assert issue["code"] == "forbidden"
            assert len(issue["details"]) == 1
            assert len(issue["details"]["coding"]) == 1

            issue_coding = issue["details"]["coding"][0]

            assert issue_coding["system"] == "https://fhir.nhs.uk/CodeSystem/NHSD-API-ErrorOrWarningCode"
            assert issue_coding["code"] == "ACCESS_DENIED"

    @pytest.mark.asyncio
    async def test_unsupported_vector_of_trust(
        self,
        service_url: str,
        patient_authenticator: PatientAuthenticator
    ):

        # This NHS number is included within the API-M NHS login mock dataset and utilises the "P9.Cp" Vector of Trust.
        access_code = patient_authenticator.auth(nhs_number="5900068196")

        request_headers = {
            "echo": "",  # enable echo header
            "nhsd-target-identifier": generate_valid_target_identifier(),
            "Authorization": "Bearer " + access_code,
            RenamedHeader.CORRELATION_ID.original: "test_unsupported_vector_of_trust",
        }

        response = requests.get(service_url, headers=request_headers)
        assert (
            response.status_code == 401
        ), "Expected 401 when accessing the API but instead received " + str(response.status_code)

        response_data = response.json()

        assert response_data["resourceType"] == "OperationOutcome"
        assert len(response_data["issue"]) == 1

        issue = response_data["issue"][0]

        assert issue["severity"] == "error"
        assert issue["code"] == "login"
        assert issue["diagnostics"] == "Unsupported Vector of Trust value utilised for authentication."
        assert len(issue["details"]) == 1
        assert len(issue["details"]["coding"]) == 1

        issue_coding = issue["details"]["coding"][0]

        assert issue_coding["system"] == "https://fhir.nhs.uk/CodeSystem/NHSD-API-ErrorOrWarningCode"
        assert issue_coding["code"] == "ACCESS_DENIED"
