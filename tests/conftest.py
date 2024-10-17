# flake8: noqa
import os
import requests

from uuid import uuid4
from time import time
from datetime import datetime

import pytest
import pytest_asyncio

from pytest_nhsd_apim.identity_service import (
    AuthorizationCodeConfig,
    AuthorizationCodeAuthenticator,
)
from pytest_nhsd_apim.apigee_apis import (
    ApiProductsAPI,
    ApigeeClient,
    ApigeeNonProdCredentials,
    DeveloperAppsAPI,
)

@pytest.fixture()
def client():
    config = ApigeeNonProdCredentials()
    return ApigeeClient(config=config)


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
    return "9900000285"


@pytest.fixture(scope="session")
def service_name():
    return get_env("FULLY_QUALIFIED_SERVICE_NAME")


@pytest.fixture(scope="session")
def service_url(environment):
    if environment == "prod":
        base_url = "https://api.service.nhs.uk"
    else:
        http_base = "https://"
        base_url = f"{http_base}{environment}.api.service.nhs.uk"

    service_base_path = get_env("SERVICE_BASE_PATH")

    return f"{base_url}/{service_base_path}"


@pytest.fixture(scope="session")
def status_endpoint_api_key():
    return get_env("STATUS_ENDPOINT_API_KEY")


@pytest.fixture(scope="session")
def oauth_url():
    oauth_proxy = get_env("OAUTH_PROXY")
    oauth_base_uri = get_env("OAUTH_BASE_URI")
    return f"{oauth_base_uri}/{oauth_proxy}"


@pytest.fixture
def make_product(client, environment, service_name):
    async def _make_product(product_scopes):
        # Setup
        product = ApiProductsAPI(client=client)

        proxies = [f"identity-service-mock-{environment}"]

        if service_name is not None:
            proxies.append(service_name)

        product_name = f"apim-auto-{uuid4()}"

        attributes=[
            {"name": "requestLimit_referral", "value": "100"},
            {"name": "requestLimit_general", "value": "100"},
            {"name": "burstLimit_referral", "value": "1200pm"},
            {"name": "burstLimit_general", "value": "1200pm"}
        ]

        body = {
            "proxies": proxies,
            "scopes": product_scopes,
            "name": product_name,
            "displayName": product_name,
            "attributes": attributes,
            "approvalType": "auto",
            "environments": ["internal-dev"],
            "quota": 500,
            "quotaInterval": "1",
            "quotaTimeUnit": "minute",
        }
        product.post_products(body=body)
        return product_name

    return _make_product


@pytest.fixture
def make_app(client):
    async def _make_app(product, custom_attributes={}):
        # Setup
        devAppAPI = DeveloperAppsAPI(client=client)
        app_name = f"apim-auto-{uuid4()}"

        attributes = [{"name": key, "value": value} for key, value in custom_attributes.items()]
        attributes.append({"name": "DisplayName", "value": app_name})

        body = {
            "apiProducts": [product],
            "attributes": attributes,
            "name": app_name,
            "scopes": [],
            "status": "approved",
            "callbackUrl": "http://example.com",
        }
        app = devAppAPI.create_app(email="apm-testing-internal-dev@nhs.net", body=body)
        print(f"CREATED APP NAME: {app_name}")

        return app

    return _make_app


@pytest_asyncio.fixture
async def patient_care_product(client,make_product):
    # Setup
    productName = await make_product(["urn:nhsd:apim:user-nhs-login:P9:e-referrals-service-patient-care-api"])

    yield productName

    # Teardown
    print(f"Cleanup product: {productName}")
    product = ApiProductsAPI(client=client)
    product.delete_product_by_name(product_name=productName)


@pytest_asyncio.fixture
async def patient_care_app(
    client,
    make_app,
    patient_care_product,
    jwt_public_key_url
):
    # Setup
    app = await make_app(
        patient_care_product,
        {
            "jwks-resource-url": jwt_public_key_url
        },
    )

    appName = app["name"]
    yield app

    # Teardown
    print(f"Cleanup app: {appName}")

    devApp = DeveloperAppsAPI(client=client)
    devApp.delete_app_by_name(email="apm-testing-internal-dev@nhs.net", app_name=appName)


@pytest.fixture
def patient_access_token(client, patient_care_app, valid_nhs_number,environment, oauth_url):
        print(f"Attempting to authenticate: {valid_nhs_number}")

        credentials = patient_care_app["credentials"][0]

        config = AuthorizationCodeConfig(
            environment=environment,
            identity_service_base_url=oauth_url,
            client_id=credentials["consumerKey"],
            client_secret=credentials["consumerSecret"],
            scope="nhs-login",
            login_form={"username": valid_nhs_number},
            callback_url=patient_care_app["callbackUrl"],
        )
        # 2. Pass the config to the Authenticator
        authenticator = AuthorizationCodeAuthenticator(config=config)

        # 3. Get your token
        token_response = authenticator.get_token()
        print(f"user restricted resp: {token_response}")
        return token_response["access_token"]
