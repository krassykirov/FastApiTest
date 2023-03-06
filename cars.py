from typing import Optional, List
from fastapi import Depends, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, select
from db import get_session
from schemas import Car, CarOutput, CarInput, Trip, TripInput, UserOutput, User
from fastapi import APIRouter, Request, Form,Depends, Cookie
from fastapi.templating import Jinja2Templates
from helper import wrap
from oauth import get_current_user


templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/api/cars")

@router.get("/")
def get_cars(*, name: Optional[str] = None, size: Optional[str] = None, doors: Optional[int] = None,
             db: Session = Depends(get_session),current_user: UserOutput = Depends(get_current_user), request: Request) -> List[Car]:
    query = select(Car)
    # api/cars/?size=s&doors=2&name=Mazda
    print('current_user', current_user)
    if size:
        query = query.where(Car.size == size)
    if doors:
        query = query.where(Car.doors == doors)
    if name:
        query = query.where(Car.name == name)
    if size and doors:
        query = query.where(Car.doors == doors and Car.size == size)
    if name and doors:
        query = query.where(Car.doors == doors and Car.name == name)
    if name and size:
        query = query.where(Car.name == name and Car.size == size)
    if size and doors and name:
        query = query.where(Car.doors == doors and Car.size == size and Car.name == name)
    print('query:', query)
    #cars = jsonable_encoder(db.exec(query).all())
    cars = db.exec(query).all()
    return templates.TemplateResponse("search_results.html", {"cars": cars,"request":request})

@router.get("/{id}", response_model=CarOutput)
def car_by_id(id:int, db: Session=Depends(get_session)):
        query = select(Car).where(Car.id == id)
        results = db.exec(query)
        car = results.first()
        if car:
            return car
        else:
            raise HTTPException(status_code=404,detail=f"No car with id={id}")

@router.post("/", response_model=Car)
def add_car(car: CarInput, db: Session=Depends(get_session),user: User = Depends(get_current_user)) -> CarOutput:
        new_car = Car.from_orm(car)
        db.add(new_car)
        db.commit()
        db.refresh(new_car)
        return new_car

@router.delete("/{id}", status_code=204)
def delete_car(id:int, db: Session=Depends(get_session)) -> None:
    query = db.query(Car).where(Car.id == id)
    car = query.first()
    if car:
        db.delete(car)
        db.commit()
    else:
        raise HTTPException(status_code=404,detail=f"No car with id={id}")

@router.put("/{id}", response_model=Car)
def update_car(id:int, new_data:CarInput, db:Session=Depends(get_session)) -> Car:
    car = db.query(Car).where(Car.id == id).first()
    car_updated  = new_data.dict(exclude_unset=True)
    for key, value in car_updated.items():
        setattr(car,key,value)
    db.commit()
    return car
    # else:
    #     raise HTTPException(status_code=404,detail=f"No car with id={id}")

@router.post("/{id}/trips/", response_model=Trip)
def update_trips(car_id:int, trip_input: TripInput, db:Session=Depends(get_session)) -> Trip:
    car = db.get(Car,car_id)
    if car:
        new_trip = Trip.from_orm(trip_input, update={"car_id": car_id})
        car.trips.append(new_trip)
        db.commit()
        db.refresh(new_trip)
        return new_trip
    else:
        raise HTTPException(status_code=404,detail=f"No car with id={id}")

@router.post("/search")
@wrap
def search(*, name: str=Form(None), size: str=Form(None), doors: int=Form(None), db: Session = Depends(get_session),request: Request):
    query = select(Car)
    if size:
        query = query.where(Car.size == size)
    if doors:
        query = query.where(Car.doors == doors)
    if name:
        query = query.where(Car.name == name)
    if size and doors:
        query = query.where(Car.doors == doors and Car.size == size)
    if name and doors:
        query = query.where(Car.doors == doors and Car.name == name)
    if name and size:
        query = query.where(Car.name == name and Car.size == size)
    if size and doors and name:
        query = query.where(Car.doors == doors and Car.size == size and Car.name == name)
    cars = db.exec(query).all()
    return templates.TemplateResponse("search_results.html", {"cars": cars,"request":request})

