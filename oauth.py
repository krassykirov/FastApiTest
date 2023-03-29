from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, Request

from typing import Union
from sqlmodel import Session, select
from starlette import status
from fastapi import Depends, HTTPException, APIRouter, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from db import get_session
from models import User, Token,TokenData
from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import BackgroundTasks
from datetime import datetime, timedelta
from helper import write_log, wrap
from schemas import OAuth2PasswordBearerCookie


templates = Jinja2Templates(directory="templates")
# basic_auth = BasicAuth(auto_error=False)
oauth_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearerCookie(tokenUrl="token")

ACCESS_TOKEN_EXPIRE_MINUTES = 1  # 30 minutes
ALGORITHM = "HS256"
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"

@oauth_router.get("/", include_in_schema=False)
@wrap
def home(request: Request):
    # print("headers:", request.headers.get('cookie').split("=")[1].split()[1].replace('"',""))
    try:
        token = request.cookies.get("access_token") #or request.headers.get("access_token")
        if token:
            access_token = token.split()[1]
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            expires = payload.get("exp")
            converted_expires = datetime.fromtimestamp(expires)
            print('converted_expires', converted_expires)
            print('datetime.now()', datetime.now())
            if datetime.now() < converted_expires:
                context = {'request': request, 'current_user': username, 'access_token': access_token, 'expires': converted_expires}
                return templates.TemplateResponse("home.html", context)
        else:
            context = {'request': request, 'message': "Not Authorized please login"}
            return templates.TemplateResponse("login.html", context)
    except ExpiredSignatureError:
        context = {'request': request, 'message': "Session expired please login"}
        return templates.TemplateResponse("login.html", context)
    except Exception:
        raise

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)) ->User:
    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Could not validate credentials",
    #     headers={"WWW-Authenticate": "Bearer"},
    # )
    credentials_exception = HTTPException(status_code=302, detail="Not authorized", headers = {"Location": "/login"} )
    # expired_session_exception = HTTPException(status_code=302, detail="Session expired", headers = {"Location": "/login"} )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        expires = payload.get("exp")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, expires=expires)
    except JWTError:
        raise credentials_exception
    query = select(User).where(User.username == token_data.username)
    user = db.exec(query).first()
    if user is None:
        raise credentials_exception
    if expires is None:
        raise credentials_exception
    converted_expires = datetime.fromtimestamp(expires)
    if datetime.utcnow() > converted_expires:
        response = templates.TemplateResponse("login.html",{"request":request, 'message': "Session expired"})
        return response
    return user

@oauth_router.post('/token', response_model=Token, include_in_schema=False  )
def login_access_token(*, response: Response, form_data: OAuth2PasswordRequestForm=Depends(),
                db: Session = Depends(get_session), background_tasks: BackgroundTasks ):
    query = select(User).where(User.username == form_data.username)
    user = db.exec(query).first()
    if user and user.verify_password(form_data.password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        time = datetime.now()
        background_tasks.add_task(write_log, message=f"user:{user.username} logged in at {time} and get a token {access_token} ")
        response = RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
        return response

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or password incorrect"
        )

@oauth_router.get("/login", include_in_schema=False)
def login(request: Request):
    response = templates.TemplateResponse("login.html",{"request":request})
    return response

@oauth_router.get("/signup", include_in_schema=False)
def login(request: Request):
    response = templates.TemplateResponse("signup.html",{"request":request})
    return response

@oauth_router.post("/signup", include_in_schema=False)
async def signup(request: Request, db: Session = Depends(get_session)):
    form_data = await request.form()
    print('form_data:', form_data)
    username = form_data.get('username')
    passwd = form_data.get('password')
    passwd2 = form_data.get('password2')
    print(username,passwd, passwd2)
    assert passwd == passwd2
    query = select(User).where(User.username == username)
    user = db.exec(query).first()
    if not user:
        user = User(username=username)
        user.set_password(passwd)
        db.add(user)
        db.commit()
    response = templates.TemplateResponse("login.html",{"request":request})
    return response

@oauth_router.get("/logout", include_in_schema=False)
def route_logout_and_remove_cookie(request: Request):
    response = RedirectResponse("login.html", status_code=302)
    response = templates.TemplateResponse("login.html",{"request":request, 'current_user': None})
    response.delete_cookie(key="access_token")
    return response
