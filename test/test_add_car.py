from fastapi.testclient import TestClient
from unittest.mock import Mock
from schemas import CarInput, User, Car
from cars import add_car
from main import app

client = TestClient(app)

# run pytest from terminal
def test_add_car():
    response = client.post("/api/cars/", json={
        "doors": 4,
        "size": "l",
    },headers={'Authorization': 'Bearer krassy'})
    print(response.content)
    assert response.status_code == 200
    car = response.json()
    assert car['doors'] == 4
    assert car['size'] == "l"

# unittest run simply running the file
def test_add_car_with_mock_session():
    mock_session = Mock()
    car = CarInput(doors=2, size="xl")
    user = User(username="krassy")
    result = add_car(car, session=mock_session, user=user)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert isinstance(result, Car)
    assert result.doors == 2
    assert result.size == "xl"