from sqlalchemy.orm import Session
from app import models, schemas
from app.security import hash_password


# ---- User CRUD ----

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed = hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ---- Calculation CRUD ----

def get_calculations(db: Session, user_id: int):
    return db.query(models.Calculation).filter(models.Calculation.user_id == user_id).all()

def get_calculation(db: Session, calc_id: int, user_id: int):
    return db.query(models.Calculation).filter(
        models.Calculation.id == calc_id,
        models.Calculation.user_id == user_id
    ).first()

def create_calculation(db: Session, calc: schemas.CalculationCreate, user_id: int, result: float):
    db_calc = models.Calculation(
        user_id=user_id,
        operation=calc.operation,
        operand1=calc.operand1,
        operand2=calc.operand2,
        result=result
    )
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc

def update_calculation(db: Session, db_calc: models.Calculation, update_data: dict, new_result: float):
    for key, value in update_data.items():
        setattr(db_calc, key, value)
    db_calc.result = new_result
    db.commit()
    db.refresh(db_calc)
    return db_calc

def delete_calculation(db: Session, db_calc: models.Calculation):
    db.delete(db_calc)
    db.commit()
