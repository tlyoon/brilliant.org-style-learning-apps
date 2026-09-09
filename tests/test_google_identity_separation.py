import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app_generator.coordinator.managed import _verify_admin_account
from app_generator.sources.google_drive_auth import authorize_google_drive


class GoogleIdentitySeparationTests(unittest.TestCase):
    def test_drive_authorization_uses_oauth_account_not_gemini_account(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client_file = root / "client.json"
            token_file = root / "token.json"
            client_file.write_text("{}\n", encoding="utf-8")
            token_file.write_text("{}\n", encoding="utf-8")
            config = SimpleNamespace(
                drive_oauth_client_file=client_file,
                drive_token_file=token_file,
                drive_api_timeout_seconds=1,
                oauth_login="oauth@example.com",
                login_name="gemini@example.com",
            )
            credentials = Mock(expired=False, refresh_token=None, valid=True)
            credentials.to_json.return_value = "{}"
            response = Mock()
            response.raise_for_status.return_value = None
            response.json.return_value = {"user": {"emailAddress": "oauth@example.com"}}
            session = Mock()
            session.get.return_value = response

            with (
                patch(
                    "google.oauth2.credentials.Credentials.from_authorized_user_file",
                    return_value=credentials,
                ),
                patch(
                    "google.auth.transport.requests.AuthorizedSession",
                    return_value=session,
                ),
            ):
                authorization = authorize_google_drive(config)

            self.assertEqual("oauth@example.com", authorization.email)
            self.assertIs(session, authorization.session)

    def test_coordinator_admin_verification_uses_oauth_account_not_gemini_account(self):
        config = SimpleNamespace(
            drive_api_timeout_seconds=1,
            oauth_login="oauth@example.com",
            login_name="gemini@example.com",
        )
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"user": {"emailAddress": "oauth@example.com"}}
        session = Mock()
        session.get.return_value = response

        with patch(
            "app_generator.coordinator.managed.AuthorizedSession",
            return_value=session,
        ):
            _verify_admin_account(config, Mock())

        session.get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
