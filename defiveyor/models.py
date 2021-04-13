from sqlalchemy import Column, Integer, DateTime, String, Float
from sqlalchemy.orm import declarative_base, relationship

from defiveyor.utils import utcnow_rounded

Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    symbol = Column(String, nullable=False, unique=True)


class Network(Base):
    __tablename__ = "networks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)


class Protocol(Base):
    __tablename__ = "protocols"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)


# TODO @Cleanup: normalise Records with references to Asset, Network, Protocol.. tables
class AssetReturnRecord(Base):
    __tablename__ = "asset_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    network = relationship("Network")
    protocol = relationship("Protocol")
    asset = relationship("Asset")
    date_recorded = Column(DateTime, default=utcnow_rounded, nullable=False)
    apy = Column(Float, nullable=False)


class AssetPairReturnRecord(Base):
    __tablename__ = "asset_pair_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    network = relationship("Network")
    protocol = relationship("Protocol")
    asset_0 = relationship("Asset")
    asset_1 = relationship("Asset")
    date_recorded = Column(DateTime, default=utcnow_rounded, nullable=False)
    apy = Column(Float, nullable=False)
