from pydantic import BaseModel
from typing import Optional, Union
from sqlmodel import SQLModel, Field, Relationship,Column,VARCHAR
from passlib.context import CryptContext
# https://nilsdebruin.medium.com/fastapi-how-to-add-basic-and-cookie-authentication-a45c85ef47d3
from fastapi.security import OAuth2
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.utils import get_openapi
from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, Response, JSONResponse
from starlette.requests import Request
from typing import Optional, List
from fastapi import HTTPException
import datetime

pwd_context = CryptContext(schemes="bcrypt")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None
    expires: Optional[datetime.datetime] # https://stackoverflow.com/questions/68811220/handling-the-token-expiration-in-fastapi

class UserOutput(SQLModel):
    id: int
    username: str

class User(SQLModel, table=True):
    id: int = Field(primary_key=True,default=None)
    username: str = Field(sa_column=Column("username", VARCHAR,unique=True, index=True))
    password_hash: str = ""

    def set_password(self,password):
        self.password_hash = pwd_context.hash(password)

    def verify_password(self,password):
        return pwd_context.verify(password,self.password_hash)


class CarInput(SQLModel):
    name: str
    size: Optional[str]
    fuel: Optional[str] = "electric"
    doors: Optional[int]

    class Config:
        schema_extra = {
        "example": {
            "name": "Subaru",
            "size": "m",
            "doors": 4,
            "fuel": "electric"
           }
        }

class TripInput(SQLModel):
    start: int
    end: int
    description: str

class TripOutput(TripInput):
    id: int

class Trip(TripInput, table=True):
    id: Optional[int] = Field(default=None,primary_key=True)
    car_id: int = Field(foreign_key="car.id")
    car: "Car" = Relationship(back_populates="trips")

class CarOutput(CarInput):
    name: str
    id: int
    trips: list[TripOutput] = []

class Car(CarInput, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trips: list[Trip] = Relationship(back_populates="car")


class OAuth2PasswordBearerCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        header_authorization: str = request.headers.get("access_token")
        cookie_authorization: str = request.cookies.get("access_token")

        header_scheme, header_param = get_authorization_scheme_param(
            header_authorization
        )
        cookie_scheme, cookie_param = get_authorization_scheme_param(
            cookie_authorization
        )

        if header_scheme.lower() == "bearer":
            authorization = True
            scheme = header_scheme
            param = header_param

        elif cookie_scheme.lower() == "bearer":
            authorization = True
            scheme = cookie_scheme
            param = cookie_param

        else:
            authorization = False

        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        return param


# class BasicAuth(SecurityBase):
#     def __init__(self, scheme_name: str = None, auto_error: bool = True):
#         self.scheme_name = scheme_name or self.__class__.__name__
#         self.auto_error = auto_error

#     async def __call__(self, request: Request) -> Optional[str]:
#         authorization: str = request.headers.get("access_token")
#         scheme, param = get_authorization_scheme_param(authorization)
#         if not authorization or scheme.lower() != "basic":
#             if self.auto_error:
#                 raise HTTPException(
#                     status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
#                 )
#             else:
#                 return None
#         return param