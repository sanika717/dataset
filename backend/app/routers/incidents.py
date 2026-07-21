from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.get("", response_model=list[schemas.IncidentOut])
def list_incidents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    camera_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return crud.get_incidents(
        db, skip=skip, limit=limit, status=status, severity=severity, camera_id=camera_id
    )


@router.post("", response_model=schemas.IncidentOut, status_code=201)
def create_incident(
    incident: schemas.IncidentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return crud.create_incident(db, incident)


@router.get("/{incident_id}", response_model=schemas.IncidentOut)
def get_incident(
    incident_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    db_incident = crud.get_incident(db, incident_id)
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db_incident


@router.put("/{incident_id}", response_model=schemas.IncidentOut)
def update_incident(
    incident_id: int,
    incident: schemas.IncidentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_incident = crud.update_incident(db, incident_id, incident)
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db_incident


@router.delete("/{incident_id}", status_code=204)
def delete_incident(
    incident_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    if not crud.delete_incident(db, incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
