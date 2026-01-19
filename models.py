# models.py
from datetime import datetime
from app import db

class Permiso(db.Model):
    __tablename__ = "datos_financieros"

    id = db.Column(db.Integer, primary_key=True)
    bloque = db.Column(db.String(50))
    sucursal = db.Column(db.String(100), nullable=False)
    tipo_permiso = db.Column(db.String(100))
    existencia = db.Column(db.String(50))
    fecha_expedicion = db.Column(db.Date)
    fecha_renovacion = db.Column(db.Date)
    estatus = db.Column(db.String(30), default="VIGENTE")
    estatus_legal = db.Column(db.String(100))
    asigna = db.Column(db.String(100))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
