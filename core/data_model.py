from dataclasses import dataclass, asdict


@dataclass
class ROIData:
    col_name: str
    x: float
    y: float
    w: float
    h: float

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return ROIData(
            col_name=data.get("col_name", "Unknown"),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            w=data.get("w", 0.0),
            h=data.get("h", 0.0),
        )
