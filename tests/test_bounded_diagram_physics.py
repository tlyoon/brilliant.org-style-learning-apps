"""Synthetic adversarial cart and spring physics visualization checks."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.bounded_diagram_physics import (
    _CART_CASES, _ENERGY_CASE, check_bounded_diagram_physics,
    audit_source_bound_diagram_physics,
)


def cart(aid):
    masses,vectors=_CART_CASES[aid]
    return {"id":aid,"visualSpec":{
        "template":"mechanics.cart_collision_1d",
        "semanticParameters":{"phase":"before","track_orientation":"horizontal"},
        "entities":[{"id":f"cart-{i+1}","kind":"cart",
                     "properties":{"mass":masses[i]}} for i in range(2)],
        "vectors":[{"entityId":eid,"direction":direction,
                    "quantity":"velocity","relativeMagnitude":0.7}
                   for eid,direction in vectors],
    }}


def spring():
    return {"id":_ENERGY_CASE,"visualSpec":{
        "template":"state.energy_bar",
        "entities":[{"id":name,"kind":"energy-component",
                     "properties":{"relativeAmount":fraction}}
                    for name,fraction in (("kinetic",0.6),("elastic",0.4))],
        "states":[{"id":"initial-state","values":{"kinetic":1.0,"elastic":0.0}},
                  {"id":"intermediate-state","values":{"kinetic":0.6,"elastic":0.4}}],
        "invariants":[{"kind":"conserved","references":["kinetic","elastic"]}],
    }}


class DiagramPhysicsInvariantTests(unittest.TestCase):
    def test_four_original_cart_models_only_before_collision(self):
        for aid in _CART_CASES:
            with self.subTest(activity=aid):
                r=check_bounded_diagram_physics(cart(aid))
                self.assertTrue(r["beforeCollisionVerified"])
                self.assertFalse(r["postImpactOutcomesVerified"])
                self.assertFalse(r["scientificVisualSemanticsVerified"])

    def test_reversed_arrow_cannot_pass(self):
        x=cart("mcq-equal-mass-elastic-transfer")
        x["visualSpec"]["vectors"][0]["direction"]="left"
        with self.assertRaisesRegex(ValueError,"arrows"):
            check_bounded_diagram_physics(x)

    def test_extra_stationary_target_arrow_cannot_pass(self):
        x=cart("mcq-perfectly-inelastic-outcome")
        x["visualSpec"]["vectors"].append({
            "entityId":"cart-2","direction":"left","quantity":"velocity",
            "relativeMagnitude":0.7})
        with self.assertRaisesRegex(ValueError,"roster altered"):
            check_bounded_diagram_physics(x)

    def test_incorrect_mass_phase_or_velocity_quantity_block(self):
        x=cart("mcq-extreme-mass-heavy-target")
        x["visualSpec"]["entities"][1]["properties"]["mass"]="m"
        with self.assertRaisesRegex(ValueError,"mass labels"):
            check_bounded_diagram_physics(x)
        x=cart("mcq-collision-types-concept")
        x["visualSpec"]["semanticParameters"]["phase"]="after"
        with self.assertRaisesRegex(ValueError,"preimpact"):
            check_bounded_diagram_physics(x)
        x=cart("mcq-collision-types-concept")
        x["visualSpec"]["vectors"][0]["quantity"]="force"
        with self.assertRaisesRegex(ValueError,"velocity"):
            check_bounded_diagram_physics(x)

    def test_energy_bar_exact_conservation_and_positive_partition(self):
        r=check_bounded_diagram_physics(spring())
        self.assertEqual("1",r["intermediateEnergySum"])
        self.assertFalse(r["collisionEnergyLawVerified"])
        x=spring()
        x["visualSpec"]["states"][1]["values"]["kinetic"]=0.5
        with self.assertRaisesRegex(ValueError,"not conserved"):
            check_bounded_diagram_physics(x)
        x=spring()
        x["visualSpec"]["entities"][1]["properties"]["relativeAmount"]=0.5
        with self.assertRaisesRegex(ValueError,"differ"):
            check_bounded_diagram_physics(x)

    def test_nan_vector_and_energy_values_rejected(self):
        x=cart("mcq-equal-mass-elastic-transfer")
        x["visualSpec"]["vectors"][0]["relativeMagnitude"]=float("nan")
        with self.assertRaisesRegex(ValueError,"finite"):
            check_bounded_diagram_physics(x)
        x=spring()
        x["visualSpec"]["states"][1]["values"]["kinetic"]=True
        with self.assertRaisesRegex(ValueError,"finite"):
            check_bounded_diagram_physics(x)

    def test_complete_source_bound_package_has_only_bounded_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            file=root/"package.json"
            activities=[cart(aid) for aid in _CART_CASES]+[spring()]
            activities += [{"id":f"nonvisual-{i}"} for i in range(13)]
            file.write_text(json.dumps({"activities":activities}),encoding="utf-8")
            pdf=root/"source.pdf";pdf.write_bytes(b"%PDF-1.4 synthetic")
            packets=root/"packets.json";packets.write_text("{}")
            report={"newlyReverifiedSourceActivities":18,
                    "publicationAuthorized":False,"visualSemanticsVerified":False,
                    "packageSha256":sha256(file.read_bytes()).hexdigest(),
                    "sourceSha256":sha256(pdf.read_bytes()).hexdigest()}
            with patch(
                "app_generator.validation.bounded_diagram_physics.verify_full_source_packet_roster",
                return_value=report,
            ) as verified:
                result=audit_source_bound_diagram_physics(
                    package_file=file,source_pdf=pdf,packets_file=packets)
                verified.assert_called_once()
            self.assertEqual(5,result["boundedDiagramActivitiesChecked"])
            self.assertEqual(4,result["cartInitialConfigurationsChecked"])
            self.assertFalse(result["allRenderedScientificSemanticsVerified"])
            self.assertEqual(0,result["formalAcademicPASS"])
            self.assertFalse(result["publicationAuthorized"])
            # An otherwise visually plausible wrong arrow cannot be accepted.
            activities[0]["visualSpec"]["vectors"][0]["direction"]="left"
            file.write_text(json.dumps({"activities":activities}),encoding="utf-8")
            report["packageSha256"]=sha256(file.read_bytes()).hexdigest()
            with patch(
                "app_generator.validation.bounded_diagram_physics.verify_full_source_packet_roster",
                return_value=report,
            ):
                with self.assertRaisesRegex(ValueError,"arrows"):
                    audit_source_bound_diagram_physics(
                        package_file=file,source_pdf=pdf,packets_file=packets)


if __name__ == "__main__":
    unittest.main()
