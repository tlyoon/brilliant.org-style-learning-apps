"""High-level Gemini session coordinating Gem setup, model choice, and chat."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app_generator.browser.account import GoogleAccountVerifier
from app_generator.config import GeneratorConfig
from app_generator.errors import UiContractError
from app_generator.gemini.conversation import GemConversationPage
from app_generator.gemini.editor import GemEditorPage
from app_generator.gemini.models import ModelFailure, ModelOption, classify_model_failure, rank_models
from app_generator.prompts import gem_description, gem_instructions

LOGGER = logging.getLogger("app_generator.gemini")


class GeminiClient:
    def __init__(self, driver: Any, config: GeneratorConfig) -> None:
        self.driver = driver
        self.config = config
        self.editor = GemEditorPage(driver, config.gem_url, config.gem_edit_url, config.ui_timeout_seconds)
        self.conversation = GemConversationPage(
            driver, config.gem_url, config.ui_timeout_seconds, config.response_timeout_seconds
        )
        self.ranked_models: list[ModelOption] = []
        self.model_index = 0

    @property
    def actual_model(self) -> str:
        return self.ranked_models[self.model_index].label

    def open_editor_and_verify_account(self) -> None:
        self.editor.navigate()
        GoogleAccountVerifier(self.driver, self.config.login_name, self.config.login_timeout_seconds).verify()
        self.editor.enter_editor()

    def configure_gem(self) -> None:
        self.editor.verify_identity(self.config.gem_name)
        self.editor.initialize_configuration(gem_description(), gem_instructions())

    def open_conversation_select_model_and_attach(self, source_path: Path) -> str:
        self.conversation.open_new()
        model_selected_in_ui = False
        try:
            discovered = self.conversation.discover_models()
            self.ranked_models = rank_models(
                discovered,
                self.config.model_preference_patterns,
                allow_unknown_fallback=self.config.allow_unknown_model_fallback,
            )
            model_selected_in_ui = True
        except UiContractError as exc:
            if not self.config.allow_unknown_model_fallback:
                raise
            self.ranked_models = [
                ModelOption(
                    "Gem default (model selector unavailable)",
                    "Gemini did not expose a model picker; using the Gem's current/default model.",
                    selected=True,
                )
            ]
            LOGGER.warning("Gemini model picker unavailable; using the Gem default model: %s", exc)
        self.model_index = 0
        if model_selected_in_ui:
            self.conversation.select_model(self.actual_model)
        self.conversation.attach_pdf(source_path)
        LOGGER.info("Selected Gemini model and attached claimed source", extra={"model": self.actual_model})
        return self.actual_model

    def ask(self, prompt: str) -> str:
        while True:
            try:
                response = self.conversation.ask(prompt)
            except Exception as exc:
                failure = classify_model_failure(str(exc))
                if failure.permits_model_fallback and self.model_index + 1 < len(self.ranked_models):
                    self.select_next_model()
                    continue
                raise
            failure = (
                ModelFailure.UNKNOWN
                if "BEGIN_JSON" in response and "END_JSON" in response
                else classify_model_failure(response)
            )
            if failure.permits_model_fallback and self.model_index + 1 < len(self.ranked_models):
                self.select_next_model()
                continue
            if failure in {ModelFailure.OUTPUT_TRUNCATED, ModelFailure.CONTEXT_LIMIT, ModelFailure.RESPONSE_SIZE}:
                LOGGER.error("Generation response hit an output-size limit; model was not downgraded")
            return response

    def select_next_model(self) -> str:
        if self.model_index + 1 >= len(self.ranked_models):
            raise RuntimeError("No lower-ranked configured Gemini model remains")
        previous = self.actual_model
        self.model_index += 1
        self.conversation.select_model(self.actual_model)
        LOGGER.warning("Fell back to another Gemini model: %s -> %s", previous, self.actual_model)
        return self.actual_model
