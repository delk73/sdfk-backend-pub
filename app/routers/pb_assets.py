from fastapi import APIRouter, Response, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from app.utils.proto_converter import proto_to_asset, asset_to_proto
from app.proto import asset_pb2
from app import models
import app.models.db as db
from app.services.asset_utils import format_nested_asset_response

from app.schema_version import require_schema_version


router = APIRouter()


@router.post(
    "/",
    response_class=Response,
    responses={200: {"content": {"application/x-protobuf": {}}}},
)
def create_asset_proto(
    body: bytes = Body(..., media_type="application/x-protobuf"),
    db: Session = Depends(db.get_db),
    _: None = Depends(require_schema_version),
) -> Response:
    proto_obj = asset_pb2.Asset()
    proto_obj.ParseFromString(body)
    asset_data = proto_to_asset(proto_obj)

    db_obj = models.ProtoAsset(
        name=asset_data.get("name", ""),
        description=asset_data.get("description"),
        proto_blob=body,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    return Response(
        content=db_obj.proto_blob,
        media_type="application/x-protobuf",
        headers={
            "Content-Disposition": f"attachment; filename=asset-{db_obj.proto_asset_id}.pb"
        },
    )


@router.post(
    "/from-synesthetic/{syn_asset_id}",
    response_class=Response,
    responses={200: {"content": {"application/x-protobuf": {}}}},
)
def create_from_synesthetic(
    syn_asset_id: int,
    db: Session = Depends(db.get_db),
    _: None = Depends(require_schema_version),
) -> Response:
    syn_asset = (
        db.query(models.SynestheticAsset)
        .filter(models.SynestheticAsset.synesthetic_asset_id == syn_asset_id)
        .first()
    )
    if syn_asset is None:
        raise HTTPException(status_code=404, detail="Synesthetic asset not found")

    asset_dict = format_nested_asset_response(
        syn_asset,
        syn_asset.shader,
        syn_asset.control,
        syn_asset.tone,
        syn_asset.haptic,
        syn_asset.modulation.modulations if syn_asset.modulation else None,
    )
    proto_bytes = asset_to_proto(asset_dict).SerializeToString()

    db_obj = (
        db.query(models.ProtoAsset)
        .filter(models.ProtoAsset.proto_asset_id == syn_asset_id)
        .first()
    )
    if db_obj is None:
        db_obj = models.ProtoAsset(
            proto_asset_id=syn_asset_id,
            name=asset_dict.get("name", ""),
            description=asset_dict.get("description"),
            proto_blob=proto_bytes,
        )
        db.add(db_obj)
    else:
        db_obj.name = asset_dict.get("name", "")
        db_obj.description = asset_dict.get("description")
        db_obj.proto_blob = proto_bytes
    db.commit()
    return Response(
        content=db_obj.proto_blob,
        media_type="application/x-protobuf",
        headers={
            "Content-Disposition": f"attachment; filename=asset-{db_obj.proto_asset_id}.pb"
        },
    )


@router.get(
    "/{asset_id}",
    response_class=Response,
    responses={200: {"content": {"application/x-protobuf": {}}}},
)
def get_asset_proto(asset_id: int, db: Session = Depends(db.get_db)) -> Response:
    db_obj = (
        db.query(models.ProtoAsset)
        .filter(models.ProtoAsset.proto_asset_id == asset_id)
        .first()
    )
    if db_obj is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return Response(
        content=db_obj.proto_blob,
        media_type="application/x-protobuf",
        headers={
            "Content-Disposition": f"attachment; filename=asset-{db_obj.proto_asset_id}.pb"
        },
    )


@router.put(
    "/{asset_id}",
    response_class=Response,
    responses={200: {"content": {"application/x-protobuf": {}}}},
)
def update_asset_proto(
    asset_id: int,
    body: bytes = Body(..., media_type="application/x-protobuf"),
    db: Session = Depends(db.get_db),
    _: None = Depends(require_schema_version),
) -> Response:
    db_obj = (
        db.query(models.ProtoAsset)
        .filter(models.ProtoAsset.proto_asset_id == asset_id)
        .first()
    )
    if db_obj is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    proto_obj = asset_pb2.Asset()
    proto_obj.ParseFromString(body)
    asset_data = proto_to_asset(proto_obj)

    db_obj.name = asset_data.get("name", "")
    db_obj.description = asset_data.get("description")
    db_obj.proto_blob = body
    db.commit()
    db.refresh(db_obj)

    return Response(
        content=db_obj.proto_blob,
        media_type="application/x-protobuf",
        headers={
            "Content-Disposition": f"attachment; filename=asset-{db_obj.proto_asset_id}.pb"
        },
    )


@router.delete("/{asset_id}")
def delete_asset_proto(
    asset_id: int, db: Session = Depends(db.get_db), _: None = Depends(require_schema_version)
):
    db_obj = (
        db.query(models.ProtoAsset)
        .filter(models.ProtoAsset.proto_asset_id == asset_id)
        .first()
    )
    if db_obj is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(db_obj)
    db.commit()
    return {"status": "deleted"}
