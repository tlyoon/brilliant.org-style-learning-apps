import unittest
from unittest.mock import patch

from app_generator.coordinator.managed import ADMIN_SCOPES
from coordinator.deployment.manage import _ensure_deployment, _web_app_is_reachable


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
                return Response(
                    {
                        "deploymentId": "deployment-id",
                        "entryPoints": [
                            {
                                "entryPointType": "WEB_APP",
                                "webApp": {"url": "https://script.google.com/macros/s/deployment-id/exec"},
                            }
                        ],
                    }
                )

        with patch("coordinator.deployment.manage._web_app_is_reachable", return_value=True):
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

    def test_reachability_probe_sends_no_credentials(self):
        url = "https://script.google.com/macros/s/deployment-id/exec"

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {"ok": False, "code": "UNAUTHORIZED"}

        deployment = {
            "entryPoints": [
                {"entryPointType": "WEB_APP", "webApp": {"url": url}}
            ]
        }
        with patch(
            "coordinator.deployment.manage.requests.post",
            return_value=Response(),
        ) as request:
            self.assertTrue(_web_app_is_reachable(deployment))

        request.assert_called_once_with(url, json={}, timeout=60)

    def test_explicit_web_app_url_is_validated_and_used_without_api_mutation(self):
        url = "https://script.google.com/macros/s/manual-deployment/exec"

        class Session:
            def __getattr__(self, name):
                raise AssertionError(f"Apps Script API must not be called: {name}")

        with patch("coordinator.deployment.manage._web_app_is_reachable", return_value=True):
            deployment_id, resolved_url = _ensure_deployment(
                Session(), script_id="script-id", version_number=8,
                project_name="ManagedProject", web_app_url_override=url,
            )

        self.assertEqual("manual-deployment", deployment_id)
        self.assertEqual(url, resolved_url)


    def test_inaccessible_preferred_adopts_reachable_web_app_without_updating_it(self):
        get_calls = []
        web_app_url = "https://script.google.com/macros/s/web-deployment/exec"

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
            def put(self, url, *, json, timeout):
                raise AssertionError("reachable web-app deployments must not be updated")

            def get(self, url, *, timeout):
                get_calls.append(url)
                if url.endswith("/non-web-deployment"):
                    return Response(
                        {
                            "deploymentId": "non-web-deployment",
                            "entryPoints": [
                                {
                                    "entryPointType": "WEB_APP",
                                    "webApp": {
                                        "url": "https://script.google.com/macros/s/inaccessible/exec"
                                    },
                                }
                            ],
                        }
                    )
                return Response(
                    {
                        "deployments": [
                            {"deploymentId": "non-web-deployment"},
                            {
                                "deploymentId": "web-deployment",
                                "deploymentConfig": {"description": "Manually deployed web app"},
                                "entryPoints": [
                                    {"entryPointType": "WEB_APP", "webApp": {"url": web_app_url}}
                                ],
                            },
                        ]
                    }
                )

        with patch(
            "coordinator.deployment.manage._web_app_is_reachable",
            side_effect=lambda deployment: deployment.get("deploymentId") == "web-deployment",
        ):
            deployment_id, url = _ensure_deployment(
                Session(),
                script_id="script-id",
                version_number=8,
                project_name="ManagedProject",
                preferred_id="non-web-deployment",
            )

        self.assertEqual("web-deployment", deployment_id)
        self.assertEqual(web_app_url, url)
        self.assertEqual(2, len(get_calls))
        self.assertTrue(get_calls[0].endswith("/non-web-deployment"))


if __name__ == "__main__":
    unittest.main()
