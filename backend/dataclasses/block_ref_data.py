from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class BlockRef:
    name: str
    x: float
    y: float
    angle: float
    name_error: Optional[Any]
    blockref: Any
    
    def __iter__(self):
        return iter([self.name, self.x, self.y, self.angle, self.name_error, self.blockref])
