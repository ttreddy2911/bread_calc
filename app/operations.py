def add(a: float, b: float) -> float:
    return a + b

def subtract(a: float, b: float) -> float:
    return a - b

def multiply(a: float, b: float) -> float:
    return a * b

def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def perform(operation: str, a: float, b: float) -> float:
    ops = {"add": add, "subtract": subtract, "multiply": multiply, "divide": divide}
    if operation not in ops:
        raise ValueError(f"Invalid operation: '{operation}'. Choose from: add, subtract, multiply, divide")
    return ops[operation](a, b)
