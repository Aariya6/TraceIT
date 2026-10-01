from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__='users'
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(100)); email: Mapped[str]=mapped_column(String(190),unique=True,index=True); password_hash: Mapped[str]=mapped_column(String(500)); is_active: Mapped[bool]=mapped_column(Boolean,default=True); role: Mapped[str]=mapped_column(String(30),default='citizen'); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    observations=relationship('Observation',back_populates='user',cascade='all, delete-orphan'); bookmarks=relationship('Bookmark',back_populates='user',cascade='all, delete-orphan'); interventions=relationship('Intervention',back_populates='created_by')

class WaterBody(Base):
    __tablename__='water_bodies'
    id: Mapped[int]=mapped_column(primary_key=True); slug: Mapped[str]=mapped_column(String(100),unique=True,index=True); name: Mapped[str]=mapped_column(String(160)); city: Mapped[str]=mapped_column(String(120)); country: Mapped[str]=mapped_column(String(80),default='India'); latitude: Mapped[float]=mapped_column(Float); longitude: Mapped[float]=mapped_column(Float); status: Mapped[str]=mapped_column(String(50),default='RESEARCH RECORD'); description: Mapped[str]=mapped_column(Text,default=''); source_period: Mapped[str]=mapped_column(String(100),default=''); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    observations=relationship('Observation',back_populates='water_body',cascade='all, delete-orphan'); bookmarks=relationship('Bookmark',back_populates='water_body',cascade='all, delete-orphan'); incidents=relationship('Incident',back_populates='water_body',cascade='all, delete-orphan'); interventions=relationship('Intervention',back_populates='water_body',cascade='all, delete-orphan'); protocols=relationship('FieldProtocol',back_populates='water_body',cascade='all, delete-orphan')
River=WaterBody

class Observation(Base):
    __tablename__='observations'; __table_args__=(Index('ix_obs_body_time','water_body_id','observed_at'),Index('ix_obs_site_time','site_code','observed_at'))
    id: Mapped[int]=mapped_column(primary_key=True); water_body_id: Mapped[int]=mapped_column(ForeignKey('water_bodies.id',ondelete='CASCADE'),index=True); user_id: Mapped[int|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL'),index=True); observed_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True); source: Mapped[str]=mapped_column(String(80)); source_record_id: Mapped[str|None]=mapped_column(String(160),index=True); note: Mapped[str]=mapped_column(Text,default=''); site_code: Mapped[str]=mapped_column(String(32),index=True); lat: Mapped[float]=mapped_column(Float); lon: Mapped[float]=mapped_column(Float); temperature_c: Mapped[float|None]=mapped_column(Float); ph: Mapped[float|None]=mapped_column(Float); tds_mg_l: Mapped[float|None]=mapped_column(Float); do_mg_l: Mapped[float|None]=mapped_column(Float); bod_mg_l: Mapped[float|None]=mapped_column(Float); cod_mg_l: Mapped[float|None]=mapped_column(Float); nitrate_mg_l: Mapped[float|None]=mapped_column(Float); phosphate_mg_l: Mapped[float|None]=mapped_column(Float); conductivity_us_cm: Mapped[float|None]=mapped_column(Float); biodiversity_signal: Mapped[float]=mapped_column(Float,default=0); human_signal: Mapped[float]=mapped_column(Float,default=0); image_signal: Mapped[float]=mapped_column(Float,default=0); quality_score: Mapped[float]=mapped_column(Float,default=1); provenance: Mapped[dict]=mapped_column(JSON,default=dict); validation: Mapped[dict]=mapped_column(JSON,default=dict)
    water_body=relationship('WaterBody',back_populates='observations'); user=relationship('User',back_populates='observations')

class Bookmark(Base):
    __tablename__='bookmarks'; __table_args__=(UniqueConstraint('user_id','water_body_id',name='uq_user_water_body_bookmark'),)
    id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id',ondelete='CASCADE')); water_body_id: Mapped[int]=mapped_column(ForeignKey('water_bodies.id',ondelete='CASCADE')); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); user=relationship('User',back_populates='bookmarks'); water_body=relationship('WaterBody',back_populates='bookmarks')

class Incident(Base):
    __tablename__='incidents'
    id: Mapped[int]=mapped_column(primary_key=True); water_body_id: Mapped[int]=mapped_column(ForeignKey('water_bodies.id',ondelete='CASCADE')); code: Mapped[str]=mapped_column(String(32),unique=True); detected_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); severity: Mapped[str]=mapped_column(String(24)); confidence: Mapped[float]=mapped_column(Float); title: Mapped[str]=mapped_column(String(180)); summary: Mapped[str]=mapped_column(Text); evidence_count: Mapped[int]=mapped_column(default=0); evidence: Mapped[dict]=mapped_column(JSON,default=dict); water_body=relationship('WaterBody',back_populates='incidents')

class FieldProtocol(Base):
    __tablename__='field_protocols'
    id: Mapped[int]=mapped_column(primary_key=True); water_body_id: Mapped[int]=mapped_column(ForeignKey('water_bodies.id',ondelete='CASCADE')); title: Mapped[str]=mapped_column(String(180)); version: Mapped[str]=mapped_column(String(30)); steps: Mapped[list]=mapped_column(JSON); required_measurements: Mapped[list]=mapped_column(JSON); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); water_body=relationship('WaterBody',back_populates='protocols')

class Intervention(Base):
    __tablename__='interventions'
    id: Mapped[int]=mapped_column(primary_key=True); water_body_id: Mapped[int]=mapped_column(ForeignKey('water_bodies.id',ondelete='CASCADE')); created_by_id: Mapped[int|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL')); title: Mapped[str]=mapped_column(String(180)); status: Mapped[str]=mapped_column(String(30),default='planned'); action_type: Mapped[str]=mapped_column(String(60)); notes: Mapped[str]=mapped_column(Text,default=''); target_date: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); outcome: Mapped[str]=mapped_column(Text,default=''); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); water_body=relationship('WaterBody',back_populates='interventions'); created_by=relationship('User',back_populates='interventions')

class DataSource(Base):
    __tablename__='data_sources'
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(150)); kind: Mapped[str]=mapped_column(String(40)); url: Mapped[str]=mapped_column(String(500)); description: Mapped[str]=mapped_column(Text,default=''); update_frequency: Mapped[str]=mapped_column(String(80),default=''); enabled: Mapped[bool]=mapped_column(Boolean,default=True); last_checked_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); metadata_json: Mapped[dict]=mapped_column(JSON,default=dict)
