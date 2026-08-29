import unittest
from dataclasses import dataclass

from app_generator.errors import ResponseContractError
from app_generator.generation.metadata import apply_source_metadata, materialize_source_metadata


@dataclass(frozen=True)
class Config:
    pdf_subchapter_path: str = "8.3"
    subchapter: str = "8.3"
    heading: str = "8.3"
    learning_boundary: str = "Controlled PDF boundary"
    page_range: str = "Complete controlled PDF for section 8.3"


class GeneratorMetadataTests(unittest.TestCase):
    def analysis(self):
        return {
            "sectionTitle": "Section 8.3 Conceptual Energy Transfers",
            "scopeNotes": {
                "includedConcepts": ["energy transfer pathways", "system boundaries"],
                "excludedConcepts": ["material from later sections"],
            },
        }

    def test_materializes_exact_pdf_title_and_scope(self):
        config = materialize_source_metadata(Config(), self.analysis())
        self.assertEqual("8.3 Conceptual Energy Transfers", config.subchapter)
        self.assertEqual(config.subchapter, config.heading)
        self.assertIn("energy transfer pathways", config.learning_boundary)
        self.assertIn("material from later sections", config.learning_boundary)

    def test_rejects_analysis_without_a_title_beyond_the_section_number(self):
        analysis = self.analysis()
        analysis["sectionTitle"] = "Section 8.3"
        with self.assertRaises(ResponseContractError):
            materialize_source_metadata(Config(), analysis)

    def test_rewrites_python_owned_package_provenance(self):
        config = materialize_source_metadata(Config(), self.analysis())
        package = {
            "subchapter": "8.3",
            "activities": [{"provenance": {"sourceLocation": "old", "originalContent": True}}],
        }
        updated = apply_source_metadata(package, config)
        self.assertEqual(config.subchapter, updated["subchapter"])
        self.assertEqual(
            f"{config.heading}; {config.page_range}",
            updated["activities"][0]["provenance"]["sourceLocation"],
        )
        self.assertEqual("old", package["activities"][0]["provenance"]["sourceLocation"])


if __name__ == "__main__":
    unittest.main()
