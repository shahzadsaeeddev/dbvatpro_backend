from datetime import datetime

import jwt
import requests
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from rest_framework.exceptions import AuthenticationFailed

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.db.utils import IntegrityError
from django.utils.timezone import get_current_timezone, make_aware
from celery.utils.time import is_naive


class MyOIDCABackend(OIDCAuthenticationBackend):
    """Class for OIDC Authentication backend."""

    access_token = None

    def verify_claims(self, claims):
        """Verify the provided claims to decide if authentication should be allowed."""

        # Verify claims required by default configuration
        scopes = self.get_settings("OIDC_RP_SCOPES", "preferred_username")
        if "status" in claims:
            raise AuthenticationFailed(claims["message"])

        else:
            if "preferred_username" in scopes.split():
                return "preferred_username" in claims
            return True

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified username."""
        username = claims.get("preferred_username")
        if not username:
            return self.UserModel.objects.none()
        users = self.UserModel.objects.filter(username__iexact=username)
        if users.count() > 1:
            print("user are more than 1")
        return users

    def create_user(self, claims):
        """
        create_user
        Create a new user instance after the user is authenticated from the SSO.

        :param claims: Includes the user details received from the SSO.
        :return: new created user.
        """
        username = claims.get("preferred_username")
        first_name = claims.get("given_name")
        last_name = claims.get("family_name")
        email = claims.get("email")
        roles = self.get_roles(claims)
        try:
            # Ignore duplicate user integrity error  due to race condition
            user = self.UserModel.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_owner=True,
                keycloak_uuid=claims.get("sub"),
                application_roles=roles,
                last_login=datetime.now(get_current_timezone()),
            )
        except IntegrityError:
            user = self.UserModel.objects.get(username=username)
        return user

    def update_user(self, user, claims):
        auth_time = datetime.fromtimestamp(claims.get("iat"))
        auth_time = make_aware(auth_time)

        if user.last_login:
            if is_naive(user.last_login):
                user.last_login = make_aware(user.last_login)
        else:
            user.last_login = auth_time
        if user.last_login <= auth_time:
            user.last_login = auth_time

        user.application_roles = self.get_roles(claims)

        user.save()
        return user

    def get_or_create_user(self, access_token, id_token, payload):
        """Returns a User instance if 1 user is found. Creates a user if not found
        and configured to do so. Returns nothing if multiple users are matched."""
        self.access_token = access_token
        user_info = self.verify(access_token)

        if not self.verify_claims(user_info):
            msg = "Claims verification failed"
            raise SuspiciousOperation(msg)

        users = self.filter_users_by_claims(user_info)

        if len(users) == 1:
            return self.update_user(users[0], user_info)
        elif len(users) > 1:
            # In the rare case that two user accounts have the same email address,
            # bail. Randomly selecting one seems really wrong.
            msg = "Multiple users returned"
            raise SuspiciousOperation(msg)
        elif self.get_settings("OIDC_CREATE_USER", True):
            user = self.create_user(user_info)
            return user
        else:

            self.describe_user_by_claims(user_info)

            return None

    @classmethod
    def verify(cls, access_token):
        try:
            claim = jwt.decode(
                access_token,
                key=settings.OIDC_RP_IDP_SIGN_KEY,
                audience="account",
                algorithms=["RS256"],
                issuer=f"{settings.OIDC_HOST}/realms/{settings.OIDC_REALM}",
            )


        except jwt.ExpiredSignatureError as e:
            print(e)
            # Token has expired
            return {"status": "Failed", "message": "Verification token has expired"}
        except jwt.exceptions.InvalidTokenError:
            return {
                "status": "Failed",
                "message": "Authentication token verification failed",
            }
        return claim

    def get_userinfo(self, access_token, id_token, payload):
        """Return user details dictionary. The id_token and payload are not used in
        the default implementation, but may be used when overriding this method"""

        user_response = requests.get(
            self.OIDC_OP_USER_ENDPOINT,
            headers={"Authorization": "Bearer {0}".format(access_token)},
            verify=self.get_settings("OIDC_VERIFY_SSL", True),
            timeout=self.get_settings("OIDC_TIMEOUT", None),
            proxies=self.get_settings("OIDC_PROXY", None),
        )
        user_response.raise_for_status()
        return user_response.json()

    def get_roles(self, claim):
        user_roles =[]
        resource_access = claim.get("resource_access", {})
        onboard_access = resource_access.get("onboard", {})
        roles = onboard_access.get("roles", [])

        if roles:
            user_roles = [role for role in roles if role.startswith("CAN")]
        return user_roles
