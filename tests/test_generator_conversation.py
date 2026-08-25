import unittest
from unittest.mock import patch

from app_generator.errors import UiContractError
from app_generator.gemini import selectors
from app_generator.gemini.conversation import GemConversationPage, _complete_json_frame


class GeneratorConversationTests(unittest.TestCase):
    class Driver:
        def __init__(self):
            self.loaded_urls = []
            self.executed_scripts = []
            self.generation_active = False
            self.response_complete = True

        def get(self, url):
            self.loaded_urls.append(url)

        def execute_script(self, script, element):
            self.executed_scripts.append((script, element))

        def find_elements(self, by, selector):
            locator = (by, selector)
            if self.generation_active and locator in selectors.GENERATION_ACTIVE:
                return [GeneratorConversationTests.Element()]
            if self.response_complete and locator in selectors.RESPONSE_COMPLETE:
                return [GeneratorConversationTests.Element()]
            return []

    class Element:
        def __init__(self, *, click_error=None, element_id="", value=""):
            self.clicked = False
            self.click_error = click_error
            self.id = element_id
            self.value = value
            self.sent_keys = []

        def click(self):
            self.clicked = True
            if self.click_error:
                raise self.click_error

        def is_displayed(self):
            return True

        def get_attribute(self, name):
            return self.value if name == "value" else None

        def send_keys(self, keys):
            self.sent_keys.append(keys)
            self.value = ""

    class ElementClickInterceptedException(Exception):
        pass

    def page(self, driver):
        return GemConversationPage(driver, "https://gemini.google.com/gem/test", 1, 1)

    def test_model_response_selectors_do_not_include_bare_message_content(self):
        self.assertNotIn(("css selector", "message-content"), selectors.MODEL_RESPONSES)
        self.assertIn(("css selector", "model-response message-content"), selectors.MODEL_RESPONSES)

    def test_introductory_model_content_does_not_mark_conversation_stale(self):
        driver = self.Driver()
        composer = self.Element()
        with (
            patch("app_generator.gemini.conversation.find_first", return_value=composer) as finder,
            patch("app_generator.gemini.conversation.find_all", return_value=[]) as find_all,
        ):
            self.page(driver).open_new()
        self.assertEqual(["https://gemini.google.com/gem/test"], driver.loaded_urls)
        finder.assert_called_once_with(driver, selectors.COMPOSER, 1)
        self.assertEqual(2, find_all.call_count)
        find_all.assert_called_with(driver, selectors.USER_MESSAGES)

    def test_prior_user_message_forces_a_new_conversation(self):
        driver = self.Driver()
        composer = self.Element()
        new_chat = self.Element()
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, new_chat, composer],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[self.Element()], []],
            ),
        ):
            self.page(driver).open_new()
        self.assertTrue(new_chat.clicked)
        self.assertEqual(
            ["https://gemini.google.com/gem/test", "https://gemini.google.com/gem/test"],
            driver.loaded_urls,
        )

    def test_persisting_user_message_still_stops_safely(self):
        driver = self.Driver()
        composer = self.Element()
        new_chat = self.Element()
        existing = self.Element()
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, new_chat, composer],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[existing], [existing]],
            ),
        ):
            with self.assertRaisesRegex(UiContractError, "fresh conversation"):
                self.page(driver).open_new()

    def test_ask_uses_dom_click_when_layout_intercepts_send_button(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element(click_error=self.ElementClickInterceptedException())
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[], [self.Element()], [self.Element()]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch(
                "app_generator.gemini.conversation.element_text",
                return_value='BEGIN_JSON\n{"ok": true}\nEND_JSON',
            ),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0, 0, 0.5, 3],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            self.assertIn("BEGIN_JSON", self.page(driver).ask("prompt"))
        click_scripts = [item for item in driver.executed_scripts if item[0] == "arguments[0].click()"]
        self.assertEqual([("arguments[0].click()", send)], click_scripts)

    def test_ask_detects_response_text_replaced_in_existing_container(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        reused_response = self.Element(element_id="model-response-1")
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[reused_response], [reused_response], [reused_response]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch(
                "app_generator.gemini.conversation.element_text",
                side_effect=[
                    "Gem introduction",
                    'BEGIN_JSON\n{"ok": true}\nEND_JSON',
                    'BEGIN_JSON\n{"ok": true}\nEND_JSON',
                ],
            ),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0, 0, 0.5, 3],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            self.assertIn("BEGIN_JSON", self.page(driver).ask("prompt"))

    def test_ask_returns_complete_sentinel_response_when_stop_control_is_gone(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        response = self.Element(element_id="new-model-response")
        framed = 'BEGIN_JSON\n{"ok": true}\nEND_JSON'
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[], [response], [response]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch("app_generator.gemini.conversation.element_text", return_value=framed),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0, 0, 0.5],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            self.assertEqual(framed, self.page(driver).ask("prompt"))

    def test_ask_waits_for_generation_control_to_finish_before_returning_json(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        response = self.Element(element_id="new-model-response")
        framed = 'BEGIN_JSON\n{"ok": true}\nEND_JSON'
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[], [response], [response], [response]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch("app_generator.gemini.conversation.element_text", return_value=framed),
            patch(
                "app_generator.gemini.conversation._generation_signals",
                side_effect=[(True, False), (True, False), (False, True)],
            ) as signals,
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0, 0.5, 1],
            ),
            patch("app_generator.gemini.conversation.time.sleep") as sleeper,
        ):
            self.assertEqual(framed, self.page(driver).ask("prompt"))
        self.assertEqual(3, signals.call_count)
        self.assertEqual(1, sleeper.call_count)

    def test_submission_noop_retries_dom_click_then_native_enter(self):
        driver = self.Driver()
        driver.response_complete = False
        composer = self.Element(value="prompt remains in composer")
        send = self.Element()
        page = self.page(driver)

        with (
            patch("app_generator.gemini.conversation.find_first", return_value=send),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 4, 4, 8, 8, 8, 9],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            self.assertFalse(page._confirm_prompt_submitted(composer, send, set()))

        self.assertIn(("arguments[0].click()", send), driver.executed_scripts)
        self.assertEqual(1, len(composer.sent_keys))

    def test_ask_removes_attachment_badge_text_outside_json_frame(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        response = self.Element(element_id="new-model-response")
        framed = 'BEGIN_JSON\n{"ok": true}\nEND_JSON'
        rendered = framed + "\nPDF\n+ 4"
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[], [response], [response]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch("app_generator.gemini.conversation.element_text", return_value=rendered),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0, 0, 0.5],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            self.assertEqual(framed, self.page(driver).ask("prompt"))

    def test_ask_frames_complete_json_when_gemini_omits_sentinels(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        response = self.Element(element_id="new-model-response")
        rendered = '{"ok": true}\nPDF\n+ 4'
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[], [response], [response]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch("app_generator.gemini.conversation.element_text", return_value=rendered),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0, 0, 0.5],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            self.assertEqual(
                'BEGIN_JSON\n{"ok": true}\nEND_JSON',
                self.page(driver).ask("prompt"),
            )

    def test_ask_checks_all_changed_response_candidates(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        complete = self.Element(element_id="complete-response")
        partial = self.Element(element_id="partial-wrapper")
        texts = {
            complete: 'BEGIN_JSON\n{"ok": true}\nEND_JSON',
            partial: "Response controls",
        }
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[], [complete, partial], [complete, partial]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch(
                "app_generator.gemini.conversation.element_text",
                side_effect=lambda element: texts[element],
            ),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0.5],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            self.assertEqual(texts[complete], self.page(driver).ask("prompt"))

    def test_ask_does_not_reuse_previous_frame_from_changed_aggregate_wrapper(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        wrapper = self.Element(element_id="aggregate-wrapper")
        old = 'BEGIN_JSON\n{"id": "old"}\nEND_JSON'
        old_with_new_user_ui = old + "\nNew user prompt"
        new = old_with_new_user_ui + '\nBEGIN_JSON\n{"id": "new"}\nEND_JSON'
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[wrapper], [wrapper], [wrapper], [wrapper], [wrapper]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch(
                "app_generator.gemini.conversation.element_text",
                side_effect=[old, old_with_new_user_ui, old_with_new_user_ui, new, new],
            ),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0, 0, 0.5],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            self.assertEqual(
                'BEGIN_JSON\n{"id": "new"}\nEND_JSON',
                self.page(driver).ask("prompt"),
            )

    def test_ask_accepts_identical_frame_from_genuinely_new_response_element(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        old_response = self.Element(element_id="old-response")
        new_response = self.Element(element_id="new-response")
        framed = 'BEGIN_JSON\n{"id": "same-retry"}\nEND_JSON'
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[old_response], [old_response, new_response], [old_response, new_response]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch("app_generator.gemini.conversation.element_text", return_value=framed),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0.5],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            self.assertEqual(framed, self.page(driver).ask("prompt"))

    def test_json_frame_skips_an_earlier_non_json_bracket(self):
        self.assertEqual(
            'BEGIN_JSON\n{"ok": true}\nEND_JSON',
            _complete_json_frame('Status [complete]\n{"ok": true}\nPDF'),
        )

    def test_json_frame_does_not_accept_nested_object_while_outer_object_is_incomplete(self):
        self.assertIsNone(
            _complete_json_frame('{"activities": [{"id": "activity-one"}')
        )

    def test_ask_keeps_waiting_for_incomplete_unframed_json(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        response = self.Element(element_id="new-model-response")
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[], [response], [response]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch("app_generator.gemini.conversation.element_text", return_value='{"ok":'),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 2],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            with self.assertRaisesRegex(Exception, "complete parseable JSON"):
                self.page(driver).ask("prompt")

    def test_ask_fails_fast_when_non_json_response_stabilizes(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        response = self.Element(element_id="new-model-response")
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[], [response], [response]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch("app_generator.gemini.conversation.element_text", return_value="A prose reply"),
            patch("app_generator.gemini.conversation.NON_JSON_STABLE_POLLS", 1),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0.5],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            with self.assertRaisesRegex(Exception, "stabilized without complete parseable JSON"):
                self.page(driver).ask("prompt")

    def test_non_json_stability_survives_dom_element_replacement(self):
        driver = self.Driver()
        composer = self.Element()
        send = self.Element()
        first = self.Element(element_id="response-version-1")
        replacement = self.Element(element_id="response-version-2")
        with (
            patch(
                "app_generator.gemini.conversation.find_first",
                side_effect=[composer, send],
            ),
            patch(
                "app_generator.gemini.conversation.find_all",
                side_effect=[[], [first], [replacement]],
            ),
            patch("app_generator.gemini.conversation.replace_element_text"),
            patch("app_generator.gemini.conversation.element_text", return_value="Stable prose"),
            patch("app_generator.gemini.conversation.NON_JSON_STABLE_POLLS", 1),
            patch(
                "app_generator.gemini.conversation.time.monotonic",
                side_effect=[0, 0, 0.5],
            ),
            patch("app_generator.gemini.conversation.time.sleep"),
        ):
            with self.assertRaisesRegex(Exception, "stabilized without complete parseable JSON"):
                self.page(driver).ask("prompt")


if __name__ == "__main__":
    unittest.main()
