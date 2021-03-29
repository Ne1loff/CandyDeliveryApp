from datetime import datetime
from typing import List

from pydantic import BaseModel, validator


class CourierRegion(BaseModel):
    id: int
    region_id: int
    courier_id: int


class CourierWorkingHours(BaseModel):
    id: int
    working_hours: str
    courier_id: int


class CourierDto(BaseModel):
    courier_id: int
    courier_type: str
    regions: List[int]
    working_hours: List[str]

    class Config:
        orm_mode = True

    @validator('courier_type')
    def invalid_courier_type(cls, courier_type):
        if courier_type not in ["foot", "bike", "car"]:
            raise ValueError
        return courier_type


class Courier(CourierDto):
    rating: float
    earning: int

    class Config:
        orm_mode = True


class OrderDeliveryHours(BaseModel):
    id: int
    delivery_hours: str
    order_id: int


class OrderDto(BaseModel):
    order_id: int
    weight: float
    region: int
    delivery_hours: List[str]

    @validator('weight')
    def invalid_weight(cls, w):
        if w < 0.01 or w > 50.0:
            raise ValueError
        return w

    # @validator('region')
    # def invalid_weight(cls, w):
    #     if isinstance(w, int):
    #         raise ValueError
    #     return w


class Order(OrderDto):
    courier_id: int
    assign_time: datetime

    class Config:
        orm_mode = True
