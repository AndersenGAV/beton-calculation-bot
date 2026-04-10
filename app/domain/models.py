from dataclasses import dataclass


@dataclass
class ConcretePrice:
    full_label: str
    short_label: str
    price_uah_per_m3: int


@dataclass
class DeliveryPrice:
    distance_km: int
    price_per_cube: int