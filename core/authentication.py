import jwt
import logging
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from keycloak import KeycloakOpenID
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

User = get_user_model()
logger = logging.getLogger(__name__)


class KeycloakJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that validates tokens issued by Keycloak.

    This authentication class:
    1. Extracts the JWT token from the Authorization header
    2. Validates the token using Keycloak's public key (RS256)
    3. Extracts user information from the token claims
    4. Creates or updates the Django user based on Keycloak user data
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keycloak_openid = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET
        )

    def get_validated_token(self, raw_token):
        """
        Validates the token using Keycloak's public key.
        """
        try:
            # Get Keycloak's public key for token validation
            public_key = (
                "-----BEGIN PUBLIC KEY-----\n"
                + self.keycloak_openid.public_key()
                + "\n-----END PUBLIC KEY-----"
            )

            # Configure token validation options
            options = {
                "verify_signature": True,
                "verify_aud": False,  # Keycloak doesn't always include aud claim
                "verify_iat": True,
                "verify_exp": True,
                "verify_nbf": True,
            }

            # Decode and validate the token
            decoded_token = jwt.decode(
                raw_token,
                public_key,
                algorithms=["RS256"],
                options=options,
                audience=settings.KEYCLOAK_CLIENT_ID if hasattr(settings, 'KEYCLOAK_AUDIENCE') else None
            )

            return decoded_token

        except ExpiredSignatureError:
            logger.warning("Keycloak token has expired")
            raise AuthenticationFailed("Token has expired")
        except InvalidTokenError as e:
            logger.warning(f"Invalid Keycloak token: {str(e)}")
            raise AuthenticationFailed(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Error validating Keycloak token: {str(e)}")
            raise AuthenticationFailed("Could not validate token")

    def get_user(self, validated_token):
        """
        Retrieves or creates a Django user based on the Keycloak token claims.
        """
        try:
            # Extract user information from token claims
            username = validated_token.get("preferred_username")
            email = validated_token.get("email", "")
            first_name = validated_token.get("given_name", "")
            last_name = validated_token.get("family_name", "")
            keycloak_id = validated_token.get("sub")  # Keycloak user ID

            if not username:
                raise AuthenticationFailed("Token does not contain username")

            # Get or create the user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                }
            )

            # Update user information if it changed in Keycloak
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

            # Store Keycloak-specific data in user object for potential use
            user.keycloak_id = keycloak_id
            user.keycloak_token = validated_token

            if created:
                logger.info(f"Created new user from Keycloak: {username}")

            return user

        except User.DoesNotExist:
            logger.warning(f"User not found: {username}")
            raise AuthenticationFailed("User not found")
        except Exception as e:
            logger.error(f"Error getting user from token: {str(e)}")
            raise AuthenticationFailed(f"Could not authenticate user: {str(e)}")

    def authenticate(self, request):
        """
        Authenticates the request using Keycloak JWT token.
        """
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        return (user, validated_token)