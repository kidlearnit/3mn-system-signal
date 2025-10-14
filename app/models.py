from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, TIMESTAMP, Enum, UniqueConstraint, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .db import Base
import enum
from datetime import datetime

class TFEnum(enum.Enum):
    m1='1m'; m2='2m'; m5='5m'; m15='15m'; m30='30m'; h1='1h'; h4='4h'; d1='1D'

class Symbol(Base):
    __tablename__ = "symbols"
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False)
    exchange = Column(String(20), nullable=False)
    currency = Column(String(10), default='VND')
    active = Column(Boolean, default=True)

class Candle1m(Base):
    __tablename__ = "candles_1m"
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    ts = Column(TIMESTAMP, nullable=False)
    open = Column(DECIMAL(18,6), nullable=False)
    high = Column(DECIMAL(18,6), nullable=False)
    low  = Column(DECIMAL(18,6), nullable=False)
    close= Column(DECIMAL(18,6), nullable=False)
    volume= Column(DECIMAL(20,2))

class CandleTF(Base):
    __tablename__ = "candles_tf"
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    timeframe = Column(Enum(TFEnum), nullable=False)
    ts = Column(TIMESTAMP, nullable=False)
    open = Column(DECIMAL(18,6), nullable=False)
    high = Column(DECIMAL(18,6), nullable=False)
    low  = Column(DECIMAL(18,6), nullable=False)
    close= Column(DECIMAL(18,6), nullable=False)
    volume= Column(DECIMAL(20,2))

class MACD(Base):
    __tablename__ = "indicators_macd"
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    timeframe = Column(Enum(TFEnum), nullable=False)
    ts = Column(TIMESTAMP, nullable=False)
    macd = Column(DECIMAL(18,6), nullable=False)
    macd_signal = Column(DECIMAL(18,6), nullable=False)  # đổi tên
    hist = Column(DECIMAL(18,6), nullable=False)

class Bars(Base):
    __tablename__ = "indicators_bars"
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    timeframe = Column(Enum(TFEnum), nullable=False)
    ts = Column(TIMESTAMP, nullable=False)
    bars = Column(DECIMAL(18,6), nullable=False)

class Strategy(Base):
    __tablename__ = "trade_strategies"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String)

class TFName(Base):
    __tablename__ = "timeframes"
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)

class IndicatorName(Base):
    __tablename__ = "indicators"
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)

class Zone(Base):
    __tablename__ = "zones"
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)

class StrategyThreshold(Base):
    __tablename__ = "strategy_thresholds"
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("trade_strategies.id"), nullable=False)
    timeframe_id = Column(Integer, ForeignKey("timeframes.id"), nullable=False)
    __table_args__ = (UniqueConstraint('strategy_id','timeframe_id', name='uniq_strategy_tf'),)

class ThresholdValue(Base):
    __tablename__ = "threshold_values"
    id = Column(Integer, primary_key=True)
    threshold_id = Column(Integer, ForeignKey("strategy_thresholds.id"), nullable=False)
    indicator_id = Column(Integer, ForeignKey("indicators.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    comparison = Column(String(10), nullable=False, default='>=')
    min_value = Column(DECIMAL(18,6))
    max_value = Column(DECIMAL(18,6))
    __table_args__ = (UniqueConstraint('threshold_id','indicator_id','zone_id', name='uniq_threshold'),)

class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    timeframe = Column(Enum('1m','2m','5m','15m','30m','1h','4h','1D'), nullable=False)
    ts = Column(TIMESTAMP, nullable=False)
    strategy_id = Column(Integer, ForeignKey("trade_strategies.id"), nullable=False)
    signal_type = Column(String(30), nullable=False)
    details = Column(JSON)
    __table_args__ = (UniqueConstraint('symbol_id','timeframe','ts','strategy_id','signal_type', name='uniq_signal'),)

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    nodes = Column(JSON, nullable=False)
    connections = Column(JSON, nullable=False)
    properties = Column(JSON)
    workflow_meta = Column(JSON, name='metadata')
    status = Column(Enum('active', 'inactive', 'draft'), default='draft')
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
