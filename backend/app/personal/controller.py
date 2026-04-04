# app/personal/controller.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.personal.schema import PersonalCreate, PersonalOut, HorarioOut
from app.personal import service

router = APIRouter(prefix="/personal", tags=["personal"])

@router.post("", response_model=PersonalOut, status_code=201)
def crear_persona(payload: PersonalCreate, db: Session = Depends(get_db)):
    return service.crear_personal(db, payload)

@router.get("", response_model=list[PersonalOut])
def listar(db: Session = Depends(get_db)):
    return service.listar_personal(db)

@router.get("/{personal_id}", response_model=PersonalOut)
def obtener(personal_id: int, db: Session = Depends(get_db)):
    return service.obtener_personal(db, personal_id)

@router.get("/horario/documento", response_model=HorarioOut)
def obtener_horario_por_documento(
    documento: str = Query(..., description="Documento de la persona"),
    db: Session = Depends(get_db)
):
    """Obtiene el horario de entrada y salida de una persona por documento"""
    return service.obtener_horario_por_documento(db, documento)
