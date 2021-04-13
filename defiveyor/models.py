import logging

from sqlalchemy import Column, Integer, DateTime, String, Float, ForeignKey, Table
import sqlalchemy.engine
from sqlalchemy.orm import declarative_base, relationship

from defiveyor.utils import utcnow_rounded

Base = declarative_base()


class Asset(Base):
    __tablename__ = "asset"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, unique=True, nullable=False)


class Network(Base):
    __tablename__ = "network"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, unique=True, nullable=False)


class Protocol(Base):
    __tablename__ = "protocol"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, unique=True, nullable=False)


class AssetReturnRecord(Base):
    __tablename__ = "asset_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    network_id = Column(Integer, ForeignKey("network.id"))
    protocol_id = Column(Integer, ForeignKey("protocol.id"))
    asset_id = Column(Integer, ForeignKey("asset.id"))
    date_recorded = Column(DateTime, default=utcnow_rounded, nullable=False)
    apy = Column(Float, nullable=False)


asset_group_record_association = Table(
    "asset_group_record_association",
    Base.metadata,
    Column("asset_id", Integer, ForeignKey("asset.id")),
    Column("asset_group_record_id", Integer, ForeignKey("asset_group_record.id")),
)


class AssetGroupReturnRecord(Base):
    __tablename__ = "asset_group_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    network_id = Column(Integer, ForeignKey("network.id"))
    protocol_id = Column(Integer, ForeignKey("protocol.id"))
    assets = relationship("Asset", secondary=asset_group_record_association)
    date_recorded = Column(DateTime, default=utcnow_rounded, nullable=False)
    apy = Column(Float, nullable=False)


logger = logging.getLogger("models")


def create_all(engine: sqlalchemy.engine.Engine):
    logger.info("creating all models")
    Base.metadata.create_all(engine)
    logger.info("created all models")
