from sqlmodel import create_engine, Session

engine = create_engine(
    "sqlite:///app.db", connect_args={"check_same_thread": False} # Log generated SQL
    #  "postgresql://fastapi_traefik:fastapi_traefik@db:5432/fastapi_traefik"
)

def get_session():
    with Session(engine) as session:
        yield session
