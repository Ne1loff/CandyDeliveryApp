from typing import List

from pydantic import BaseModel


class CourierRegion(BaseModel):
    id: int
    courier_id: int


class CourierWorkingHours(BaseModel):
    working_hours: str
    courier_id: int


class CourierDto(BaseModel):
    courier_id: int
    courier_type: str
    regions: List[int]
    working_hours: List[str]


class Courier(CourierDto):
    rating: float
    earning: int

    class Config:
        orm_mode = True


class OrderDeliveryHours(BaseModel):
    delivery_hours: str
    order_id: int


class OrderDto(BaseModel):
    id: int
    weight: float
    region_id: int
    delivery_hours: List[str] = []


class Order(OrderDto):
    courier_id: int

    class Config:
        orm_mode = True
