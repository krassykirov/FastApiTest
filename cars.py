from typing import Optional, List
from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session, select
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from db import get_session
from schemas import Car, User
from helper import wrap
from oauth import get_current_user, get_username_from_token
import os

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/api")

@router.get("/")
def get_cars(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("search_results.html", {"request":request})

@router.get("/cars")
def get_user_cars(request: Request, db: Session = Depends(get_session), user: User = Depends(get_current_user)):
    username = user.username
    cars = user.cars
    return templates.TemplateResponse("user_items.html", {"request":request,'cars': cars,'username': username})

@router.get("/add_car_ui")
def add_car_ui(request: Request, user: User = Depends(get_current_user)):
    username = get_username_from_token(request)
    return templates.TemplateResponse("add_car_ui.html", {"request":request, 'username': username})

@router.post("/add_car_ui")
async def add_car_ui(request: Request, db: Session = Depends(get_session), user: User = Depends(get_current_user)):
    try:
        username = user.username
        form_data = await request.form()
        file = form_data['file']
        content = await file.read()
        dir = os.path.join('static', f'{username}')
        if not os.path.exists(dir):
               os.makedirs(dir,exist_ok=True)
        full_name = os.path.join(dir,file.filename)
        with open(full_name, 'wb') as f:
            f.write(content)
        car = Car(name=form_data['name'], doors=form_data['doors'], size=form_data['size'], photo=file.filename, username=username)
        db.add(car)
        db.commit()
        response = RedirectResponse("add_car_ui.html", status_code=302)
        response = templates.TemplateResponse("add_car_ui.html",{"request":request, 'car': car})
        return response
    except Exception as e:
        print(e)
        return {"message": f"There was an error uploading the file:{e}"}
    finally:
        await file.close()

@router.get("/{id}", response_model=Car)
def car_by_id(id:int, db: Session=Depends(get_session), user: User = Depends(get_current_user)):
        query = select(Car).where(Car.id == id)
        results = db.exec(query)
        car = results.first()
        if car:
            return car
        else:
            raise HTTPException(status_code=404,detail=f"No car with id={id}")

@router.post("/", response_model=Car)
def add_car(car: Car, db: Session=Depends(get_session),user: User = Depends(get_current_user)) -> Car:
        new_car = Car.from_orm(car)
        db.add(new_car)
        db.commit()
        db.refresh(new_car)
        return new_car

@router.delete("/{id}", status_code=204)
def delete_car(id:int, db: Session=Depends(get_session), user: User = Depends(get_current_user)) -> None:
    query = db.query(Car).where(Car.id == id)
    car = query.first()
    if car:
        db.delete(car)
        db.commit()
    else:
        raise HTTPException(status_code=404,detail=f"No car with id={id}")

@router.put("/{id}", response_model=Car)
def update_car(id:int, new_data:Car, db:Session=Depends(get_session), user: User = Depends(get_current_user)) -> Car:
    car = db.query(Car).where(Car.id == id).first()
    car_updated  = new_data.dict(exclude_unset=True)
    for key, value in car_updated.items():
        setattr(car,key,value)
    db.commit()
    return car
    # else:
    #     raise HTTPException(status_code=404,detail=f"No car with id={id}")

# @router.post("/{id}/trips/", response_model=Trip)
# def update_trips(car_id:int, trip_input: TripInput, db:Session=Depends(get_session)) -> Trip:
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
def search(*, name: str=Form(None), size: str=Form(None), doors: int=Form(None), db: Session = Depends(get_session),
           user: User = Depends(get_current_user), request: Request):
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




