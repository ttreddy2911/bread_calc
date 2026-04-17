from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from app.database import Base, engine, get_db
from app import models, schemas, crud
from app.security import verify_password, create_access_token, decode_token
from app.operations import perform

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Calculation BREAD API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


# ---- Auth Dependency ----

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = decode_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ---- Auth Endpoints ----

@app.post("/api/register", response_model=schemas.UserRead, status_code=201, tags=["Auth"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)


@app.post("/api/login", response_model=schemas.Token, tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


# ---- BREAD Endpoints ----

# BROWSE
@app.get("/api/calculations", response_model=List[schemas.CalculationRead], tags=["Calculations"])
def browse_calculations(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_calculations(db, current_user.id)


# READ
@app.get("/api/calculations/{id}", response_model=schemas.CalculationRead, tags=["Calculations"])
def read_calculation(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    calc = crud.get_calculation(db, id, current_user.id)
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calc


# ADD
@app.post("/api/calculations", response_model=schemas.CalculationRead, status_code=201, tags=["Calculations"])
def add_calculation(calc: schemas.CalculationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        result = perform(calc.operation, calc.operand1, calc.operand2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return crud.create_calculation(db, calc, current_user.id, result)


# EDIT
@app.put("/api/calculations/{id}", response_model=schemas.CalculationRead, tags=["Calculations"])
def edit_calculation(id: int, calc: schemas.CalculationUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_calc = crud.get_calculation(db, id, current_user.id)
    if not db_calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    update_data = calc.model_dump(exclude_unset=True)
    new_op = update_data.get("operation", db_calc.operation)
    new_a = update_data.get("operand1", db_calc.operand1)
    new_b = update_data.get("operand2", db_calc.operand2)
    try:
        new_result = perform(new_op, new_a, new_b)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return crud.update_calculation(db, db_calc, update_data, new_result)


# DELETE
@app.delete("/api/calculations/{id}", status_code=204, tags=["Calculations"])
def delete_calculation(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_calc = crud.get_calculation(db, id, current_user.id)
    if not db_calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    crud.delete_calculation(db, db_calc)


# ---- Static Frontend ----

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def serve_ui():
    return FileResponse("static/index.html")
