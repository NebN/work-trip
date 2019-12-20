from dataclasses import dataclass


@dataclass
class Button:
    text: str
    value: str
    style: str = None
