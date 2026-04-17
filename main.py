from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import engine, get_db

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Calculation BREAD API")

# Setup default seed users if none exist
def seed_users():
    db = next(get_db())
    if db.query(models.User).count() == 0:
        db.add(models.User(username="alice"))
        db.add(models.User(username="bob"))
        db.commit()

seed_users()

# Serve static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

# Helper math function
def perform_calculation(op: str, num1: float, num2: float) -> float:
    if op == "add": return num1 + num2
    if op == "subtract": return num1 - num2
    if op == "multiply": return num1 * num2
    if op == "divide":
        if num2 == 0: raise ValueError("Cannot divide by zero")
        return num1 / num2
    raise ValueError("Invalid operation type")

# --- BREAD ENDPOINTS ---

# 1. BROWSE
@app.get("/api/users", response_model=List[schemas.UserOut])
def get_users(db: Session = Depends(get_db)):
    """Get mocked users"""
    return db.query(models.User).all()

@app.get("/api/calculations", response_model=List[schemas.CalculationOut])
def get_calculations(user_id: int = None, db: Session = Depends(get_db)):
    """Retrieve all calculations. If user_id provided, filter by user."""
    query = db.query(models.Calculation)
    if user_id:
        query = query.filter(models.Calculation.user_id == user_id)
    return query.all()

# 2. READ
@app.get("/api/calculations/{id}", response_model=schemas.CalculationOut)
def read_calculation(id: int, db: Session = Depends(get_db)):
    """Retrieve details of a specific calculation."""
    db_calc = db.query(models.Calculation).filter(models.Calculation.id == id).first()
    if not db_calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return db_calc

# 3. ADD (Create)
@app.post("/api/calculations", response_model=schemas.CalculationOut, status_code=201)
def create_calculation(calc: schemas.CalculationCreate, db: Session = Depends(get_db)):
    """Create a new calculation."""
    try:
        result = perform_calculation(calc.operation, calc.operand1, calc.operand2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    db_calc = models.Calculation(**calc.model_dump(), result=result)
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc

# 4. EDIT (Update)
@app.put("/api/calculations/{id}", response_model=schemas.CalculationOut)
def update_calculation(id: int, calc: schemas.CalculationUpdate, db: Session = Depends(get_db)):
    """Update an existing calculation."""
    db_calc = db.query(models.Calculation).filter(models.Calculation.id == id).first()
    if not db_calc:
        raise HTTPException(status_code=404, detail="Calculation not found")

    update_data = calc.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_calc, key, value)
    
    # Recalculate result
    try:
        db_calc.result = perform_calculation(db_calc.operation, db_calc.operand1, db_calc.operand2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    db.refresh(db_calc)
    return db_calc

# 5. DELETE
@app.delete("/api/calculations/{id}", status_code=204)
def delete_calculation(id: int, db: Session = Depends(get_db)):
    """Remove a calculation."""
    db_calc = db.query(models.Calculation).filter(models.Calculation.id == id).first()
    if not db_calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    db.delete(db_calc)
    db.commit()
    return None
