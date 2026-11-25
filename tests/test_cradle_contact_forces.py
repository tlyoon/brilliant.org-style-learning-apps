"""Synthetic adversarial finite-stiffness cradle and source-raster checks."""
from fractions import Fraction as F
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from app_generator.validation.cradle_contact_forces import (
    _forces,contact_chain_counterexample,
)
from app_generator.validation.cradle_original_figure import audit_cradle_original_figure


class CradleContactTests(unittest.TestCase):
    def test_simultaneous_compressive_forces_exact_static_equilibrium(self):
        for stiffness,compression in ((F(1),F(1,100)),
                                      (F(3),F(1,50)),
                                      (F(100),F(1,100))):
            with self.subTest(stiffness=stiffness):
                f1,f2=_forces((2*compression,compression,F(0)),stiffness)
                self.assertEqual(f1,f2)
                self.assertGreater(f1,0)
                r=contact_chain_counterexample(
                    stiffness=stiffness,compression=compression)
                self.assertTrue(r["staticTwoSimultaneousContactForces"])
                self.assertTrue(r["finiteStepOverlapObserved"])
                self.assertFalse(r["finiteStepIsExactContinuumTrajectory"])
                self.assertFalse(r["textbookAcademicPASS"])

    def test_zero_or_negative_contact_force_and_bad_inputs(self):
        self.assertEqual((F(0),F(0)),_forces((F(0),F(1),F(2)),F(1)))
        for params in ({"stiffness":F(0)},{"compression":F(-1)},
                       {"step":F(1)},{"step":0},
                       {"stiffness":F(10000)}):
            with self.subTest(params=params):
                with self.assertRaises(ValueError):
                    contact_chain_counterexample(**params)

    def test_raster_provenance_only_and_both_figure_labels(self):
        with TemporaryDirectory() as folder:
            src=Path(folder)/"original.pdf"
            src.write_bytes(b"%PDF-1.4 synthetic")
            body=" ".join(("Figure 9.9","Example 9.4","This can happen",
                           "This cannot happen","kinetic energy"))
            pages=["other text"]*4+[body]
            def render_ok(args,**kwargs):
                Path(args[-1]+".jpg").write_bytes(
                    b"\xff\xd8"+b"A"*12000+b"\xff\xd9")
                return SimpleNamespace(returncode=0,stdout=b"")
            with patch(
                "app_generator.validation.cradle_original_figure.extract_pages",
                return_value=pages,
            ),patch(
                "app_generator.validation.cradle_original_figure.subprocess.run",
                side_effect=render_ok,
            ) as render:
                report=audit_cradle_original_figure(src)
                self.assertEqual(5,report["physicalPdfPage"])
                self.assertTrue(report["diagramHasTwoDistinctLabeledOutcomes"])
                self.assertFalse(report["visualPhysicsMeaningMachineVerified"])
                self.assertFalse(report["externalSourceOrImageUploaded"])
                render.assert_called_once()

    def test_missing_source_label_and_bad_render_rejected(self):
        with TemporaryDirectory() as folder:
            src=Path(folder)/"source.pdf";src.write_bytes(b"%PDF-1.4 test")
            with patch(
                "app_generator.validation.cradle_original_figure.extract_pages",
                return_value=["page"]*5,
            ):
                with self.assertRaisesRegex(ValueError,"labels unlocated"):
                    audit_cradle_original_figure(src)
            body="Figure 9.9 Example 9.4 This can happen This cannot happen kinetic energy"
            with patch(
                "app_generator.validation.cradle_original_figure.extract_pages",
                return_value=["page"]*4+[body],
            ),patch(
                "app_generator.validation.cradle_original_figure.subprocess.run",
                return_value=SimpleNamespace(returncode=1,stdout=b""),
            ):
                with self.assertRaisesRegex(ValueError,"rendering failed"):
                    audit_cradle_original_figure(src)


if __name__=="__main__":
    unittest.main()
