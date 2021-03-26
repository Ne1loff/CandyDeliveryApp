from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from . import models, schemas


def get_courier_by_id(db: Session, courier_id: int):
    db_courier = db.query(models.Courier).filter(models.Courier.courier_id == courier_id).first()
    if not db_courier:
        return None
    rating = db_courier.rating
    earning = db_courier.earning
    if rating is None:
        rating = 0
    if earning is None:
        earning = 0
    courier = schemas.Courier
    courier.courier_id = db_courier.courier_id
    courier.courier_type = db_courier.type
    courier.regions = get_regions_by_courier_id(db, courier_id)
    courier.working_hours = get_working_hours_by_courier_id(db, courier_id)
    courier.rating = rating
    courier.earning = earning
    return courier


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


def get_orders_by_working_hours(db: Session, working_hours: List[str], orders_id: List[int]):
    orders_list = []
    suited = False
    for order_n in orders_id:
        order = db.query(models.Order) \
            .filter(models.Order.courier_id == -1) \
            .filter(models.Order.id == order_n) \
            .first()
        if order is None:
            return orders_list
        for d_h_class in order.delivery_hours:
            d_h = d_h_class.delivery_hours
            for w_h in working_hours:
                if checking_the_time(w_h, d_h):
                    orders_list.append(order)
                    suited = True
                    break
            if suited:
                break

    return orders_list


def get_orders_by_regions(db: Session, regions_id: List[int]):
    regions_list = []
    for region_id in regions_id:
        order = db.query(models.Order) \
            .filter(models.Order.courier_id == -1) \
            .filter(models.Order.region_id == region_id) \
            .first()
        if order is not None:
            regions_list.append(order)
    return regions_list


def get_orders_weighing_less_than(db: Session, weight: float):
    return db.query(models.Order) \
        .filter(models.Order.courier_id == -1) \
        .filter(models.Order.weight <= weight) \
        .all()


def create_courier(db: Session, courier: schemas.CourierDto):
    db_courier = models.Courier(
        type=courier.courier_type,
        rating=None,
        earning=None
    )
    for region in courier.regions:
        db_courier_regions = models.CourierRegion(
            courier_id=courier.courier_id,
            region_id=region
        )
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

    suitable_orders = []

    print(db.query(models.Order).filter(models.Order.region_id == 1).first().courier_id)

    list_by_weight = get_orders_weighing_less_than(db, weight)
    if list_by_weight:
        orders_id_by_weight = []
        for order in list_by_weight:
            orders_id_by_weight.append(order.id)

        list_by_region = get_orders_by_regions(db, courier.regions)
        if list_by_region:
            orders_id_by_region = []
            for order in list_by_region:
                orders_id_by_region.append(order.id)

            orders_id = list(set(orders_id_by_weight) & set(orders_id_by_region))
            if orders_id:
                suitable_orders = get_orders_by_working_hours(db, courier.working_hours, orders_id)

    now = datetime.now()
    assign_time = now.isoformat()
    print(assign_time)
    for order in suitable_orders:
        db_order = db.query(models.Order).get(order.id)
        db_order.courier_id = courier.courier_id
        print(db_order.courier_id)
        db_order.assign_time = now
        db.commit()
    return suitable_orders, assign_time


def update_courier(db: Session, changes: dict, courier_id: int):
    fields = [
        "courier_id",
        "courier_type",
        "regions",
        "working_hours"
    ]
    db_courier = db.query(models.Courier).get(courier_id)
    for field in fields:
        change = changes.get(field)
        if change is not None:
            if field == "regions":

                # delite all regions
                db_regions = db.query(models.CourierRegion) \
                    .filter(models.CourierRegion.courier_id == courier_id) \
                    .all()
                for region in db_regions:
                    db.delete(region)

                for region in change:
                    db_region = models.CourierRegion(
                        courier_id=courier_id,
                        region_id=region
                    )
                    db.add(db_region)
                    db.commit()
            elif field == "working_hours":

                # delite all working hours
                db_working_hours = db.query(models.CourierWorkingHours) \
                    .filter(models.CourierWorkingHours.courier_id == courier_id) \
                    .all()
                for w_h in db_working_hours:
                    db.delete(w_h)

                for w_h in change:
                    db_w_h = models.CourierWorkingHours(
                        courier_id=courier_id,
                        courier_working_hours=w_h
                    )
                    db.add(db_w_h)
                    db.commit()
            elif field == "courier_id":
                db_courier.courier_id = change
            else:
                db_courier.type = change
            db.commit()
    db.refresh(db_courier)

    courier_dto = schemas.CourierDto
    courier_dto.courier_id = db_courier.courier_id
    courier_dto.courier_type = db_courier.type
    courier_dto.regions = get_regions_by_courier_id(db, courier_id)
    courier_dto.working_hours = get_working_hours_by_courier_id(db, courier_id)

    print(courier_dto)
    return courier_dto


def check_courier(db: Session, courier_id: int):
    courier_orders = db.query(models.Order).filter(models.Order.courier_id == courier_id).all()
    courier_regions = get_regions_by_courier_id(db, courier_id)
    courier_w_h = get_working_hours_by_courier_id(db, courier_id)
    courier = get_courier_by_id(db, courier_id)
    courier_max_weight = courier.courier_type

    if courier_max_weight == "foot":
        courier_max_weight = 10.0
    elif courier_max_weight == "bike":
        courier_max_weight = 15.0
    else:
        courier_max_weight = 50.0

    for order in courier_orders:
        if order.weight > courier_max_weight:
            order.courier_id = -1
            order.assign_time = None
            db.commit()
        elif order.region_id not in courier_regions:
            order.courier_id = -1
            order.assign_time = None
            db.commit()
        elif order.delivery_hours:
            ok = False
            for d_h in order.delivery_hours:
                for w_h in courier_w_h:
                    if checking_the_time(w_h, d_h):
                        ok = True
            if not ok:
                order.courier_id = -1
                order.assign_time = None
                db.commit()


def checking_the_time(w_h: str, d_h: str):
    # Delivery hours convert in minute
    d_h_begin, d_h_end = convert_to_minute(d_h)

    # Working hours convert in minute
    w_h_begin, w_h_end = convert_to_minute(w_h)

    b1 = d_h_end <= w_h_begin
    b2 = d_h_begin >= w_h_end

    if b1 or b2:
        return False
    elif d_h_begin <= w_h_begin < d_h_end:
        return True
    elif w_h_begin <= d_h_begin < d_h_end:
        return True


def convert_to_minute(time: str):
    begin = (int(time[0]) * 10 + int(time[1])) * 60
    begin += int(time[3]) * 10 + int(time[4])
    end = (int(time[6]) * 10 + int(time[7])) * 60
    end += int(time[9]) * 10 + int(time[10])
    return begin, end
