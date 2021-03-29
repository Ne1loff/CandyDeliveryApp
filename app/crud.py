from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import dateutil.parser

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

    assigned_orders = db.query(models.Order).filter(models.Order.courier_id == courier.courier_id).all()
    completed_orders = db.query(models.CompletedCourierOrder) \
        .filter(models.CompletedCourierOrder.courier_id == courier.courier_id) \
        .all()

    assigned_orders_id = []
    completed_orders_id = []
    for order in assigned_orders:
        assigned_orders_id.append(order.id)
    for order in completed_orders:
        completed_orders_id.append(order.order_id)

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
    change_assign_time = True
    for order in suitable_orders:
        db_order = db.query(models.Order).get(order.id)
        db_order.courier_id = courier.courier_id
        db_order.courier_type = courier.courier_type
        db_order.assign_time = now
        db.commit()
        change_assign_time = False

    if change_assign_time:
        if assigned_orders:
            max_time = assigned_orders[0].assign_time
            for order in assigned_orders:
                if order.assign_time > max_time:
                    max_time = order.assign_time
            assign_time = max_time

    orders_id = list(set(assigned_orders_id) ^ set(completed_orders_id))
    for order_id in orders_id:
        db_order = db.query(models.Order).get(order_id)
        suitable_orders.append(db_order)

    suitable_orders = list(set(suitable_orders))

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


def create_completed_courier_order(
        db: Session,
        courier_id: int,
        order_id: int,
        complete_time_g: datetime,
        order_region: int
):
    completed_orders = db.query(models.CompletedCourierOrder) \
        .filter(models.CompletedCourierOrder.courier_id == courier_id) \
        .filter(models.CompletedCourierOrder.order_region == order_region) \
        .all()
    last_completed_order = []
    if completed_orders:
        for order in completed_orders:
            last_completed_order.append(order.order_number)
        last_completed_order = list(set(last_completed_order))[-1]
    else:
        last_completed_order = 0

    if last_completed_order == 0:
        db_order = db.query(models.Order).get(order_id)
        completion_time = db_order.assign_time
    else:
        db_last_completed_order = db.query(models.CompletedCourierOrder) \
            .filter(models.CompletedCourierOrder.order_number == last_completed_order) \
            .first()
        completion_time = db_last_completed_order.complete_time

    complete_time = complete_time_g.strftime('%Y-%m-%dT%H:%M:%S')
    completion_time = completion_time.strftime('%Y-%m-%dT%H:%M:%S')
    complete_time_s = dateutil.parser.parse(complete_time)
    completion_time_s = dateutil.parser.parse(completion_time)

    lead_time = int((complete_time_s - completion_time_s).total_seconds())

    db_completed_courier_order = models.CompletedCourierOrder(
        courier_id=courier_id,
        order_id=order_id,
        order_number=last_completed_order + 1,
        complete_time=complete_time_g,
        lead_time=lead_time,
        order_region=order_region
    )
    db.add(db_completed_courier_order)
    db.commit()


def order_complete(db: Session, order_info: dict):
    order_id = order_info.get("order_id")
    complete_time = order_info.get("complete_time")
    courier_id = order_info.get("courier_id")

    db_order = db.query(models.Order).get(order_id)

    if db_order is None or db_order.courier_id != courier_id:
        return None
    complete_time_dt = dateutil.parser.parse(complete_time)
    if db.query(models.CompletedCourierOrder).filter(models.CompletedCourierOrder.order_id == order_id).first() is None:

        create_completed_courier_order(
            db, courier_id, order_id,
            complete_time_dt,
            db_order.region_id
        )

        earning_ratio = db_order.courier_type
        if earning_ratio == "foot":
            earning_ratio = 2
        elif earning_ratio == "bike":
            earning_ratio = 5
        else:
            earning_ratio = 9

        calculate_courier_rating_earning(db, courier_id, earning_ratio)

    return order_id


def calculate_courier_rating_earning(db: Session, courier_id: int, earning_ratio: int):
    db_courier = db.query(models.Courier).get(courier_id)
    db_all_completed_orders = db.query(models.CompletedCourierOrder) \
        .filter(models.CompletedCourierOrder.courier_id == courier_id) \
        .all()

    all_regions = []
    for completed_order in db_all_completed_orders:
        all_regions.append(completed_order.order_region)
    all_regions = list(set(all_regions))
    average_lead_time_in_regions = []
    for region in all_regions:
        db_completed_orders = db.query(models.CompletedCourierOrder) \
            .filter(models.CompletedCourierOrder.order_region == region) \
            .all()
        average_lead_time = 0
        count = 0
        for order in db_completed_orders:
            average_lead_time += order.lead_time
            count += 1
        average_lead_time /= count
        average_lead_time_in_regions.append(average_lead_time)

    t = min(average_lead_time_in_regions)
    rating = ((60 * 60 - min(t, 60 * 60)) / (60 * 60)) * 5
    db_courier.rating = float(format(rating, ".2f"))
    db_courier.earning += 500 * earning_ratio
    db.commit()
