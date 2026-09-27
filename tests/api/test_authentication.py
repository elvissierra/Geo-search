import time

import jwt
import pytest

from geo_search_api.api.authentication import (
    Auth0TokenAuthentication,
)
from geo_search_api.api.exceptions import InvalidTokenException

BAD_TOKEN = """
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtpZCJ9.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.
TRNreu-GjJRGdRUlQTWBAGpBrqhywP3g_W-UPc-wnvE
"""
RSA_N = """
tSKfSeI0fukRIX38AHlKB1YPpX8PUYN2JdvfM-XjNmLfU1M74N0VmdzIX95sneQGO9kC2xMIE-AIlt52Yf_KgBZggAlS9Y0Vx8
DsSL2HvOjguAdXir3vYLvAyyHin_mUisJOqccFKChHKjnk0uXy_38-1r17_cYTp76brKpU1I4kM20M__dbvLBWjfzyw9ehufr7
4aVwr-0xJfsBVr2oaQFww_XHGz69Q7yHK6DbxYO4w4q2sIfcC4pT8XTPHo4JZ2M733Ea8a7HxtZS563_mhhRZLU5aynQpwaVv2
U--CL6EvGt8TlNZOkeRv8wz-Rt8B70jzoRpVK36rR-pHKlXhMGT619v82LneTdsqA25Wi2Ld_c0niuul24A6-aaj2u9SWbxA9L
mVtFntvNbRaHXE1SLpLPoIp8uppGF02Nz2v3ld8gCnTTWfq_BQ80Qy8e0coRRABECZrjIMzHEg6MloRDy4na0pRQv61VogqRKD
U2r3_VezFPQDb3ciYsZjWBr3HpNOkUjTrvLmFyOE9Q5R_qQGmc6BYtfk5rn7iIfXlkJAZHXhBy-ElBuiBM-YSkFM7dH92sSIoZ
05V4MP09Xcppx7kdwsJy72Sust9Hnd9B7V35YnVF6W791lVHnenhCJOziRmkH4xLLbPkaST2Ks3IHH7tVltM6NsRk3jNdVM
"""
ERR_MSG = "Invalid token headers"
HEADERS = {
    "kty": "RSA",
    "kid": "kid",
}
PAYLOAD = {
    "iss": "test_issuer/",
    "aud": "test_audience",
    "iat": 1614698924,
    "exp": time.time() + 1000,
}


class MockResponse:

    data = {
        "n": "".join(RSA_N.splitlines()),
        "e": "AQAB",
        "kty": "RSA",
        "kid": "kid",
        "use": "sig",
    }

    @staticmethod
    def json():
        return {"keys": [MockResponse.data]}


class MockRequest:
    META = {"HTTP_AUTHORIZATION": "Bearer"}


@pytest.fixture
def mock_settings(settings):
    settings.AUTH0_DOMAIN = "test_domain/"
    settings.AUTH0_ISSUER = "test_issuer/"
    settings.AUTH0_API_AUDIENCE = "test_audience"
    return settings


@pytest.fixture
def private_key():
    with open("tests/keys/private_key", "rb") as prv_file:
        private_key = prv_file.read()
    return private_key


@pytest.fixture
def mock_response(mocker):
    mocker.patch("requests.get", return_value=MockResponse)


def test_auth0_token_authentication_fail_if_no_auth_provided(mock_settings):
    auth = Auth0TokenAuthentication()
    with pytest.raises(InvalidTokenException) as ex:
        auth.authenticate(MockRequest)
    assert str(ex.value) == "Authentication failed"


def test_auth0_token_authentication_fail_if_empty_auth_provided(mock_settings):
    auth = Auth0TokenAuthentication()
    MockRequest.META["HTTP_AUTHORIZATION"] = ""
    with pytest.raises(InvalidTokenException):
        auth.authenticate(MockRequest)


def test_auth0_token_authentication_fail_if_wrong_format_auth_provided(mock_settings):
    auth = Auth0TokenAuthentication()
    MockRequest.META["HTTP_AUTHORIZATION"] = "Bearer test test"
    with pytest.raises(InvalidTokenException) as ex:
        auth.authenticate(MockRequest)
    assert str(ex.value) == "Authentication failed"


def test_auth0_token_authentication_fail_if_wrong_token_provided(mocker, mock_settings):
    auth = Auth0TokenAuthentication()
    mocker.patch("requests.get", return_value=MockResponse)
    MockRequest.META["HTTP_AUTHORIZATION"] = "Bearer test_token"
    with pytest.raises(InvalidTokenException):
        auth.authenticate(MockRequest)


def test_auth0_token_authentication_positive_scenario(private_key, mock_settings, mock_response):
    auth = Auth0TokenAuthentication()
    token = jwt.encode(payload=PAYLOAD, key=private_key, headers=HEADERS, algorithm="RS256")
    MockRequest.META["HTTP_AUTHORIZATION"] = "Bearer {}".format(token)
    assert auth.authenticate(MockRequest) == ({"id": "", "roles": None}, token.encode())


def test_auth0_token_authentication_fail_if_token_is_expired(
    private_key, mock_settings, mock_response
):
    auth = Auth0TokenAuthentication()
    payload = PAYLOAD.copy()
    payload["exp"] = time.time() - 10
    token = jwt.encode(payload=payload, key=private_key, headers=HEADERS, algorithm="RS256")
    MockRequest.META["HTTP_AUTHORIZATION"] = "Bearer {}".format(token)
    with pytest.raises(InvalidTokenException) as ex:
        auth.authenticate(MockRequest)
    assert str(ex.value) == "Token is expired"


def test_auth0_token_authentication_fail_if_issuer_is_wrong(
    mock_settings, private_key, mock_response
):
    auth = Auth0TokenAuthentication()
    payload = PAYLOAD.copy()
    payload["iss"] = "another_test"
    token = jwt.encode(
        payload=payload, key=private_key.decode(), headers=HEADERS, algorithm="RS256"
    )
    MockRequest.META["HTTP_AUTHORIZATION"] = "Bearer {}".format(token)
    with pytest.raises(InvalidTokenException) as ex:
        auth.authenticate(MockRequest)
    assert str(ex.value) == "Incorrect claims, please check issuer"


def test_auth0_token_authentication_fail_if_audience_is_wrong(
    mock_settings, private_key, mock_response
):
    auth = Auth0TokenAuthentication()
    payload = PAYLOAD.copy()
    payload["aud"] = "another_test"
    token = jwt.encode(
        payload=payload, key=private_key.decode(), headers=HEADERS, algorithm="RS256"
    )
    MockRequest.META["HTTP_AUTHORIZATION"] = "Bearer {}".format(token)
    with pytest.raises(InvalidTokenException) as ex:
        auth.authenticate(MockRequest)
    assert str(ex.value) == "Incorrect claims, please check audience"


def test_auth0_token_authentication_fail_if_token_is_in_wrong_format(
    mock_settings, private_key, mock_response
):
    auth = Auth0TokenAuthentication()
    MockRequest.META["HTTP_AUTHORIZATION"] = "Bearer {}".format("".join(BAD_TOKEN.splitlines()))
    with pytest.raises(InvalidTokenException) as ex:
        auth.authenticate(MockRequest)
    assert str(ex.value) == "Unable to parse authentication"


def test_auth0_token_authentication_fail_if_token_has_another_id(
    mocker, mock_settings, private_key, mock_response
):
    auth = Auth0TokenAuthentication()
    MockResponse.data["kid"] = "another_id"
    mocker.patch("requests.get", return_value=MockResponse)
    with pytest.raises(InvalidTokenException) as ex:
        auth.authenticate(MockRequest)
    assert str(ex.value) == "Authentication failed"
