from pydantic import BaseModel, EmailStr
from typing import Optional


# ---- User Schemas ----

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


# ---- Token Schemas ----

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# ---- Calculation Schemas ----

class CalculationCreate(BaseModel):
    operation: str
    operand1: float
    operand2: float

class CalculationUpdate(BaseModel):
    operation: Optional[str] = None
    operand1: Optional[float] = None
    operand2: Optional[float] = None

class CalculationRead(BaseModel):
    id: int
    user_id: int
    operation: str
    operand1: float
    operand2: float
    result: float

    class Config:
        from_attributes = True
