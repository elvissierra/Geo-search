import json
import jwt
import requests
from django.conf import settings
from jwt.exceptions import DecodeError
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from geo_search_api.api.exceptions import InvalidTokenException


class Auth0TokenAuthentication(BaseAuthentication):
    """
    Auth0 token based authentication.
    Clients should authenticate by passing the token key in the 'Authorization'
    HTTP header, starting with the string 'Bearer '.  For example:
        Authorization: Bearer <token data>
    """

    keyword = "Bearer"
    err_msg = "Authentication failed"

    def authenticate(self, request):
        """
        Authentication function which is called before any request to API
        """
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            raise InvalidTokenException(self.err_msg)

        if len(auth) != 2:
            raise InvalidTokenException(self.err_msg)
        token = auth[1]
        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        """
        Authenticator for token.
        Returns user information and token.
        """
        payload, is_valid = self.validate_token(token)
        if not is_valid:
            raise InvalidTokenException(self.err_msg)
        sub = payload.get("sub")
        user_info = {
            "id": sub.split("|")[1] if sub else "",
            "roles": payload.get("permissions"),
        }
        return user_info, token

    def validate_token(self, token):
        """
        Check that auth0 token is valid for given domain and audience
        """
        resp = requests.get(settings.AUTH0_DOMAIN + ".well-known/jwks.json")
        jwks = resp.json()
        try:
            unverified_header = jwt.get_unverified_header(token)
        except DecodeError:
            return {}, False
        public_key = None
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
        if public_key is not None:
            return self.decode_token(token, public_key)
        return {}, False

    @staticmethod
    def decode_token(token, public_key):
        """
        Decode the token and match metadata.
        :param token: Auth token
        :param public_key: Public key got from auth0
        """
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=settings.AUTH0_ALGORITHMS,
                audience=settings.AUTH0_API_AUDIENCE,
                issuer=settings.AUTH0_ISSUER,
            )
            return payload, True
        except jwt.ExpiredSignatureError:
            raise InvalidTokenException("Token is expired") from jwt.ExpiredSignatureError
        except jwt.InvalidIssuerError:
            raise InvalidTokenException(
                "Incorrect claims, please check issuer"
            ) from jwt.InvalidIssuerError
        except jwt.InvalidAudienceError:
            raise InvalidTokenException(
                "Incorrect claims, please check audience"
            ) from jwt.InvalidAudienceError
        except Exception:
            raise InvalidTokenException("Unable to parse authentication") from Exception
