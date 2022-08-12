# flake8: noqa
import os

from uuid import uuid4
from time import time

import pytest
from api_test_utils.apigee_api_apps import ApigeeApiDeveloperApps
from api_test_utils.apigee_api_products import ApigeeApiProducts
from api_test_utils.oauth_helper import OauthHelper
from api_test_utils.api_test_session_config import APITestSessionConfig
from api_test_utils.fixtures import api_client   # pylint: disable=unused-import

__JWKS_RESOURCE_URL = "https://raw.githubusercontent.com/NHSDigital/identity-service-jwks/main/jwks/internal-dev/9baed6f4-1361-4a8e-8531-1f8426e3aba8.json"

@pytest.fixture(scope='session')
def api_test_config() -> APITestSessionConfig:
    """
        this imports a 'standard' test session config,
        which builds the proxy uri

    """
    return APITestSessionConfig()


def get_env(variable_name: str) -> str:
    """Returns an environment variable"""
    try:
        var = os.environ[variable_name]
        if not var:
            raise RuntimeError(f"Variable is null, Check {variable_name}.")
        return var
    except KeyError:
        raise RuntimeError(f"Variable is not set, Check {variable_name}.")


@pytest.fixture(scope="session")
def environment():
    return get_env("ENVIRONMENT")


@pytest.fixture(scope="session")
def valid_nhs_number():
    return "9912003888"


@pytest.fixture(scope="session")
def service_name():
    return get_env("FULLY_QUALIFIED_SERVICE_NAME")


@pytest.fixture(scope="session")
def service_url(environment):
    if environment == "prod":
        base_url = "https://api.service.nhs.uk"
    else:
        base_url = f"https://{environment}.api.service.nhs.uk"

    service_base_path = get_env("SERVICE_BASE_PATH")

    return f"{base_url}/{service_base_path}"


@pytest.fixture(scope="session")
def status_endpoint_api_key():
    return get_env("STATUS_ENDPOINT_API_KEY")


@pytest.fixture(scope="session")
def token_url():
    oauth_proxy = get_env("OAUTH_PROXY")
    oauth_base_uri = get_env("OAUTH_BASE_URI")
    return f"{oauth_base_uri}/{oauth_proxy}/token"


@pytest.fixture
def make_product(environment, service_name):
    async def _make_product(product_scopes):
        # Setup
        product = ApigeeApiProducts()
        await product.create_new_product()

        print(f"CREATED PRODUCT NAME: {product.name}")

        # Update products allowed paths
        proxies = [f"identity-service-mock-{environment}"]

        if service_name is not None:
            proxies.append(service_name)

        await product.update_proxies(proxies)
        await product.update_scopes(scopes=product_scopes)
        return product

    return _make_product


@pytest.fixture
def make_app():
    async def _make_app(product, custom_attributes):
        # Setup
        app = ApigeeApiDeveloperApps()
        await app.create_new_app()

        print(f"CREATED APP NAME: {app.name}")

        await app.set_custom_attributes(custom_attributes)

        # Assign the new app to the product
        await app.add_api_product([product.name])

        app.oauth = OauthHelper(app.client_id, app.client_secret, app.callback_url)
        return app

    return _make_app


@pytest.fixture
async def patient_care_product(make_product):
    # Setup
    product = await make_product(["urn:nhsd:apim:user-nhs-login:P9:e-referrals-service-patient-care-api"])

    await product.update_attributes(
        attributes={"requestLimit_referral": "100",
            "requestLimit_general": "100",
            "burstLimit_referral": "1200pm",
            "burstLimit_general": "1200pm"
        }
    )

    yield product

    # Teardown
    print(f"Cleanup product: {product.name}")
    await product.destroy_product()


@pytest.fixture
async def patient_care_app(
    make_app,
    patient_care_product
):
    # Setup
    app = await make_app(
        patient_care_product,
        {
            "jwks-resource-url": __JWKS_RESOURCE_URL
        },
    )

    yield app

    # Teardown
    print(f"Cleanup app: {app.name}")
    await app.destroy_app()


@pytest.fixture
async def nhs_login_subject_token(patient_care_app: ApigeeApiDeveloperApps, valid_nhs_number: str):
    id_token_claims = {
        "aud": "tf_-APIM-1",
        "id_status": "verified",
        "token_use": "id",
        "auth_time": 1616600683,
        "iss": "https://identity.ptl.api.platform.nhs.uk/auth/realms/NHS-Login-mock-internal-dev",  # Points to internal dev -> testing JWKS
        "sub": "https://internal-dev.api.service.nhs.uk",
        "exp": int(time()) + 300,
        "iat": int(time()) - 10,
        "vtm": "https://auth.sandpit.signin.nhs.uk/trustmark/auth.sandpit.signin.nhs.uk",
        "jti": str(uuid4()),
        "identity_proofing_level": "P9",
        "birthdate": "1939-09-26",
        "nhs_number": valid_nhs_number,
        "nonce": "randomnonce",
        "surname": "CARTHY",
        "vot": "P9.Cp.Cd",
        "family_name": "CARTHY",
    }

    id_token_headers = {
        "kid": "B86zGrfcoloO13rnjKYDyAJcqj2iZAMrS49jyleL0Fo",
        "typ": "JWT",
        "alg": "RS512"
    }

    # private key we retrieved from earlier
    nhs_login_id_token_private_key_path = get_env("ID_TOKEN_NHS_LOGIN_PRIVATE_KEY_ABSOLUTE_PATH")

    with open(nhs_login_id_token_private_key_path, "r") as f:
        contents = f.read()

    id_token_jwt = patient_care_app.oauth.create_id_token_jwt(
        algorithm="RS512",
        claims=id_token_claims,
        headers=id_token_headers,
        signing_key=contents,
    )

    return id_token_jwt

@pytest.fixture
async def patient_access_token(patient_care_app: ApigeeApiDeveloperApps, nhs_login_subject_token):

    oauth_proxy = get_env("OAUTH_PROXY")
    oauth_base_uri = get_env("OAUTH_BASE_URI")
    token_url = f"{oauth_base_uri}/{oauth_proxy}/token"

    jwt = patient_care_app.oauth.create_jwt(
        kid="test-1",
        claims={
                "sub": patient_care_app.client_id,
                "iss": patient_care_app.client_id,
                "jti": str(uuid4()),
                "aud": token_url,
                "exp": int(time()) + 60,
        }
    )

    token = await get_token(patient_care_app, nhs_login_subject_token, jwt)
    return token["access_token"]


async def get_token(
    app: ApigeeApiDeveloperApps, nhs_login_subject_token, jwt
):
    oauth = app.oauth

    resp = await oauth.get_token_response(grant_type="token_exchange",
    data={
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "subject_token": nhs_login_subject_token,
        "client_assertion": jwt,
    })

    if resp["status_code"] != 200:
        message = "unable to get token"
        raise RuntimeError(
            f"\n{'*' * len(message)}\n"
            f"MESSAGE: {message}\n"
            f"URL: {resp.get('url')}\n"
            f"STATUS CODE: {resp.get('status_code')}\n"
            f"RESPONSE: {resp.get('body')}\n"
            f"HEADERS: {resp.get('headers')}\n"
            f"TOKEN: {nhs_login_subject_token}\n"
            f"{'*' * len(message)}\n"
        )
    return resp["body"]
