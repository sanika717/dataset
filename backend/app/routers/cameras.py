from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])


@router.get("", response_model=list[schemas.CameraOut])
def list_cameras(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return crud.get_cameras(db, skip=skip, limit=limit)


@router.post("", response_model=schemas.CameraOut, status_code=201)
def create_camera(
    camera: schemas.CameraCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return crud.create_camera(db, camera)


@router.get("/{camera_id}", response_model=schemas.CameraOut)
def get_camera(
    camera_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    db_camera = crud.get_camera(db, camera_id)
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera


@router.put("/{camera_id}", response_model=schemas.CameraOut)
def update_camera(
    camera_id: int,
    camera: schemas.CameraUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_camera = crud.update_camera(db, camera_id, camera)
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera


@router.delete("/{camera_id}", status_code=204)
def delete_camera(
    camera_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    if not crud.delete_camera(db, camera_id):
        raise HTTPException(status_code=404, detail="Camera not found")
