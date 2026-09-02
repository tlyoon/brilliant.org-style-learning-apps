import unittest

from app_generator.coordinator.managed import ADMIN_SCOPES
from coordinator.deployment.manage import _ensure_deployment


class CoordinatorDeploymentTests(unittest.TestCase):
    def test_admin_scopes_explicitly_include_google_identity_bundle(self):
        self.assertIn("openid", ADMIN_SCOPES)
        self.assertIn("https://www.googleapis.com/auth/userinfo.email", ADMIN_SCOPES)

    def test_create_deployment_posts_deployment_config_directly(self):
        calls = []

        class Response:
            status_code = 200
            text = ""

            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        class Session:
            def get(self, url, *, timeout):
                return Response({"deployments": []})

            def post(self, url, *, json, timeout):
                calls.append((url, json, timeout))
                return Response({"deploymentId": "deployment-id"})

        deployment_id, url = _ensure_deployment(
            Session(),
            script_id="script-id",
            version_number=7,
            project_name="ManagedProject",
        )

        self.assertEqual("deployment-id", deployment_id)
        self.assertEqual("https://script.google.com/macros/s/deployment-id/exec", url)
        self.assertEqual("script-id", calls[0][1]["scriptId"])
        self.assertEqual(7, calls[0][1]["versionNumber"])
        self.assertNotIn("deploymentConfig", calls[0][1])


if __name__ == "__main__":
    unittest.main()
