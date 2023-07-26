import uvicorn
from fastapi import FastAPI, Request, Response
from sqlmodel import SQLModel, create_engine, Session
from cars import router
from oauth import oauth_router
from fastapi.staticfiles import StaticFiles
from fastapi import Depends
from oauth import get_current_user
# from fastapi.middleware.cors import CORSMiddleware
from db import engine

app = FastAPI()
app.include_router(router)
app.include_router(oauth_router)
app.mount("/static", StaticFiles(directory="static"), name="static")
# app.dependencies=[Depends(get_current_user)]

# origins = [
#     "http://localhost:8000",
#     "http://localhost:8080",
# ]
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# @app.middleware('http')
# async def add_cookie(request: Request, call_next):
#     response = await call_next(request)
#     response.set_cookie(key='cars_cookie',value="You've visted cars site")
#     response.headers['X-car-Header'] = "Car Header"
#     print(response.headers)
#     return response


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    uvicorn.run("main:app",reload=True)

# uvicorn main:app --reload