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
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"validation_error": {"couriers": exc.errors()}})
    )


@app.post('/couriers', status_code=201, response_model=dict)
def create_couriers(data: Dict[str, List[schemas.CourierDto]], db: Session = Depends(get_db)):  # TODO: change to create couriers
    list_couriers = []
    for courier in data.get("data"):
        list_couriers.append({"id": courier.courier_id})
        crud.create_courier(db, courier)
    return {"couriers": list_couriers}


@app.get('/couriers/{courier_id}', response_model=schemas.Courier)
def get_full_courier(courier_id: int, db: Session = Depends(get_db)):
    db_courier = crud.get_courier_by_id(db, courier_id=courier_id)
    if db_courier is None:
        raise HTTPException(status_code=404, detail="Courier not found")
    return db_courier


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
