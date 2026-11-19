"""BSA215: continuation top status follows latest executable recovery entry."""
import unittest
from scripts.check_regression_contract import _checkpoint_freshness_errors


class ContinuationCheckpointFreshnessTests(unittest.TestCase):
    def test_latest_registry_id_and_status_at_top_passes(self):
        entries=[{"id":"BSA-20261118-215","status":"resolved"}]
        checkpoint=("# Latest Continuation Checkpoint\n"
                    "> CURRENT RECOVERY CHECKPOINT: BSA-20261118-215 | RESOLVED\n"
                    "\nHistorical BSA-20261118-214 active text can remain below.\n")
        self.assertEqual(_checkpoint_freshness_errors(checkpoint,entries),[])

    def test_historical_active_header_without_new_closure_fails_closed(self):
        entries=[{"id":"BSA-20261118-214","status":"resolved"},
                 {"id":"BSA-20261118-215","status":"resolved"}]
        checkpoint=("# Latest Continuation Checkpoint\n"
                    "> **BSA214 ACTIVE** some old details\n"
                    "\n# audit historical.\n"
                    "> CURRENT RECOVERY CHECKPOINT: BSA-20261118-214 | RESOLVED\n")
        result=_checkpoint_freshness_errors(checkpoint,entries)
        self.assertEqual(len(result),1)
        self.assertIn("disagree",result[0])

    def test_latest_status_transition_must_refresh_top_marker(self):
        entries=[{"id":"BSA-20261118-215","status":"active"}]
        checkpoint=("# Latest Continuation Checkpoint\n"
                    "> CURRENT RECOVERY CHECKPOINT: BSA-20261118-215 | RESOLVED\n")
        self.assertTrue(_checkpoint_freshness_errors(checkpoint,entries))


if __name__=="__main__":
    unittest.main()
