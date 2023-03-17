from typing import Optional, List, Union
from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session, select
from fastapi import UploadFile
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from starlette.datastructures import URL
from db import get_session
from schemas import Car, User
from helper import wrap
from oauth import get_current_user
import os
from os.path import abspath

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/api")


@router.get("/cars")
def get_user_cars(request: Request, db: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return templates.TemplateResponse("user_items.html", {"request":request,'cars': user.cars,'current_user': user.username})

@router.get("/cars/{id}")
def car_details(request: Request, id:int, db: Session=Depends(get_session), user: User = Depends(get_current_user)):
        print('headers:', request.headers)
        print('request.base_url', request.base_url)
        print('request.path_param', request.path_params)
        query = select(Car).where(Car.id == id)
        results = db.exec(query)
        car = results.first()
        print('car', car)
        if car:
            return templates.TemplateResponse("car_details.html", {"request":request,'car': car, 'current_user': user.username})
        else:
            raise HTTPException(status_code=404,detail=f"No car with id={id}")

@router.get("/add_car_ui")
def add_car_ui(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("add_car_ui.html", {"request":request, 'current_user': user.username})

@router.post("/add_car_ui")
async def add_car_ui(request: Request, db: Session = Depends(get_session), user: User = Depends(get_current_user)):
    try:
        username = user.username
        form_data = await request.form()
        file = form_data['file']
        car_name=form_data['name']
        path = f'{username}/cars/{car_name}/images'
        content = await file.read()
        dir = os.path.join('static', path)
        print('dir:',dir)
        if not os.path.exists(dir):
               os.makedirs(dir,exist_ok=True)
        full_name = os.path.join(dir,file.filename)
        print('full_name:', full_name)
        with open(full_name, 'wb') as f:
            f.write(content)
        car = Car(name=form_data['name'], doors=form_data['doors'], size=form_data['size'], photo=file.filename, photo_full_path=full_name, username=username)
        db.add(car)
        db.commit()
        redirect_url = URL(request.url_for('get_user_cars'))
        response = RedirectResponse(redirect_url, status_code=303)
        return response
    except Exception as e:
        print({"message": f"There was an error uploading the file:{e}"})
        redirect_url = URL(request.url_for('get_user_cars'))
        response = RedirectResponse(redirect_url, status_code=303)
        return response
    finally:
        await file.close()

@router.post("/", response_model=Car)
def add_car(car: Car, db: Session=Depends(get_session),user: User = Depends(get_current_user)) -> Car:
        new_car = Car.from_orm(car)
        db.add(new_car)
        db.commit()
        db.refresh(new_car)
        return new_car

@router.post("/cars/delete_car", status_code=204)
@router.post("/delete_car", status_code=204)
def delete_car(request: Request, id: int=Form(None), db: Session=Depends(get_session), user: User = Depends(get_current_user)) -> None:
    query = db.query(Car).where(Car.id == id)
    car = query.first()
    if car:
        print(f'deleting car {car.name} and id {id}')
        db.delete(car)
        db.commit()
        redirect_url = URL(request.url_for('get_user_cars'))
        response = RedirectResponse(redirect_url, status_code=303)
        return response
    else:
        raise HTTPException(status_code=404,detail=f"No car with id={id}")

@router.put("/cars/update_car", response_model=Car)
def update_car(id:int, new_data:Car, db:Session=Depends(get_session), user: User = Depends(get_current_user)) -> Car:
    car = db.query(Car).where(Car.id == id).first()
    print('car', car)
    print('new_data', new_data )
    old_path = abspath(f"static/{user.username}/cars/{car.name}")
    new_path = abspath(f"static/{user.username}/cars/{new_data.name}")
    print('old_path', abspath(old_path))
    print('new_path', abspath(new_path))
    new_data.photo_full_path = new_path
    new_data  = new_data.dict(exclude_unset=True)
    os.rename(old_path, new_path)
    print('new_data', new_data )
    for key, value in new_data.items():
        setattr(car,key,value)
    db.commit()
    return car

@router.post("/cars/update_car", response_model=Car)
def update_car(request: Request, id: int=Form(None), name: str=Form(None), size: str=Form(None), doors: int=Form(None), db:Session=Depends(get_session), user: User = Depends(get_current_user)) -> Car:
    car = db.query(Car).where(Car.id == id).first()
    print('car', car)
    new_data = Car(id=id, name=name,size=size, doors=doors)
    old_path = abspath(f"static/{user.username}/cars/{car.name}")
    new_path = abspath(f"static/{user.username}/cars/{new_data.name}")
    print('old_path', abspath(old_path))
    print('new_path', abspath(new_path))
    new_data.photo_full_path = new_path
    new_data  = new_data.dict(exclude_unset=True)
    os.rename(old_path, new_path)
    print('new_data', new_data )
    for key, value in new_data.items():
        setattr(car,key,value)
    db.commit()
    return templates.TemplateResponse("car_details.html", {"request":request,'car': car, 'current_user': user.username})


@router.get("/")
def get_cars(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("search_results.html", {"request":request, 'current_user': user.username})

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




