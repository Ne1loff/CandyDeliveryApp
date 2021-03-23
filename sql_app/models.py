from sqlalchemy import Column, ForeignKey, Integer, String, Numeric
from sqlalchemy.orm import relationship

from .database import Base


class Courier(Base):
    __tablename__ = "courier"

    id = Column('courier_id', Integer, primary_key=True, nullable=False, index=True)
    type = Column('courier_type', String, nullable=False)
    rating = Column('courier_rating', Numeric, nullable=False, default=0.0)
    earnings = Column('courier_earnings', Integer, nullable=False, default=0)

    regions = relationship("CourierRegion", back_populates="courier")
    working_hours = relationship("CourierWorkingHours", back_populates="courier")


class CourierRegion(Base):
    __tablename__ = "courier_region"

    id = Column('id', Integer, primary_key=True, nullable=False)
    courier_id = Column('courier_id', Integer, ForeignKey("courier.courier_id"), nullable=False)
    region_id = Column('region_id', Integer, nullable=False)

    courier = relationship("Courier", back_populates="regions")


class CourierWorkingHours(Base):
    __tablename__ = "courier_working_hours"

    id = Column('id', Integer, primary_key=True, nullable=False)
    courier_id = Column('courier_id', Integer, ForeignKey("courier.courier_id"), nullable=False)
    courier_working_hours = Column('courier_working_hours', String, nullable=False)

    courier = relationship("Courier", back_populates="working_hours")


class Order(Base):
    __tablename__ = "order"

    id = Column('order_id', Integer, primary_key=True, nullable=False, index=True)
    weight = Column('order_weight', Numeric, nullable=False)
    region_id = Column('order_region_id', Integer, nullable=False)
    courier_id = Column('order_courier_id', Integer)

    delivery_hours = relationship("OrderDeliveryHours", back_populates="order")


class OrderDeliveryHours(Base):
    __tablename__ = "order_delivery_hours"

    order_id = Column('order_id', Integer, ForeignKey("order.order_id"), primary_key=True, nullable=False)
    delivery_hours = Column('order_delivery_hours', String, nullable=False)

    order = relationship("Order", back_populates="delivery_hours")
