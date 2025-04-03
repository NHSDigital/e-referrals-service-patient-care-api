import base64
import json

from typing import Collection, TypedDict

from pytest_nhsd_apim.identity_service import (
    AuthorizationCodeConfig,
    AuthorizationCodeAuthenticator,
)

_VALID_NHSD_TARGET_IDENTIFIER: "Identifier" = {
    "system": "urn:ietf:rfc:3986",
    "value": "2b3b21fd-fe9f-403c-9682-10b8d8a4eaf3"
}


def generate_valid_target_identifier() -> str:
    """
    Generate a valid target identifier to supply to the APIs.
    """
    return generate_target_identifier(_VALID_NHSD_TARGET_IDENTIFIER)


def generate_target_identifier(value: "Identifier") -> str:
    """
    Generate a target identifier from a given dictionary to supply to the APIs.
    :param value: dict containing values to be converted into an identifier.
    """
    return base64.b64encode(bytes(json.dumps(value), "utf-8"))


class Identifier(TypedDict):
    system: str
    value: str


class PatientAuthenticator:
    '''
    Class to handle the authentication of a given patient.
    '''
    def __init__(self, patient_care_app: dict[str, Collection[str]], environment: str, oauth_url: str):
        self.patient_care_app = patient_care_app
        self.environment = environment
        self.oauth_url = oauth_url

    def auth(self, nhs_number: str) -> str:
        '''
        Authenticate a given NHS number, returning the provided access token.
        :param nhs_number: The NHS number of the patient to be authenticated.
        '''
        credentials = self.patient_care_app["credentials"][0]

        config = AuthorizationCodeConfig(
            environment=self.environment,
            identity_service_base_url=self.oauth_url,
            client_id=credentials["consumerKey"],
            client_secret=credentials["consumerSecret"],
            scope="nhs-login",
            login_form={"username": nhs_number},
            callback_url=self.patient_care_app["callbackUrl"],
        )
        # Pass the config to the Authenticator
        authenticator = AuthorizationCodeAuthenticator(config=config)

        # Get your token
        token_response = authenticator.get_token()
        print(f"user restricted resp: {token_response}")
        return token_response["access_token"]
