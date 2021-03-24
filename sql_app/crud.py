from sqlalchemy.orm import Session
from typing import List

from . import models, schemas


def get_courier_by_id(db: Session, courier_id: int):
    db_courier = db.query(models.Courier).filter(models.Courier.courier_id == courier_id).first()
    rating = db_courier.rating
    earning = db_courier.earning
    if rating is None:
        rating = 0
    if earning is None:
        earning = 0
    dict_ = {
        "courier_id": db_courier.courier_id,
        "courier_type": db_courier.type,
        "regions": get_regions_by_courier_id(db, courier_id),
        "working_hours": get_working_hours_by_courier_id(db, courier_id),
        "rating": rating,
        "earning": earning
    }
    return dict_


def get_order_by_id(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_regions_by_courier_id(db: Session, courier_id: int):
    db_regions = db.query(models.CourierRegion).filter(models.CourierRegion.courier_id == courier_id).all()
    regions = []
    for region in db_regions:
        regions.append(region.region_id)
    return regions


def get_working_hours_by_courier_id(db: Session, courier_id: int):
    db_w_h = db.query(models.CourierWorkingHours).filter(models.CourierWorkingHours.courier_id == courier_id).all()
    working_hours = []
    for w_h in db_w_h:
        working_hours.append(w_h.courier_working_hours)
    return working_hours


def get_order_by_order_id(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_orders_by_working_hours(db: Session, working_hours: List[str]):
    order_delivery_hours = db.query(models.Order.delivery_hours)
    return list(set(order_delivery_hours) & set(working_hours))


def get_orders_by_regions(db: Session, region_ids: List[int]):
    return db.query(models.Order).filter(models.Order.region_id == [r_id for r_id in region_ids]).all()


def get_orders_weighing_less_than(db: Session, weight: float):
    return db.query(models.Order).filter(models.Order.weight <= weight).all()


def create_courier(db: Session, courier: schemas.CourierDto):
    db_courier = models.Courier(
        type=courier.courier_type,
        rating=None,
        earning=None
    )
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
    db.refresh(db_courier)
    return db_courier


def create_order(db: Session, order: schemas.OrderDto):
    db_order = models.Order(
        weight=order.weight,
        region_id=order.region,
    )
    for d_hours in order.delivery_hours:
        db_order_delivery_hours = models.OrderDeliveryHours(
            order_id=order.order_id,
            delivery_hours=d_hours
        )
        db.add(db_order_delivery_hours)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def assign_order(db: Session, courier: schemas.Courier):
    if courier.courier_type == "foot":
        weight = 10.0
    elif courier.courier_type == "bike":
        weight = 15.0
    else:
        weight = 50.0
    list_by_wh = get_orders_by_working_hours(db, courier.working_hours)
    list_by_region = get_orders_by_regions(db, courier.regions)
    list_by_weight = get_orders_weighing_less_than(db, weight)
    matching_orders = list(set(list_by_region) & set(list_by_weight) & set(list_by_wh))
    matching_orders_for_courier = []
    for order in matching_orders:
        if order.order_id is None:
            matching_orders_for_courier.append(order)

    return matching_orders_for_courier
