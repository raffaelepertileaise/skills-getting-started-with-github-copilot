import unittest
from copy import deepcopy
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        state = patch.dict(activities, deepcopy(activities), clear=True)
        state.start()
        self.addCleanup(state.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_unregister_updates_activity_and_allows_signup_again(self):
        email = activities["Chess Club"]["participants"][0]
        before = activities["Chess Club"]["participants"].copy()

        response = self.client.delete(
            "/activities/Chess%20Club/unregister", params={"email": email}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(email, response.json()["message"])
        updated = self.client.get("/activities").json()
        self.assertEqual(updated["Chess Club"]["participants"], before[1:])
        self.assertEqual(
            self.client.post(
                "/activities/Chess%20Club/signup", params={"email": email}
            ).status_code,
            200,
        )

    def test_unregister_unknown_activity_does_not_change_data(self):
        before = deepcopy(activities)
        response = self.client.delete(
            "/activities/Unknown/unregister", params={"email": "student@example.com"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Activity not found")
        self.assertEqual(activities, before)

    def test_unregister_missing_participant_does_not_change_data(self):
        before = deepcopy(activities)
        response = self.client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "missing@example.com"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"], "Student is not signed up for this activity"
        )
        self.assertEqual(activities, before)
