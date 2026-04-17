from pydantic import BaseModel
from typing import Optional

class CalculationBase(BaseModel):
    user_id: int
    operation: str
    operand1: float
    operand2: float

class CalculationCreate(CalculationBase):
    pass

class CalculationUpdate(BaseModel):
    operation: Optional[str] = None
    operand1: Optional[float] = None
    operand2: Optional[float] = None

class CalculationOut(CalculationBase):
    id: int
    result: float

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True
