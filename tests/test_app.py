from copy import deepcopy

import pytest


def test_root_redirects_to_activity_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_activity_page_is_served(client):
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Mergington High School" in response.text


def test_get_activities_includes_details_and_empty_participants(client, activity_data):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activity_data


def test_signup_is_immediately_visible_and_preserves_other_data(client, activity_data):
    expected = deepcopy(activity_data)
    email = "new+student@mergington.edu"
    expected["Chess Club"]["participants"].append(email)

    response = client.post(
        "/activities/Chess%20Club/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert client.get("/activities").json() == expected


@pytest.mark.parametrize(
    "method,path,email,status,detail",
    [
        (
            "POST",
            "/activities/Chess%20Club/signup",
            "michael@mergington.edu",
            400,
            "Student already signed up for this activity",
        ),
        (
            "POST",
            "/activities/Unknown/signup",
            "student@mergington.edu",
            404,
            "Activity not found",
        ),
        (
            "DELETE",
            "/activities/Unknown/unregister",
            "student@mergington.edu",
            404,
            "Activity not found",
        ),
        (
            "DELETE",
            "/activities/Chess%20Club/unregister",
            "missing@mergington.edu",
            404,
            "Student is not signed up for this activity",
        ),
    ],
)
def test_rejected_registration_changes_leave_data_unchanged(
    client, activity_data, method, path, email, status, detail
):
    before = deepcopy(activity_data)

    response = client.request(method, path, params={"email": email})

    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert client.get("/activities").json() == before


def test_unregister_is_immediately_visible_and_allows_signup_again(client, activity_data):
    before = deepcopy(activity_data)
    email = before["Chess Club"]["participants"][0]
    expected = deepcopy(before)
    expected["Chess Club"]["participants"].remove(email)

    response = client.delete(
        "/activities/Chess%20Club/unregister", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert client.get("/activities").json() == expected

    response = client.post(
        "/activities/Chess%20Club/signup", params={"email": email}
    )

    assert response.status_code == 200
    expected["Chess Club"]["participants"].append(email)
    assert client.get("/activities").json() == expected


def test_repeated_unregister_does_not_remove_other_participants(client, activity_data):
    email = activity_data["Chess Club"]["participants"][0]
    path = "/activities/Chess%20Club/unregister"
    assert client.delete(path, params={"email": email}).status_code == 200
    expected = deepcopy(activity_data)

    response = client.delete(path, params={"email": email})

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert client.get("/activities").json() == expected


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/activities/Chess%20Club/signup"),
        ("DELETE", "/activities/Chess%20Club/unregister"),
    ],
)
def test_registration_requires_email(client, activity_data, method, path):
    before = deepcopy(activity_data)

    response = client.request(method, path)

    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"] and error["type"] == "missing"
        for error in response.json()["detail"]
    )
    assert client.get("/activities").json() == before
