"""
Tests for Mergington High School Activities API.

Uses the Arrange-Act-Assert (AAA) pattern for clarity:
- Arrange: Set up test data and fixtures
- Act: Call the API endpoint
- Assert: Verify the response and state changes
"""

import pytest


# ============================================================================
# Root Endpoint Tests
# ============================================================================

class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """
        Arrange: Request the root endpoint
        Act: Make GET request to "/"
        Assert: Verify redirect to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ============================================================================
# Get Activities Endpoint Tests
# ============================================================================

class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_returns_dict(self, client):
        """
        Arrange: N/A
        Act: Make GET request to /activities
        Assert: Response is 200 and contains dict of activities
        """
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9

    def test_get_activities_contains_all_expected_activities(self, client):
        """
        Arrange: N/A
        Act: Get all activities
        Assert: All 9 activities are present
        """
        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        expected_names = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Swimming Club", "Art Studio",
            "Drama Club", "Debate Team", "Science Club"
        ]
        for activity_name in expected_names:
            assert activity_name in activities

    def test_each_activity_has_required_fields(self, client):
        """
        Arrange: N/A
        Act: Get all activities
        Assert: Each activity has required structure
        """
        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Missing '{field}' in {activity_name}"
            assert isinstance(activity_data["participants"], list)

    def test_activities_have_correct_initial_participants(self, client):
        """
        Arrange: N/A
        Act: Get all activities
        Assert: Initial participants match expected values
        """
        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]
        assert len(activities["Basketball Team"]["participants"]) == 0


# ============================================================================
# Signup Endpoint Tests - Happy Path
# ============================================================================

class TestSignupHappyPath:
    """Tests for successful signup scenarios"""

    def test_signup_new_student_to_empty_activity(self, client):
        """
        Arrange: Basketball Team has no participants
        Act: Sign up new student
        Assert: Signup succeeds and returns success message
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Basketball Team"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_signup_updates_participant_list(self, client):
        """
        Arrange: Get initial participants count
        Act: Sign up new student
        Assert: Participant is added to activity list
        """
        # Arrange
        email = "swimmer@mergington.edu"
        activity = "Swimming Club"
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])

        # Act
        client.post(f"/activities/{activity}/signup", params={"email": email})

        # Assert
        response = client.get("/activities")
        final_count = len(response.json()[activity]["participants"])
        assert final_count == initial_count + 1
        assert email in response.json()[activity]["participants"]

    def test_signup_multiple_students_to_same_activity(self, client):
        """
        Arrange: Activity with no participants
        Act: Sign up multiple students
        Assert: All are added successfully
        """
        # Arrange
        activity = "Drama Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]

        # Act
        for email in emails:
            response = client.post(f"/activities/{activity}/signup", params={"email": email})
            assert response.status_code == 200

        # Assert
        response = client.get("/activities")
        for email in emails:
            assert email in response.json()[activity]["participants"]


# ============================================================================
# Signup Endpoint Tests - Error Cases
# ============================================================================

class TestSignupErrorCases:
    """Tests for signup error scenarios"""

    def test_signup_activity_not_found(self, client):
        """
        Arrange: Non-existent activity name
        Act: Try to sign up for non-existent activity
        Assert: Returns 404 with appropriate error message
        """
        # Act
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_rejected(self, client):
        """
        Arrange: Student already signed up for activity
        Act: Try to sign up again with same email
        Assert: Returns 400 with duplicate error
        """
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity}/signup", params={"email": email})

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_missing_email_parameter(self, client):
        """
        Arrange: No email parameter provided
        Act: Make signup request without email
        Assert: Returns 422 validation error
        """
        # Act
        response = client.post("/activities/Chess Club/signup")

        # Assert
        assert response.status_code == 422


# ============================================================================
# Unregister Endpoint Tests - Happy Path
# ============================================================================

class TestUnregisterHappyPath:
    """Tests for successful unregister scenarios"""

    def test_unregister_existing_participant(self, client):
        """
        Arrange: Student is signed up for activity
        Act: Unregister the student
        Assert: Unregister succeeds and returns success message
        """
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
        assert email in data["message"]

    def test_unregister_removes_participant_from_list(self, client):
        """
        Arrange: Student is in participant list
        Act: Unregister the student
        Assert: Student is removed from participant list
        """
        # Arrange
        email = "emma@mergington.edu"
        activity = "Programming Class"
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]

        # Act
        client.post(f"/activities/{activity}/unregister", params={"email": email})

        # Assert
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_unregister_student_can_signup_again(self, client):
        """
        Arrange: Student signs up, then unregisters
        Act: Student signs up again
        Assert: Second signup succeeds
        """
        # Arrange
        email = "reregister@mergington.edu"
        activity = "Art Studio"

        # Act - First signup
        response1 = client.post(f"/activities/{activity}/signup", params={"email": email})
        assert response1.status_code == 200

        # Act - Unregister
        client.post(f"/activities/{activity}/unregister", params={"email": email})

        # Act - Sign up again
        response2 = client.post(f"/activities/{activity}/signup", params={"email": email})

        # Assert
        assert response2.status_code == 200


# ============================================================================
# Unregister Endpoint Tests - Error Cases
# ============================================================================

class TestUnregisterErrorCases:
    """Tests for unregister error scenarios"""

    def test_unregister_activity_not_found(self, client):
        """
        Arrange: Non-existent activity name
        Act: Try to unregister from non-existent activity
        Assert: Returns 404
        """
        # Act
        response = client.post(
            "/activities/Fake Activity/unregister",
            params={"email": "student@mergington.edu"}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_signed_up(self, client):
        """
        Arrange: Student is not signed up for activity
        Act: Try to unregister student who isn't signed up
        Assert: Returns 400 with appropriate error
        """
        # Act
        response = client.post(
            "/activities/Science Club/unregister",
            params={"email": "notsignup@mergington.edu"}
        )

        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_missing_email_parameter(self, client):
        """
        Arrange: No email parameter provided
        Act: Make unregister request without email
        Assert: Returns 422 validation error
        """
        # Act
        response = client.post("/activities/Chess Club/unregister")

        # Assert
        assert response.status_code == 422


# ============================================================================
# Integration Tests - Multi-Step Workflows
# ============================================================================

class TestIntegrationWorkflows:
    """Tests combining multiple endpoints in realistic workflows"""

    def test_signup_view_and_unregister_workflow(self, client):
        """
        Arrange: N/A
        Act: 1) Sign up for activity, 2) View activities, 3) Unregister
        Assert: All steps succeed and state changes correctly
        """
        # Arrange
        email = "workflow@mergington.edu"
        activity = "Debate Team"

        # Act 1 - Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert 1
        assert signup_response.status_code == 200

        # Act 2 - View activities and verify participant added
        view_response = client.get("/activities")
        activities_data = view_response.json()

        # Assert 2
        assert email in activities_data[activity]["participants"]

        # Act 3 - Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert 3
        assert unregister_response.status_code == 200

        # Act 4 - Verify removal
        final_view = client.get("/activities")
        assert email not in final_view.json()[activity]["participants"]

    def test_multiple_participants_in_same_activity(self, client):
        """
        Arrange: N/A
        Act: Multiple students sign up for same activity
        Assert: All are properly listed
        """
        # Arrange
        activity = "Science Club"
        students = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu"
        ]

        # Act - All sign up
        for email in students:
            response = client.post(f"/activities/{activity}/signup", params={"email": email})
            assert response.status_code == 200

        # Assert - All are in list
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in students:
            assert email in participants

    def test_student_signs_up_for_multiple_activities(self, client):
        """
        Arrange: N/A
        Act: One student signs up for multiple activities
        Assert: Student appears in all activity lists
        """
        # Arrange
        email = "multiactivity@mergington.edu"
        activities_to_join = ["Art Studio", "Drama Club", "Science Club"]

        # Act
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup", params={"email": email})
            assert response.status_code == 200

        # Assert
        response = client.get("/activities")
        activities_data = response.json()
        for activity in activities_to_join:
            assert email in activities_data[activity]["participants"]
