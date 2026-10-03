import math
import unittest

from app_generator.visuals.models import evaluate_motion_1d


class Motion1DModelTests(unittest.TestCase):
    def test_constant_velocity_nominal_and_sign_cases(self):
        self.assertEqual(6.0, evaluate_motion_1d(0, 3, 2).position)
        self.assertEqual(-6.0, evaluate_motion_1d(0, -3, 2).position)
        self.assertEqual(5.0, evaluate_motion_1d(5, 0, 9).position)

    def test_initial_state_and_velocity_are_preserved(self):
        state = evaluate_motion_1d(4, 2.5, 0)
        self.assertEqual(4.0, state.position)
        self.assertEqual(2.5, state.velocity)
        self.assertEqual(0.0, state.time)

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            evaluate_motion_1d(0, 1, -1)
        with self.assertRaises(ValueError):
            evaluate_motion_1d(0, math.inf, 1)


if __name__ == "__main__":
    unittest.main()
