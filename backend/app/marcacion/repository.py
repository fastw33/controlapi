# app/marcacion/repository.py
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.marcacion.model import Marcacion
from app.personal.model import Personal
from app.vectores.model import PersonalVectores

_ALLOWED_TYPES = {"entrada", "salida", "on_almuerzo", "off_almuerzo"}


def _apply_marcacion_filters(stmt, *, tipo: Optional[str], personal_id: Optional[int], desde: Optional[datetime], hasta: Optional[datetime]):
    conds = []
    if tipo:
        if tipo in _ALLOWED_TYPES:
            conds.append(Marcacion.tipo == tipo)
    if personal_id is not None:
        conds.append(Marcacion.personal_id == personal_id)
    if desde is not None:
        conds.append(Marcacion.fecha_hora >= desde)
    if hasta is not None:
        conds.append(Marcacion.fecha_hora <= hasta)
    if conds:
        stmt = stmt.where(and_(*conds))
    return stmt


def create(db: Session, data: dict) -> Marcacion:
    """
    Crea una marcación. 'data' debe contener únicamente columnas válidas del modelo Marcacion.
    (No persistir biometría aquí; solo marcación base).
    """
    obj = Marcacion(**data)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_with_personal(
    db: Session,
    *,
    limit: Optional[int] = None,
    offset: int = 0,
    tipo: Optional[str] = None,
    personal_id: Optional[int] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
):
    """
    Lista marcaciones con datos básicos de Personal.
    Devuelve filas con atributos:
      id, personal_id, tipo, fecha_hora, dispositivo, observacion,
      justificacion, evidencia_url, aprobado, creado_en,
      documento, nombres, apellidos
    """
    stmt = (
        select(
            Marcacion.id,
            Marcacion.personal_id,
            Marcacion.tipo,
            Marcacion.fecha_hora,
            Marcacion.dispositivo,
            Marcacion.observacion,
            Marcacion.justificacion,
            Marcacion.evidencia_url,
            Marcacion.aprobado,
            Marcacion.creado_en,
            Personal.documento,
            Personal.nombres,
            Personal.apellidos,
        )
        .select_from(Marcacion)
        .join(Personal, Personal.id == Marcacion.personal_id)
    )

    stmt = _apply_marcacion_filters(
        stmt,
        tipo=tipo,
        personal_id=personal_id,
        desde=desde,
        hasta=hasta,
    )

    stmt = stmt.order_by(Marcacion.fecha_hora.desc(), Marcacion.id.desc())

    # Nota: en MySQL offset requiere limit; mantenemos tu lógica original
    if limit is not None:
        stmt = stmt.limit(limit).offset(offset)

    return db.execute(stmt).all()


def count_with_personal(
    db: Session,
    *,
    tipo: Optional[str] = None,
    personal_id: Optional[int] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
) -> int:
    stmt = (
        select(Marcacion.id)
        .select_from(Marcacion)
        .join(Personal, Personal.id == Marcacion.personal_id)
    )
    stmt = _apply_marcacion_filters(
        stmt,
        tipo=tipo,
        personal_id=personal_id,
        desde=desde,
        hasta=hasta,
    )
    return db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()


def get_with_personal(db: Session, marcacion_id: int):
    """
    Obtiene una marcación puntual con datos básicos de Personal.
    """
    stmt = (
        select(
            Marcacion.id,
            Marcacion.personal_id,
            Marcacion.tipo,
            Marcacion.fecha_hora,
            Marcacion.dispositivo,
            Marcacion.observacion,
            Marcacion.justificacion,
            Marcacion.evidencia_url,
            Marcacion.aprobado,
            Marcacion.creado_en,
            Personal.documento,
            Personal.nombres,
            Personal.apellidos,
        )
        .select_from(Marcacion)
        .join(Personal, Personal.id == Marcacion.personal_id)
        .where(Marcacion.id == marcacion_id)
    )
    return db.execute(stmt).one_or_none()


def fetch_all_vectors_joined(db: Session):
    """
    Obtiene todos los vectores faciales junto con datos de Personal.
    Solo para comparación EFÍMERA (no persistir la foto de input).
    """
    stmt = (
        select(
            Personal.id.label("personal_id"),
            Personal.documento,
            Personal.nombres,
            Personal.apellidos,
            PersonalVectores.vector1,
            PersonalVectores.vector2,
            PersonalVectores.vector3,
            PersonalVectores.vector4,
            PersonalVectores.vector5,
        )
        .select_from(Personal)
        .join(PersonalVectores, PersonalVectores.id_personal == Personal.id)
    )
    return db.execute(stmt).all()


def get_vectors_for_person(db: Session, personal_id: int):
    """
    Obtiene vectores para una persona específica (para verificación en memoria).
    """
    stmt = (
        select(
            Personal.id.label("personal_id"),
            Personal.documento,
            Personal.nombres,
            Personal.apellidos,
            PersonalVectores.vector1,
            PersonalVectores.vector2,
            PersonalVectores.vector3,
            PersonalVectores.vector4,
            PersonalVectores.vector5,
        )
        .select_from(Personal)
        .join(PersonalVectores, PersonalVectores.id_personal == Personal.id)
        .where(Personal.id == personal_id)
    )
    return db.execute(stmt).one_or_none()
