from fastapi import FastAPI
from routers import users
from core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sajith task_2_project API - JWT Authentication [24-10-2025]")

# Including user router
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"message": "Welcome to the Sajith task_2_project API - JWT Authentication [24-10-2025]😄"
    "paaka nala irukum, vandhu paarungal!😊"}