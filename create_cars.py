"""
create_user.py
-------------
A convenience script to create a user.
"""

from getpass import getpass

from sqlmodel import SQLModel, Session, create_engine

from schemas import CarInput, Car
import json


engine = create_engine(
    "sqlite:///app.db",
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=True # Log generated SQL
)

if __name__ == "__main__":
    print("Creating tables (if necessary)")
    SQLModel.metadata.create_all(engine)

    print("--------")
    print("This script will create a cars and save it in the database.")
    with open('cars.json') as json_file:
        data = json.load(json_file)

    for car in data:
        print('car', car)
        with Session(engine) as session:
            car = Car(name=car['name'],size=car['size'], fuel=car['fuel'], doors=car['doors'])
            session.add(car)
            session.commit()
