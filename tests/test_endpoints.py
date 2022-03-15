import pytest
from api_test_utils.oauth_helper import OauthHelper
from api_test_utils.apigee_api_apps import ApigeeApiDeveloperApps
from api_test_utils.apigee_api_products import ApigeeApiProducts


class TestEndpoints:

    @pytest.fixture()
    def app(self):
        """
        Import the test utils module to be able to:
            - Create apigee test application
                - Update custom attributes
                - Update custom ratelimits
                - Update products to the test application
        """
        return ApigeeApiDeveloperApps()

    @pytest.fixture()
    def product(self):
        """
        Import the test utils module to be able to:
            - Create apigee test product
                - Update custom scopes
                - Update environments
                - Update product paths
                - Update custom attributes
                - Update proxies to the product
                - Update custom ratelimits
        """
        return ApigeeApiProducts()

    @pytest.fixture()
    async def test_app_and_product(self, app, product):
        """Create a test app and product which can be modified in the test"""
        await product.create_new_product()

        await app.create_new_app()

        await product.update_scopes([
            "urn:nhsd:apim:app:level3:e-referrals-service-patient-care-api",
            "urn:nhsd:apim:user-nhs-id:aal3:e-referrals-service-patient-care-api"
        ])
        await app.add_api_product([product.name])

        yield product, app

        await app.destroy_app()
        await product.destroy_product()

    @pytest.fixture()
    async def get_token(self, test_app_and_product):
        """Call identity server to get an access token"""
        test_product, test_app = test_app_and_product
        oauth = OauthHelper(
            client_id=test_app.client_id,
            client_secret=test_app.client_secret,
            redirect_uri=test_app.callback_url
            )
        token_resp = await oauth.get_token_response(grant_type="authorization_code")
        assert token_resp["status_code"] == 200
        return token_resp['body']

    def test_user_restricted(self, get_token):
        """
        In here you can add tests which call your proxy
        You can use the 'get_token' fixture to call the proxy with a access token
        """
        pass
