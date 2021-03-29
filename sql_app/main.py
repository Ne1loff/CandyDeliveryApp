from typing import List, Dict

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from sql_app import schemas, crud, models
from sql_app.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    couriers_v_e = []
    is_courier = True
    if exc.body.get("data")[0].get("courier_id") is None:
        is_courier = False
        type_obj = "orders"
    else:
        type_obj = "couriers"

    print(exc.errors())

    for error in exc.errors():
        error_number = error.get("loc")[2]
        if is_courier:
            element_id = exc.body.get("data")[error_number].get("courier_id")
        else:
            element_id = exc.body.get("data")[error_number].get("order_id")
        couriers_v_e.append({"id": element_id})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"validation_error": {type_obj: couriers_v_e}})
    )


@app.post("/couriers", status_code=201, response_model=dict)
def create_couriers(data: Dict[str, List[schemas.CourierDto]],
                    db: Session = Depends(get_db)):
    created_couriers = []
    for courier in data.get("data"):
        created_couriers.append({"id": courier.courier_id})
        crud.create_courier(db, courier)
    return {"couriers": created_couriers}


@app.get("/couriers/{courier_id}", response_model=dict)
def get_full_courier(courier_id: int, db: Session = Depends(get_db)):
    db_courier = crud.get_courier_by_id(db, courier_id=courier_id)
    if db_courier is None:
        raise HTTPException(status_code=404, detail="Courier not found")

    if db.query(models.CompletedCourierOrder).filter(models.CompletedCourierOrder.courier_id == courier_id).all():
        courier = {
            "courier_id": db_courier.courier_id,
            "courier_type": db_courier.courier_type,
            "regions": db_courier.regions,
            "working_hours": db_courier.working_hours,
            "rating": db_courier.rating,
            "earning": db_courier.earning
        }
    else:
        courier = {
            "courier_id": db_courier.courier_id,
            "courier_type": db_courier.courier_type,
            "regions": db_courier.regions,
            "working_hours": db_courier.working_hours,
            "earning": db_courier.earning
        }
    return courier


@app.post("/orders", status_code=201, response_model=dict)
def create_order(data: Dict[str, List[schemas.OrderDto]], db: Session = Depends(get_db)):
    created_orders = []
    for order in data.get("data"):
        created_orders.append({"id": order.order_id})
        crud.create_order(db, order)
    return {"orders": created_orders}


@app.post("/orders/assign", status_code=200, response_model=dict)
def assign_order(courier: Dict[str, int], db: Session = Depends(get_db)):
    assigned_orders = []

    courier = crud.get_courier_by_id(db, courier.get("courier_id"))
    if courier is None:
        raise HTTPException(status_code=400, detail="Bad request")

    orders, assign_time = crud.assign_order(db, courier)
    orders_id = []
    for order in orders:
        if isinstance(order, models.Order):
            orders_id.append(order.id)
        else:
            orders_id.append(order.order_id)
    orders_id = list(set(orders_id))
    for order in orders_id:
        assigned_orders.append({"id": order})

    if assigned_orders:
        dict_ = {
            "orders": assigned_orders,
            "assign_time": assign_time
        }
    else:
        dict_ = {
            "orders": assigned_orders
        }
    return dict_


@app.patch("/couriers/{courier_id}", status_code=200, response_model=schemas.CourierDto)
def update_courier(courier_id: int, changes: Dict, db: Session = Depends(get_db)):
    fields = [
        "courier_id",
        "courier_type",
        "regions",
        "working_hours"
    ]
    keys = changes.keys()
    for key in keys:
        if key not in fields:
            raise HTTPException(status_code=400, detail="Bad request")
    courier_dto = crud.update_courier(db, changes, courier_id)
    crud.check_courier(db, courier_id)
    return courier_dto


@app.post("/orders/complete", status_code=200, response_model=dict)
def order_complete(order_info: Dict, db: Session = Depends(get_db)):
    order_id = crud.order_complete(db, order_info)
    if order_id is None:
        raise HTTPException(status_code=400, detail="Bad request")
    return {"order_id": order_id}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
