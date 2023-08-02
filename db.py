from sqlmodel import create_engine, Session
import os 
connection = os.getenv("conn_str")

engine = create_engine(connection)

   
def get_session():
    with Session(engine) as session:
        yield session
