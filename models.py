from pydantic import BaseModel
from typing import Optional, Union
from sqlmodel import SQLModel, Field, Relationship, Column, VARCHAR
from passlib.context import CryptContext
from typing import Optional, List

import datetime

pwd_context = CryptContext(schemes="bcrypt")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None
    expires: Optional[datetime.datetime]



class Car(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column("name", VARCHAR, unique=True, index=True))
    size: Optional[str]  = None
    fuel: Optional[str]  = None
    doors: Optional[int] = None
    photo: Optional[str] = None
    photo_full_path: Optional[str] = None
    owner: Optional['User'] = Relationship(back_populates="cars")
    username: str = Field(default=None, foreign_key="user.username")
    # user = models.ForeignKey('BirdUser', null=True, related_name='added_by', on_delete=models.CASCADE)

class CarImages(BaseModel):
    image: List[str] = None
    car_id: Field(default=None, foreign_key="car.id")

class User(SQLModel, table=True):
    id: int = Field(primary_key=True,default=None)
    username: str = Field(sa_column=Column("username", VARCHAR, unique=True, index=True))
    password_hash: str = ""
    cars: List[Car] = Relationship(sa_relationship_kwargs={"cascade": "delete"}, back_populates="owner")

    def set_password(self,password):
        self.password_hash = pwd_context.hash(password)

    def verify_password(self,password):
        return pwd_context.verify(password,self.password_hash)

    class Config:
        schema_extra = {
        "example": {
            "name": "Subaru",
            "size": "m",
            "doors": 4,
            "fuel": "electric",
            "photo": "photo",
            "owner": "krassy"
           }
        }
        orm_mode = True



