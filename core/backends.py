import logging
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakError
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)


class KeycloakAuthenticationBackend(BaseBackend):
    """
    Authentication backend that authenticates users against Keycloak.

    This backend:
    1. Accepts username/password credentials
    2. Validates them against Keycloak using Direct Access Grants flow
    3. Creates or updates the Django user based on Keycloak user data
    4. Returns the authenticated user

    This is useful for:
    - Django admin login
    - Custom login views
    - Testing and development
    """

    def __init__(self):
        super().__init__()
        self.keycloak_openid = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET
        )

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate against Keycloak and create/update Django user.
        """
        if username is None or password is None:
            return None

        try:
            # Authenticate with Keycloak
            token_response = self.keycloak_openid.token(username, password)

            if not token_response:
                logger.warning(f"Failed to obtain token from Keycloak for user: {username}")
                return None

            # Get user info from Keycloak
            userinfo = self.keycloak_openid.userinfo(token_response['access_token'])

            # Extract user information
            email = userinfo.get('email', '')
            first_name = userinfo.get('given_name', '')
            last_name = userinfo.get('family_name', '')
            keycloak_id = userinfo.get('sub')

            # Get or create the Django user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )

            # Update user information if it changed
            if not created:
                updated = False
                if user.email != email:
                    user.email = email
                    updated = True
                if user.first_name != first_name:
                    user.first_name = first_name
                    updated = True
                if user.last_name != last_name:
                    user.last_name = last_name
                    updated = True
                if updated:
                    user.save()

            # Store Keycloak tokens in the session if request is available
            if request:
                request.session['keycloak_access_token'] = token_response.get('access_token')
                request.session['keycloak_refresh_token'] = token_response.get('refresh_token')

            if created:
                logger.info(f"Created new user from Keycloak: {username}")
            else:
                logger.info(f"Authenticated existing user from Keycloak: {username}")

            return user

        except KeycloakAuthenticationError as e:
            logger.warning(f"Keycloak authentication failed for user {username}: {str(e)}")
            return None
        except KeycloakError as e:
            logger.error(f"Keycloak error during authentication for user {username}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Keycloak authentication for user {username}: {str(e)}")
            return None

    def get_user(self, user_id):
        """
        Get a user by their ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None