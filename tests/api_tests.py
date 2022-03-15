from functools import partial

import pytest
from aiohttp import ClientResponse
from api_test_utils.api_session_client import APISessionClient
from api_test_utils.api_test_session_config import APITestSessionConfig
from api_test_utils import poll_until, env


async def _is_deployed(resp: ClientResponse, api_test_config: APITestSessionConfig) -> bool:

    if resp.status != 200:
        return False
    body = await resp.json()

    return body.get("commitId") == api_test_config.commit_id


async def is_401(resp: ClientResponse) -> bool:
    return resp.status == 401


@pytest.mark.e2e
@pytest.mark.smoketest
def test_output_test_config(api_test_config: APITestSessionConfig):
    print(api_test_config)


@pytest.mark.e2e
@pytest.mark.smoketest
@pytest.mark.asyncio
async def test_wait_for_ping(api_client: APISessionClient, api_test_config: APITestSessionConfig):
    """
        test for _ping ..  this uses poll_until to wait until the correct SOURCE_COMMIT_ID ( from env var )
        is available
    """

    is_deployed = partial(_is_deployed, api_test_config=api_test_config)

    await poll_until(
        make_request=lambda: api_client.get('_ping'),
        until=is_deployed,
        timeout=120
    )


@pytest.mark.e2e
@pytest.mark.smoketest
@pytest.mark.asyncio
async def test_check_status_is_secured(api_client: APISessionClient):

    await poll_until(
        make_request=lambda: api_client.get('_status'),
        until=is_401,
        timeout=120
    )


@pytest.mark.e2e
@pytest.mark.smoketest
@pytest.mark.asyncio
async def test_wait_for_status(api_client: APISessionClient, api_test_config: APITestSessionConfig):

    """
        test for _status ..  this uses poll_until to wait until the correct SOURCE_COMMIT_ID ( from env var )
        is available
    """

    is_deployed = partial(_is_deployed, api_test_config=api_test_config)

    await poll_until(
        make_request=lambda: api_client.get('_status', headers={'apikey': env.status_endpoint_api_key()}),
        until=is_deployed,
        timeout=120
    )
