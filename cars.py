
import shutil
from typing import Optional, List, Union
from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session, select
from fastapi import UploadFile
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from starlette.datastructures import URL
from db import get_session
from models import Car, User, Image
from helper import wrap
from oauth import get_current_user
import os
from os.path import abspath

import logging
logging.getLogger().setLevel(logging.INFO)

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/api")




@router.get("/", include_in_schema=False)
@router.get("/cars", include_in_schema=False)
def get_user_cars(request: Request, db: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return templates.TemplateResponse("user_items.html", {"request":request,'cars': user.cars,'current_user': user.username})

@router.get("/cars/{id}")
def car_details(request: Request, id:int, db: Session=Depends(get_session), user: User = Depends(get_current_user)):
        query = select(Car).where(Car.id == id)
        results = db.exec(query)
        car = results.first()
        logging.info(f'car: {car}')
        if car:
            return templates.TemplateResponse("car_details.html", {"request": request,'car': car, 'current_user': user.username})
        else:
            raise HTTPException(status_code=404,detail=f"No car with id={id}")

@router.post("/add_car_ui", include_in_schema=False)
async def add_car_ui(request: Request, db: Session = Depends(get_session), user: User = Depends(get_current_user)):
        form_data = await request.form()
        file = form_data['file']
        car_name=form_data['name']
        query = db.query(Car).where(Car.name == car_name).all()
        car = [car for car in query if car.username == user.username]
        if car:
            logging.info(f"car with that name already exists!")
            return templates.TemplateResponse("user_items.html", {"request":request,'cars': user.cars,'current_user': user.username,
                                                                   'message': "Car with that name already exists!"})
        path = f'{user.username}/cars/{car_name}/images'
        content = await file.read()
        dir = os.path.join('static', path)
        if not os.path.exists(dir):
               os.makedirs(dir,exist_ok=True)
        full_name = os.path.join(dir, file.filename)
        logging.info(f'full_name: {full_name}')
        with open(full_name, 'wb') as f:
            f.write(content)
            car = Car(name=form_data['name'], doors=form_data['doors'], size=form_data['size'], username=user.username)
        db.add(car)
        db.commit()
        image = Image(name=car_name, image_path=full_name,car_id=car.id)
        db.add(image)
        db.commit()
        redirect_url = URL(request.url_for('get_user_cars'))
        response = RedirectResponse(redirect_url, status_code=303)
        await file.close()
        return response

@router.post("/cars/add_photo", include_in_schema=False)
@router.post("/add_photo", include_in_schema=False)
async def add_car_ui(request: Request, db: Session = Depends(get_session), user: User = Depends(get_current_user)):
    form_data = await request.form()
    car_id = form_data['id']
    car = db.query(Car).where(Car.id == car_id).first()
    if car:
        car_name = form_data['name']
        file = form_data['file']
        content = await file.read()
        path = f'{user.username}/cars/{car_name}/images'
        dir = os.path.join('static', path)
        if not os.path.exists(dir):
               os.makedirs(dir,exist_ok=True)
        full_name = os.path.join(dir,file.filename)
        if not os.path.isfile(full_name):
            with open(full_name, 'wb') as f:
                f.write(content)
                image = Image(name=car_name, image_path=full_name, car_id=car_id)
                db.add(image)
                db.commit()
            redirect_url = URL(request.url_for('car_details', id=car.id))
            response = RedirectResponse(redirect_url, status_code=303)
            return response
        else:
            logging.info(f"Image with name: {file.filename} already exists")
            return templates.TemplateResponse("car_details.html", {"request":request, 'car': car, 'current_user': user.username,
                                                                   'message': "Image with that name already exists!"})
    else:
        logging.info(f"No car with id: {car.id} exists")
    return templates.TemplateResponse("car_details.html", {"request":request,'car': car, 'current_user': user.username})

@router.put("/cars/update_car", response_model=Car)
@router.post("/cars/update_car", response_model=Car, include_in_schema=False)
def update_car(request: Request, id: int=Form(None), name: str=Form(None), size: str=Form(None), doors: int=Form(None),
               db:Session=Depends(get_session), user: User = Depends(get_current_user)) -> Car:
    car = db.query(Car).where(Car.id == id).first()
    new_car = db.query(Car).where(Car.name == name).first()
    if new_car:
        return templates.TemplateResponse("car_details.html", {"request":request,'car': car,
                                                               'message': f"Car with name {name} already exists!",
                                                               'current_user': user.username})
    new_data = Car(id=id, name=name, size=size, doors=doors)
    new_data_updated = new_data.dict(exclude_unset=True, exclude_defaults=True, exclude_none=True)
    new_car_name = new_data_updated.get('name')
    if new_car_name:
        old_path = abspath(f"static/{user.username}/cars/{car.name}")
        new_path = abspath(f"static/{user.username}/cars/{new_car_name}")
        for image in car.images:
            image.image_path = f"static/{user.username}/cars/{new_car_name}/images/{image.image_path.split('/')[-1]}"
            image.name = image.image_path.split('/')[-1]
        os.rename(old_path, new_path)
        for key, value in new_data_updated.items():
            setattr(car, key, value)
        db.commit()
    else:
        for key, value in new_data_updated.items():
            setattr(car, key, value)
        db.commit()
    if request.method == 'POST':
        return templates.TemplateResponse("car_details.html", {"request":request,'car': car, 'current_user': user.username})
    elif request.method == 'PUT':
        return car

@router.post("/cars/delete_car", status_code=204, include_in_schema=False)
@router.post("/delete_car", status_code=204, include_in_schema=False)
@router.delete("/delete_car", status_code=204)
def delete_car(request: Request, id: int=Form(None), db: Session=Depends(get_session), user: User = Depends(get_current_user)) -> None:
    logging.info(f'deleting car {car.name} and id {car.id}')
    car = db.query(Car).where(Car.id == id).first()
    if car and car.username == user.username:
        logging.info(f'deleting car {car.name} and id {id}')
        db.delete(car)
        db.commit()
        dir_to_delete = abspath(f"static/{user.username}/cars/{car.name}")
        # dir_to_delete_all = abspath(f"static/{car.username}/cars/{car.name}")
        logging.info(f"Deleting car directory: {dir_to_delete}")
        try:
            shutil.rmtree(dir_to_delete) # onerror={'error'}
        except OSError as e:
            logging.info(f"Error deleting the directory: {dir_to_delete}, {e.strerror}")
        except Exception as e:
            logging.error(f"Something went wrong, error: {e}, {e.strerror}")
            return HTTPException(status_code=400, detail=f"Something went wrong, error {e}")
        if request.method == "POST":
            redirect_url = URL(request.url_for('get_user_cars'))
            response = RedirectResponse(redirect_url, status_code=303)
            return response
        else:
            logging.info(f"deleted car {car.name} with id: {car.id}")
            return
    else:
        raise HTTPException(status_code=404,detail=f"No car with id={id} and owner {user.username}")

@router.post("/cars/delete_image", status_code=204)
@router.post("/delete_image", status_code=204)
async def delete_image(request: Request, id: int=Form(None), car_id: int=Form(None), db: Session=Depends(get_session), user: User = Depends(get_current_user)):
    image = db.query(Image).where(Image.id == id).first()
    car = db.query(Car).where(Car.id == car_id).first()
    image_to_delete = abspath(image.image_path)
    try:
        os.remove(image_to_delete)
    except OSError as e:
        logging.info("Error: %s" % (e.strerror))
        raise HTTPException(status_code=400,detail=f"No able to remove image {image.image_path}")
    if image:
        logging.info(f'deleting image {image.name} and id {id}')
        db.delete(image)
        db.commit()
        redirect_url = URL(request.url_for('car_details', id=car.id))
        response = RedirectResponse(redirect_url, status_code=303)
        return response #templates.TemplateResponse("car_details.html", {"request":request, 'car': car, 'current_user': user.username})
    else:
        raise HTTPException(status_code=404,detail=f"No Image with id={id}")

@router.post("/", response_model=Car)
async def add_car(request: Request, name: str=Form(None), size: str=Form(None), doors: int=Form(None),db: Session=Depends(get_session),
                   user: User = Depends(get_current_user)) -> Car:
        new_car = Car(name=name, doors=doors, size=size, username=user.username)
        db.add(new_car)
        db.commit()
        db.refresh(new_car)
        return new_car

@router.post("/search", include_in_schema=False)
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




