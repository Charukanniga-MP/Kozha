import unittest
import sys
from pathlib import Path

# Add server and backend/dellar to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_DIR = REPO_ROOT / "server"
DELLAR_DIR = REPO_ROOT / "backend" / "dellar"
DELLAR_SRC = DELLAR_DIR / "src"

for p in [str(SERVER_DIR), str(DELLAR_DIR), str(DELLAR_SRC)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dellar_service import DellarServiceManager


class TestDellarIntegration(unittest.TestCase):
    def setUp(self):
        self.service = DellarServiceManager()

    def test_session_lifecycle(self):
        session_id = "user_test_1"
        # Initial status should be OFF
        status_before = self.service.get_status(session_id)
        self.assertEqual(status_before["status"], "OFF")

        # Start session -> status should be RUNNING
        status_start = self.service.start_session(session_id)
        self.assertEqual(status_start["status"], "RUNNING")

        # Stop session -> status should be OFF
        status_stop = self.service.stop_session(session_id)
        self.assertEqual(status_stop["status"], "OFF")

    def test_sign_to_speech_processing(self):
        session_id = "user_test_2"
        self.service.start_session(session_id)

        res = self.service.process_sign(session_id)
        self.assertEqual(res["status"], "RUNNING")
        self.assertIn("latency_ms", res)
        self.assertIn("active_entities", res)
        self.assertIn("entities", res)
        self.assertIsInstance(res["entities"], list)

        self.service.stop_session(session_id)

    def test_speech_to_sign_processing(self):
        session_id = "user_test_3"
        self.service.start_session(session_id)

        res = self.service.process_speech(session_id)
        self.assertEqual(res["status"], "RUNNING")
        self.assertIn("pose_trajectory_shape", res)
        self.assertEqual(res["pose_trajectory_shape"], [1, 50, 25, 3])

        self.service.stop_session(session_id)

    def test_user_isolation(self):
        user_a = "user_alice"
        user_b = "user_bob"

        # Start user A DELLAR session
        self.service.start_session(user_a)
        status_a = self.service.get_status(user_a)
        self.assertEqual(status_a["status"], "RUNNING")

        # User B DELLAR session remains OFF
        status_b = self.service.get_status(user_b)
        self.assertEqual(status_b["status"], "OFF")

        # Process user A frame
        res_a = self.service.process_sign(user_a)
        self.assertEqual(res_a["status"], "RUNNING")

        # Clean up
        self.service.stop_session(user_a)


if __name__ == "__main__":
    unittest.main()
