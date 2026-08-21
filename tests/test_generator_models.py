import unittest

from app_generator.gemini.models import ModelFailure, ModelOption, classify_model_failure, rank_models


class GeneratorModelTests(unittest.TestCase):
    def test_semantic_model_ranking_is_not_tied_to_one_exact_label(self):
        models = [
            ModelOption("Gemini Flash Next", "Fast", ui_index=0),
            ModelOption("Gemini Advanced", "Most capable reasoning", ui_index=1),
            ModelOption("Mystery Model", selected=True, ui_index=2),
        ]
        ranked = rank_models(models, [r"pro|most capable", r"advanced", r"flash|fast"], allow_unknown_fallback=True)
        self.assertEqual(["Gemini Advanced", "Gemini Flash Next", "Mystery Model"], [item.label for item in ranked])

    def test_fallback_errors_are_distinct_from_output_limits(self):
        self.assertTrue(classify_model_failure("Quota exhausted").permits_model_fallback)
        self.assertEqual(ModelFailure.OUTPUT_TRUNCATED, classify_model_failure("Output was truncated"))
        self.assertFalse(classify_model_failure("Output was truncated").permits_model_fallback)


if __name__ == "__main__":
    unittest.main()
