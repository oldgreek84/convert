from db import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, LargeBinary


class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    job_id = Column(String)
    link = Column(String)
    data = Column(LargeBinary)
