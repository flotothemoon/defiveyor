import logging

from sqlalchemy import Column, Integer, DateTime, String, Float
import sqlalchemy.engine
from sqlalchemy.orm import declarative_base

from defiveyor.utils import utcnow_rounded

Base = declarative_base()


# TODO @Cleanup: normalise Records with references to Asset, Network, Protocol.. tables
class AssetReturnRecord(Base):
    __tablename__ = "asset_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    network = Column(String, nullable=False)
    protocol = Column(String, nullable=False)
    asset = Column(String, nullable=False)
    date_recorded = Column(DateTime, default=utcnow_rounded, nullable=False)
    apy = Column(Float, nullable=False)


class AssetPairReturnRecord(Base):
    __tablename__ = "asset_pair_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    network = Column(String, nullable=False)
    protocol = Column(String, nullable=False)
    asset_0 = Column(String, nullable=False)
    asset_1 = Column(String, nullable=False)
    date_recorded = Column(DateTime, default=utcnow_rounded, nullable=False)
    apy = Column(Float, nullable=False)


logger = logging.getLogger("models")


def create_all(engine: sqlalchemy.engine.Engine):
    logger.info("creating all models")
    Base.metadata.create_all(engine)
    logger.info("created all models")
