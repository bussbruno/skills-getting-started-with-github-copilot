"""Tests for the FastAPI application using AAA (Arrange-Act-Assert) pattern"""

import pytest


class TestGetRoot:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        # Arrange
        expected_redirect_url = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect_url


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_returns_list(self, client):
        # Arrange
        activity_names = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Swimming Club", "Art Studio", "Drama Club", "Debate Team", "Science Club"
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 9
        for activity_name in activity_names:
            assert activity_name in activities

    def test_get_activities_response_structure(self, client):
        # Arrange
        expected_keys = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert set(activity_data.keys()) == expected_keys
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client):
        # Arrange
        activity_name = "Basketball Team"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify student was added to participants
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants

    def test_signup_activity_not_found(self, client):
        # Arrange
        activity_name = "Non-existent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_multiple_students(self, client):
        # Arrange
        activity_name = "Swimming Club"
        students = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu"
        ]

        # Act
        for email in students:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Assert
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        for email in students:
            assert email in participants
        assert len(participants) == 3


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        
        # Verify student was removed from participants
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email not in participants

    def test_unregister_activity_not_found(self, client):
        # Arrange
        activity_name = "Non-existent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_student_not_signed_up(self, client):
        # Arrange
        activity_name = "Basketball Team"
        email = "notstudent@mergington.edu"  # Not signed up

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_and_signup_again(self, client):
        # Arrange
        activity_name = "Gym Class"
        email = "test@mergington.edu"

        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200

        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200

        # Act - Sign up again
        signup_again_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert signup_again_response.status_code == 200
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants
