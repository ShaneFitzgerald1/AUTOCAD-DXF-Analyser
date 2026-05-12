from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Lines:
    name: str
    x_start: float
    y_start: float
    x_end: float
    y_end: float
    offset: Optional[bool]
    lineref: Any

    def __iter__(self):
        return iter([self.name, self.x_start, self.y_start, self.x_end, self.y_end, self.offset, self.lineref])