from sqlalchemy.orm import Session
from typing import List

from . import models, schemas


def get_courier_by_id(db: Session, courier_id: int):
    return db.query(models.Courier).filter(models.Courier.id == courier_id).first()


def get_order_by_id(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_orders_by_working_hours(db: Session, working_hours: List[str]):
    order_delivery_hours = db.query(models.Order.delivery_hours)
    return list(set(order_delivery_hours) & set(working_hours))


def get_orders_by_regions(db: Session, region_ids: List[int]):
    return db.query(models.Order).filter(models.Order.region_id == [r_id for r_id in region_ids]).all()


def get_orders_weighing_less_than(db: Session, weight: float):
    return db.query(models.Order).filter(models.Order.weight <= weight).all()


def create_courier(db: Session, courier: schemas.CourierDto):
    db_courier = models.Courier(type=courier.courier_type)
    for region in courier.regions:
        db_courier_regions = models.CourierRegion(courier_id=courier.courier_id, region_id=region)
        db.add(db_courier_regions)
    for w_hours in courier.working_hours:
        db_courier_working_hours = models.CourierWorkingHours(
            courier_id=courier.courier_id,
            courier_working_hours=w_hours
        )
        db.add(db_courier_working_hours)
    db.add(db_courier)
    db.commit()
    return db_courier
