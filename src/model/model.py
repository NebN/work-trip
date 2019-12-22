from dataclasses import dataclass
from datetime import date


@dataclass
class Employee:
    user_id: str  # Primary key
    user_name: str
    channel_id: str = None


@dataclass
class Expense:
    payed_on: date
    amount: str
    description: str = None
    proof_url: str = None
    external_id: str = None
    employee_user_id: str = None
    id: int = None  # Primary Key

    def __repr__(self):
        return (f'*[{self.id}] ' if self.id else '*') + f'{self.payed_on} €{self.amount} {self.description}*'
