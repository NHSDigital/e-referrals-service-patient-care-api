"""
Tests against a deployed Proxygen instance that need an Apigee access token, so that
pytest-nhsd-apim can find the proxy and create a subscribed test app. They're skipped
when APIGEE_ACCESS_TOKEN isn't set.
"""
import pytest
import requests

from tests.proxygen.test_proxygen_smoke import HEALTHCARE_SERVICE, SERVICE_REQUEST, TIMEOUT

pytestmark = [pytest.mark.proxygen, pytest.mark.apigee_token]

P9_NHS_NUMBER = "9900000285"


def test_plugin_resolves_the_proxy_under_test(nhsd_apim_proxy_url, proxygen_base_url):
    # Checks the proxy name convention in conftest.py matches what Proxygen deployed.
    assert nhsd_apim_proxy_url == proxygen_base_url


@pytest.mark.api_paths
@pytest.mark.nhsd_apim_authorization(
    access="patient",
    level="P9",
    login_form={"username": P9_NHS_NUMBER},
)
@pytest.mark.parametrize("path", [SERVICE_REQUEST, HEALTHCARE_SERVICE])
def test_p9_patient_passes_proxygen_auth(nhsd_apim_proxy_url, nhsd_apim_auth_headers, path):
    response = requests.get(f"{nhsd_apim_proxy_url}/{path}", headers=nhsd_apim_auth_headers, timeout=TIMEOUT)

    # Until the instance has a target, only Proxygen's auth decision can be asserted.
    # Tighten to the backend's responses once the adapter target is deployed.
    assert response.status_code not in (401, 403), response.text
