from fastapi import FastAPI
from .database import engine, Base
from . import models  # important
from .routes import users, projects, github
app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(github.router)

@app.get("/")
def read_root():
    return {"message": "Backend running"}
