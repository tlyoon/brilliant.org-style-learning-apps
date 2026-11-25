import unittest
from app_generator.validation.collision_crosscheck import check_collision_witness

class CollisionCrosscheckTests(unittest.TestCase):
    def test_equal_mass_elastic_exchange(self):
        w=dict(collisionType="elastic",m1=1,m2=1,u1=2,u2=0,v1=0,v2=2)
        self.assertEqual("PASS",check_collision_witness(w,"numeric-case-1").result)
        w["v2"]=1
        self.assertEqual("FAIL",check_collision_witness(w,"numeric-case-1").result)

    def test_perfectly_inelastic_common_velocity(self):
        w=dict(collisionType="perfectly_inelastic",m1=1,m2=1,u1=2,u2=0,v1=1,v2=1)
        self.assertEqual("PASS",check_collision_witness(w,"numeric-case-2").result)
        w["v2"]=0
        self.assertEqual("FAIL",check_collision_witness(w,"numeric-case-2").result)

    def test_invalid_or_missing_witness_never_passes(self):
        self.assertEqual("REVIEW_REQUIRED",check_collision_witness(None,"missing").result)
        w=dict(collisionType="elastic",m1=-1,m2=1,u1=1,u2=0,v1=0,v2=1)
        self.assertEqual("REVIEW_REQUIRED",check_collision_witness(w,"invalid").result)
        w["m1"]=float("nan")
        self.assertEqual("REVIEW_REQUIRED",check_collision_witness(w,"invalid").result)
