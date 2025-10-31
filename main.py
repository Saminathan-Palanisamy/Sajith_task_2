from fastapi import FastAPI, Depends
from routers import users, template_check, section_check, update_temp_sec,soft_delete
from core.database import Base, engine

Base.metadata.create_all(bind=engine)



app = FastAPI(title="Sajith task_2_project API - JWT Authentication [24-10-2025]")

# Including user router
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(template_check.router, prefix="/templates", tags=["Templates"])
app.include_router(section_check.router, prefix="/sections", tags=["Sections"])
app.include_router(update_temp_sec.router, prefix="/update", tags=["Updated Data"])
app.include_router(soft_delete.router, prefix="/soft_delete", tags=["Soft_Delete"])

@app.get("/")
def root():
    return {"message": "Welcome to the Sajith task_2_project API - JWT Authentication [24-10-2025]😄"
    "paaka nala irukum, vandhu paarungal!😊"}