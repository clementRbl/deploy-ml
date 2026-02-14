"""Endpoints pour interroger les données en base (buildings + historique prédictions)."""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func

from src.api.dependencies import DbDep
from src.db.models import Building, Prediction
from src.schemas.responses import (
    BuildingRecord,
    BuildingsListResponse,
    PredictionHistoryResponse,
    PredictionRecord,
)

router = APIRouter(prefix="/db", tags=["Database"])


@router.get("/buildings", response_model=BuildingsListResponse)
async def list_buildings(
    db: DbDep,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    building_type: str | None = Query(None, description="Filtrer par type de bâtiment"),
    property_type: str | None = Query(None, description="Filtrer par type de propriété"),
    neighborhood: str | None = Query(None, description="Filtrer par quartier"),
) -> BuildingsListResponse:
    """Liste les bâtiments en base avec pagination et filtres.

    Permet de consulter les données du dataset Seattle 2016.
    """
    query = db.query(Building)

    if building_type:
        query = query.filter(Building.building_type == building_type)
    if property_type:
        query = query.filter(Building.primary_property_type == property_type)
    if neighborhood:
        query = query.filter(Building.neighborhood == neighborhood)

    total = query.count()
    buildings = query.offset(skip).limit(limit).all()

    return BuildingsListResponse(
        total=total,
        buildings=[BuildingRecord.model_validate(b) for b in buildings],
    )


@router.get("/buildings/{building_id}", response_model=BuildingRecord)
async def get_building(building_id: int, db: DbDep) -> BuildingRecord:
    """Récupère un bâtiment par son OSEBuildingID."""
    building = db.query(Building).filter(Building.ose_building_id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail=f"Building {building_id} not found")

    return BuildingRecord.model_validate(building)


@router.get("/predictions/history", response_model=PredictionHistoryResponse)
async def list_predictions(
    db: DbDep,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    property_type: str | None = Query(None, description="Filtrer par type de propriété"),
) -> PredictionHistoryResponse:
    """Liste l'historique des prédictions avec pagination.

    Assure la traçabilité complète des interactions avec le modèle ML.
    """
    query = db.query(Prediction)

    if property_type:
        query = query.filter(Prediction.primary_property_type == property_type)

    total = query.count()
    predictions = query.order_by(Prediction.created_at.desc()).offset(skip).limit(limit).all()

    records = []
    for p in predictions:
        records.append(
            PredictionRecord(
                id=str(p.id),
                created_at=p.created_at,
                primary_property_type=p.primary_property_type,
                building_type=p.building_type,
                property_gfa_total=p.property_gfa_total,
                energy_prediction_kbtu=p.energy_prediction_kbtu,
                co2_prediction_tons=p.co2_prediction_tons,
                prediction_duration_ms=p.prediction_duration_ms,
                source=p.source,
            )
        )

    return PredictionHistoryResponse(total=total, predictions=records)


@router.get("/stats/buildings")
async def buildings_stats(db: DbDep) -> dict:
    """Statistiques agrégées sur les bâtiments en base."""
    total = db.query(Building).count()

    if total == 0:
        return {"total": 0, "message": "Aucun bâtiment en base"}

    stats = db.query(
        func.count(Building.id).label("total"),
        func.count(func.distinct(Building.building_type)).label("n_building_types"),
        func.count(func.distinct(Building.primary_property_type)).label("n_property_types"),
        func.count(func.distinct(Building.neighborhood)).label("n_neighborhoods"),
        func.avg(Building.site_energy_use).label("avg_energy_kbtu"),
        func.avg(Building.total_ghg_emissions).label("avg_ghg_tons"),
        func.min(Building.year_built).label("oldest_building"),
        func.max(Building.year_built).label("newest_building"),
    ).first()

    pred_count = db.query(Prediction).count()

    return {
        "buildings": {
            "total": stats[0],
            "building_types": stats[1],
            "property_types": stats[2],
            "neighborhoods": stats[3],
            "avg_energy_kbtu": round(stats[4], 2) if stats[4] else None,
            "avg_ghg_tons": round(stats[5], 2) if stats[5] else None,
            "oldest_building_year": stats[6],
            "newest_building_year": stats[7],
        },
        "predictions": {
            "total": pred_count,
        },
    }
