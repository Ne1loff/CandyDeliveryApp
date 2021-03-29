from fastapi.testclient import TestClient
from datetime import datetime
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_create_couriers_validation_error():
    response = client.post(
        "/couriers",
        json={
            "data": [
                {
                    "courier_id": 1,
                    "courier_type": "32type",
                    "regions": [
                        1,
                        12,
                        22
                    ],
                    "working_hours": [
                        "11:35-14:05",
                        "09:00-11:00"
                    ]
                },
                {
                    "courier_id": 2,
                    "courier_type": "bike",
                    "regions": [
                        22
                    ],
                    "working_hours": [
                        "09:00-18:00"
                    ]
                },
                {
                    "courier_id": 3,
                    "courier_type": "car",
                    "regions": [
                        12,
                        22,
                        23,
                        33
                    ],
                    "working_hours": "something"
                }
            ]
        }
    )
    assert response.status_code == 400
    assert response.json() == {
        "validation_error": {
            "couriers": [
                {
                    "id": 1
                },
                {
                    "id": 3
                }
            ]
        }
    }


def test_create_couriers():
    response = client.post(
        "/couriers",
        json={
            "data": [
                {
                    "courier_id": 1,
                    "courier_type": "foot",
                    "regions": [
                        1,
                        12,
                        22
                    ],
                    "working_hours": [
                        "11:35-14:05",
                        "09:00-11:00"
                    ]
                },
                {
                    "courier_id": 2,
                    "courier_type": "bike",
                    "regions": [
                        22
                    ],
                    "working_hours": [
                        "09:00-18:00"
                    ]
                },
                {
                    "courier_id": 3,
                    "courier_type": "car",
                    "regions": [
                        12,
                        22,
                        23,
                        33
                    ],
                    "working_hours": []
                }
            ]
        }
    )
    assert response.status_code == 201
    assert response.json() == {
        "couriers": [
            {
                "id": 1
            },
            {
                "id": 2
            },
            {
                "id": 3
            }
        ]
    }


def test_create_orders_validation_error():
    response = client.post(
        "/orders",
        json={
            "data": [
                {
                    "order_id": 1,
                    "weight": 0.45,
                    "region": 12,
                    "delivery_hours": [
                        "09:00-18:00"
                    ]
                },
                {
                    "order_id": 2,
                    "weight": 50.03,
                    "region": 1,
                    "delivery_hours": [
                        "09:00-18:00"
                    ]
                },
                {
                    "order_id": 3,
                    "weight": 0.23,
                    "region": "22region",
                    "delivery_hours": [
                        "09:00-12:00",
                        "16:00-21:30"
                    ]
                }
            ]
        }
    )
    assert response.status_code == 400
    assert response.json() == {
        "validation_error": {
            "orders": [
                {
                    "id": 2
                },
                {
                    "id": 3
                }
            ]
        }
    }


def test_create_orders():
    response = client.post(
        "/orders",
        json={
            "data": [
                {
                    "order_id": 1,
                    "weight": 0.45,
                    "region": 12,
                    "delivery_hours": [
                        "09:00-18:00"
                    ]
                },
                {
                    "order_id": 2,
                    "weight": 50,
                    "region": 1,
                    "delivery_hours": [
                        "09:00-18:00"
                    ]
                },
                {
                    "order_id": 3,
                    "weight": 0.23,
                    "region": 22,
                    "delivery_hours": [
                        "09:00-12:00",
                        "16:00-21:30"
                    ]
                }
            ]
        }
    )
    assert response.status_code == 201
    assert response.json() == {
        "orders": [
            {
                "id": 1
            },
            {
                "id": 2
            },
            {
                "id": 3
            }
        ]
    }


def test_get_courier_by_id():
    response = client.get("/couriers/1")
    assert response.status_code == 200
    assert response.json() == {
        "courier_id": 1,
        "courier_type": "foot",
        "regions": [
            1,
            12,
            22
        ],
        "working_hours": [
            "11:35-14:05",
            "09:00-11:00"
        ],
        "earning": 0
    }


def test_assign_order_for_courier_2():
    response = client.post(
        "/orders/assign",
        json={
            "courier_id": 2
        }
    )
    assert response.status_code == 200
    time_re = re.compile(
        r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])'
        r'T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$')
    assert time_re.match(response.json()["assign_time"])
    assert response.json()["orders"] == [{"id": 3}]


def test_assign_order_for_courier_1():
    response = client.post(
        "/orders/assign",
        json={
            "courier_id": 1
        }
    )
    assert response.status_code == 200
    time_re = re.compile(
        r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])'
        r'T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$')
    assert time_re.match(response.json()["assign_time"])
    assert response.json()["orders"] == [{"id": 1}]


def test_patch_courier_2():
    response = client.patch(
        "/couriers/2",
        json={
            "regions": [13, 2, 1, 23],
            "working_hours": ["03:20-04:40", "05:00-06:30", "09:00-12:00"]
        }
    )
    assert response.status_code == 200
    assert response.json() == {
        "courier_id": 2,
        "courier_type": "bike",
        "regions": [
            13,
            2,
            1,
            23
        ],
        "working_hours": [
            "03:20-04:40",
            "05:00-06:30",
            "09:00-12:00"
        ]
    }


def test_assign_order_for_courier_2_again():
    response = client.post(
        "/orders/assign",
        json={
            "courier_id": 2
        }
    )
    assert response.status_code == 200
    assert response.json()["orders"] == []


def test_assign_order_for_courier_1_again():
    response = client.post(
        "/orders/assign",
        json={
            "courier_id": 1
        }
    )
    assert response.status_code == 200
    time_re = re.compile(
        r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])'
        r'T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$')
    assert time_re.match(response.json()["assign_time"])
    assert response.json()["orders"] == [{"id": 1}, {"id": 3}]


def test_complete_order_1_for_courier_1():
    complete_time = datetime.now().isoformat()
    response = client.post(
        "/orders/complete",
        json={
            "courier_id": 1,
            "order_id": 3,
            "complete_time": complete_time
        }
    )
    assert response.status_code == 200
    assert response.json() == {
        "order_id": 3
    }


def test_assign_order_for_courier_1_again_2():
    response = client.post(
        "/orders/assign",
        json={
            "courier_id": 1
        }
    )
    assert response.status_code == 200
    time_re = re.compile(
        r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])'
        r'T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$')
    assert time_re.match(response.json()["assign_time"])
    assert response.json()["orders"] == [{"id": 1}]


def test_get_courier_1():
    response = client.get("/couriers/1")
    assert response.status_code == 200
    assert response.json() == {
        "courier_id": 1,
        "courier_type": "foot",
        "regions": [
            1,
            12,
            22
        ],
        "working_hours": [
            "11:35-14:05",
            "09:00-11:00"
        ],
        "rating": 5.00,
        "earning": 1000
    }
