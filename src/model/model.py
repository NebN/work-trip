from dataclasses import dataclass
from datetime import date


@dataclass
class Employee:
    user_id: str  # Primary key
    user_name: str
    channel_id: str = None


@dataclass
class Email:
    address: str  # Primary key
    employee_user_id: str  # references Employee (user_id)
    verified: bool = False


@dataclass
class Expense:
    employee_user_id: str
    payed_on: date
    amount: str
    description: str = None
    proof_url: str = None
    id: int = None
