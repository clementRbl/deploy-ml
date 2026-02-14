#!/usr/bin/env python3
"""Scripts pour interroger les données et interagir avec le modèle ML via la base de données.

Usage:
    # Statistiques globales
    python scripts/query_db.py --stats

    # Lister les bâtiments (avec filtres)
    python scripts/query_db.py --buildings --type NonResidential --limit 10

    # Historique des prédictions
    python scripts/query_db.py --predictions --limit 20

    # Prédiction via la base de données (input → modèle → output → DB)
    python scripts/query_db.py --predict --building-id 1

    # Top N bâtiments énergivores
    python scripts/query_db.py --top-energy 10

    # Comparaison prédictions vs réel
    python scripts/query_db.py --compare
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import desc, text

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import logger
from src.db.database import SessionLocal
from src.db.models import Building, Prediction


def show_stats() -> None:
    """Affiche les statistiques globales de la base."""
    session = SessionLocal()
    try:
        b_count = session.query(Building).count()
        p_count = session.query(Prediction).count()

        print("\n" + "=" * 60)
        print("  STATISTIQUES BASE DE DONNÉES — deploy-ml")
        print("=" * 60)
        print(f"\n  Bâtiments en base : {b_count}")
        print(f"  Prédictions en base : {p_count}")

        if b_count > 0:
            stats = session.execute(
                text("""
                    SELECT
                        COUNT(DISTINCT building_type) as types,
                        COUNT(DISTINCT primary_property_type) as prop_types,
                        COUNT(DISTINCT neighborhood) as neighborhoods,
                        ROUND(AVG(site_energy_use)::numeric, 0) as avg_energy,
                        ROUND(AVG(total_ghg_emissions)::numeric, 1) as avg_ghg,
                        MIN(year_built) as min_year,
                        MAX(year_built) as max_year
                    FROM buildings
                """)
            ).fetchone()

            print("\n  --- Bâtiments ---")
            print(f"  Types de bâtiment : {stats[0]}")
            print(f"  Types de propriété : {stats[1]}")
            print(f"  Quartiers : {stats[2]}")
            print(f"  Énergie moyenne : {stats[3]:,} kBtu")
            print(f"  Émissions moyennes : {stats[4]} tonnes CO2")
            print(f"  Années de construction : {stats[5]} - {stats[6]}")

            # Répartition par type
            types = session.execute(
                text("""
                    SELECT building_type, COUNT(*) as cnt
                    FROM buildings
                    GROUP BY building_type
                    ORDER BY cnt DESC
                """)
            ).fetchall()
            print("\n  Répartition par type :")
            for t_name, cnt in types:
                print(f"    {t_name}: {cnt}")

        if p_count > 0:
            p_stats = session.execute(
                text("""
                    SELECT
                        ROUND(AVG(energy_prediction_kbtu)::numeric, 0) as avg_e,
                        ROUND(AVG(co2_prediction_tons)::numeric, 2) as avg_co2,
                        ROUND(AVG(prediction_duration_ms)::numeric, 1) as avg_ms,
                        MIN(created_at) as first,
                        MAX(created_at) as last
                    FROM predictions
                """)
            ).fetchone()
            print("\n  --- Prédictions ---")
            print(f"  Énergie moyenne prédite : {p_stats[0]:,} kBtu")
            print(f"  CO2 moyen prédit : {p_stats[1]} tonnes")
            print(f"  Durée moyenne : {p_stats[2]} ms")
            print(f"  Première prédiction : {p_stats[3]}")
            print(f"  Dernière prédiction : {p_stats[4]}")

        print("\n" + "=" * 60)

    finally:
        session.close()


def list_buildings(building_type: str | None = None, limit: int = 20) -> None:
    """Liste les bâtiments avec filtres optionnels."""
    session = SessionLocal()
    try:
        query = session.query(Building)
        if building_type:
            query = query.filter(Building.building_type == building_type)

        buildings = query.limit(limit).all()
        print(f"\n  Bâtiments ({len(buildings)} affichés) :")
        print("-" * 100)
        print(f"  {'ID':<8} {'Type':<20} {'Propriété':<25} {'Nom':<30} {'Énergie (kBtu)':<15}")
        print("-" * 100)

        for b in buildings:
            name = (b.property_name or "N/A")[:28]
            energy = f"{b.site_energy_use:,.0f}" if b.site_energy_use else "N/A"
            print(
                f"  {b.ose_building_id:<8} {b.building_type:<20} "
                f"{b.primary_property_type[:23]:<25} {name:<30} {energy:<15}"
            )

    finally:
        session.close()


def list_predictions(limit: int = 20) -> None:
    """Affiche l'historique des prédictions."""
    session = SessionLocal()
    try:
        preds = session.query(Prediction).order_by(desc(Prediction.created_at)).limit(limit).all()

        if not preds:
            print("\n  Aucune prédiction en base.")
            return

        print(f"\n  Dernières prédictions ({len(preds)}) :")
        print("-" * 110)
        print(
            f"  {'ID':<10} {'Date':<22} {'Type':<20} "
            f"{'Énergie (kBtu)':<18} {'CO2 (t)':<12} {'Durée (ms)':<12}"
        )
        print("-" * 110)

        for p in preds:
            pid = str(p.id)[:8]
            date = p.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ptype = (p.primary_property_type or "N/A")[:18]
            duration = f"{p.prediction_duration_ms:.1f}" if p.prediction_duration_ms else "N/A"
            print(
                f"  {pid:<10} {date:<22} {ptype:<20} "
                f"{p.energy_prediction_kbtu:>14,.0f}    {p.co2_prediction_tons:>8.2f}    {duration:>8}"
            )

    finally:
        session.close()


def top_energy(n: int = 10) -> None:
    """Top N bâtiments les plus énergivores."""
    session = SessionLocal()
    try:
        buildings = (
            session.query(Building)
            .filter(Building.site_energy_use.isnot(None))
            .order_by(desc(Building.site_energy_use))
            .limit(n)
            .all()
        )

        print(f"\n  Top {n} bâtiments les plus énergivores :")
        print("-" * 100)
        print(f"  {'#':<4} {'Nom':<35} {'Type':<20} {'Énergie (kBtu)':<18} {'CO2 (t)':<12}")
        print("-" * 100)

        for i, b in enumerate(buildings, 1):
            name = (b.property_name or "N/A")[:33]
            ghg = f"{b.total_ghg_emissions:.1f}" if b.total_ghg_emissions else "N/A"
            print(
                f"  {i:<4} {name:<35} {b.primary_property_type[:18]:<20} "
                f"{b.site_energy_use:>14,.0f}    {ghg:>8}"
            )

    finally:
        session.close()


def predict_from_building(building_id: int) -> None:
    """Fait une prédiction à partir d'un bâtiment en base.

    Récupère les données du bâtiment, les envoie au modèle,
    et enregistre le résultat en base.
    """
    session = SessionLocal()
    try:
        building = session.query(Building).filter(Building.ose_building_id == building_id).first()

        if not building:
            print(f"  Bâtiment {building_id} non trouvé en base.")
            return

        print(f"\n  Prédiction pour : {building.property_name} (ID: {building_id})")
        print(f"  Type : {building.primary_property_type}")
        print(f"  Surface : {building.property_gfa_total:,} sq ft")

        # Préparer les inputs pour le modèle
        from src.services.predictor import get_predictor

        predictor = get_predictor()

        building_data = {
            "NumberofBuildings": int(building.number_of_buildings or 1),
            "NumberofFloors": building.number_of_floors,
            "PropertyGFATotal": float(building.property_gfa_total or 0),
            "PropertyGFAParking": float(building.property_gfa_parking or 0),
            "PropertyGFABuilding(s)": float(building.property_gfa_building or 0),
            "LargestPropertyUseTypeGFA": float(building.largest_property_use_type_gfa or 0),
            "SecondLargestPropertyUseTypeGFA": float(
                building.second_largest_property_use_type_gfa or 0
            ),
            "ThirdLargestPropertyUseTypeGFA": float(
                building.third_largest_property_use_type_gfa or 0
            ),
            "BuildingType": building.building_type,
            "PrimaryPropertyType": building.primary_property_type,
            "LargestPropertyUseType": building.largest_property_use_type or "None",
            "SecondLargestPropertyUseType": building.second_largest_property_use_type or "None",
            "ThirdLargestPropertyUseType": building.third_largest_property_use_type or "None",
            "HasElectricity": 1
            if building.electricity_kbtu and building.electricity_kbtu > 0
            else 0,
            "HasNaturalGas": 1
            if building.natural_gas_kbtu and building.natural_gas_kbtu > 0
            else 0,
            "HasSteam": 1 if building.steam_use and building.steam_use > 0 else 0,
        }

        import time

        start = time.perf_counter()
        energy_kbtu, co2_tons = predictor.predict(building_data)
        duration_ms = (time.perf_counter() - start) * 1000

        print("\n  --- Résultats ---")
        print(f"  Énergie prédite : {energy_kbtu:,.0f} kBtu")
        print(f"  CO2 prédit : {co2_tons:.2f} tonnes")
        print(f"  Durée : {duration_ms:.1f} ms")

        if building.site_energy_use:
            diff_e = abs(energy_kbtu - building.site_energy_use)
            pct_e = diff_e / building.site_energy_use * 100
            print(
                f"\n  Énergie réelle : {building.site_energy_use:,.0f} kBtu (écart: {pct_e:.1f}%)"
            )

        if building.total_ghg_emissions:
            diff_c = abs(co2_tons - building.total_ghg_emissions)
            pct_c = diff_c / building.total_ghg_emissions * 100
            print(f"  CO2 réel : {building.total_ghg_emissions:.2f} tonnes (écart: {pct_c:.1f}%)")

        # Enregistrer la prédiction en base

        prediction = Prediction(
            building_id=building.id,
            number_of_buildings=int(building.number_of_buildings or 1),
            number_of_floors=building.number_of_floors,
            property_gfa_total=float(building.property_gfa_total or 0),
            property_gfa_parking=float(building.property_gfa_parking or 0),
            property_gfa_building=float(building.property_gfa_building or 0),
            largest_property_use_type_gfa=float(building.largest_property_use_type_gfa or 0),
            second_largest_property_use_type_gfa=float(
                building.second_largest_property_use_type_gfa or 0
            ),
            third_largest_property_use_type_gfa=float(
                building.third_largest_property_use_type_gfa or 0
            ),
            building_type=building.building_type,
            primary_property_type=building.primary_property_type,
            largest_property_use_type=building.largest_property_use_type,
            second_largest_property_use_type=building.second_largest_property_use_type,
            third_largest_property_use_type=building.third_largest_property_use_type,
            energy_prediction_kbtu=energy_kbtu,
            co2_prediction_tons=co2_tons,
            prediction_duration_ms=duration_ms,
            source="script",
        )
        session.add(prediction)
        session.commit()
        print(f"\n  Prediction {str(prediction.id)[:8]} enregistree en base")

    except Exception as e:
        session.rollback()
        logger.error(f"Erreur: {e}")
        raise
    finally:
        session.close()


def main() -> None:
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Interroger la base de données deploy-ml et interagir avec le modèle ML"
    )
    parser.add_argument("--stats", action="store_true", help="Statistiques globales")
    parser.add_argument("--buildings", action="store_true", help="Lister les bâtiments")
    parser.add_argument("--predictions", action="store_true", help="Historique des prédictions")
    parser.add_argument("--top-energy", type=int, metavar="N", help="Top N bâtiments énergivores")
    parser.add_argument(
        "--predict", action="store_true", help="Prédire à partir d'un bâtiment en base"
    )
    parser.add_argument("--building-id", type=int, help="OSEBuildingID pour --predict")
    parser.add_argument("--type", type=str, default=None, help="Filtre par building_type")
    parser.add_argument("--limit", type=int, default=20, help="Nombre de résultats (défaut: 20)")

    args = parser.parse_args()

    if not any([args.stats, args.buildings, args.predictions, args.top_energy, args.predict]):
        parser.print_help()
        return

    if args.stats:
        show_stats()

    if args.buildings:
        list_buildings(building_type=args.type, limit=args.limit)

    if args.predictions:
        list_predictions(limit=args.limit)

    if args.top_energy:
        top_energy(n=args.top_energy)

    if args.predict:
        if not args.building_id:
            print("  Erreur: --building-id requis avec --predict")
            return
        predict_from_building(args.building_id)


if __name__ == "__main__":
    main()
