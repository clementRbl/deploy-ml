#!/usr/bin/env python3
"""Script de création de la base de données PostgreSQL et insertion du dataset.

Usage:
    # Créer les tables uniquement
    python scripts/create_db.py --create-tables

    # Créer les tables + insérer le dataset CSV
    python scripts/create_db.py --seed

    # Reset complet (drop + create + seed)
    python scripts/create_db.py --reset --seed

Prérequis:
    PostgreSQL lancé localement (voir docker-compose.yml)
    Variables d'environnement ou .env configuré avec DATABASE_URL
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_settings
from src.core.logging import logger
from src.db.database import SessionLocal, engine
from src.db.models import Base, Building

# Mapping CSV column → ORM attribute
CSV_TO_ORM = {
    "OSEBuildingID": "ose_building_id",
    "DataYear": "data_year",
    "BuildingType": "building_type",
    "PrimaryPropertyType": "primary_property_type",
    "PropertyName": "property_name",
    "Address": "address",
    "City": "city",
    "State": "state",
    "ZipCode": "zip_code",
    "Neighborhood": "neighborhood",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "YearBuilt": "year_built",
    "NumberofBuildings": "number_of_buildings",
    "NumberofFloors": "number_of_floors",
    "PropertyGFATotal": "property_gfa_total",
    "PropertyGFAParking": "property_gfa_parking",
    "PropertyGFABuilding(s)": "property_gfa_building",
    "ListOfAllPropertyUseTypes": "list_of_all_property_use_types",
    "LargestPropertyUseType": "largest_property_use_type",
    "LargestPropertyUseTypeGFA": "largest_property_use_type_gfa",
    "SecondLargestPropertyUseType": "second_largest_property_use_type",
    "SecondLargestPropertyUseTypeGFA": "second_largest_property_use_type_gfa",
    "ThirdLargestPropertyUseType": "third_largest_property_use_type",
    "ThirdLargestPropertyUseTypeGFA": "third_largest_property_use_type_gfa",
    "ENERGYSTARScore": "energy_star_score",
    "SiteEUI(kBtu/sf)": "site_eui",
    "SiteEUIWN(kBtu/sf)": "site_eui_wn",
    "SourceEUI(kBtu/sf)": "source_eui",
    "SourceEUIWN(kBtu/sf)": "source_eui_wn",
    "SiteEnergyUse(kBtu)": "site_energy_use",
    "SiteEnergyUseWN(kBtu)": "site_energy_use_wn",
    "SteamUse(kBtu)": "steam_use",
    "Electricity(kWh)": "electricity_kwh",
    "Electricity(kBtu)": "electricity_kbtu",
    "NaturalGas(therms)": "natural_gas_therms",
    "NaturalGas(kBtu)": "natural_gas_kbtu",
    "TotalGHGEmissions": "total_ghg_emissions",
    "GHGEmissionsIntensity": "ghg_emissions_intensity",
    "DefaultData": "default_data",
    "ComplianceStatus": "compliance_status",
    "Outlier": "outlier",
}


def create_tables() -> None:
    """Crée toutes les tables définies dans les modèles ORM."""
    logger.info("Création des tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables créées avec succès")

    # Afficher les tables créées
    for table in Base.metadata.sorted_tables:
        logger.info(f"  - {table.name} ({len(table.columns)} colonnes)")


def drop_tables() -> None:
    """Supprime toutes les tables."""
    logger.warning("Suppression de toutes les tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Tables supprimées")


def seed_buildings(csv_path: str | None = None) -> int:
    """Insère le dataset CSV dans la table buildings.

    Args:
        csv_path: Chemin vers le fichier CSV. Par défaut: data/2016_Building_Energy_Benchmarking.csv

    Returns:
        Nombre de lignes insérées.
    """
    if csv_path is None:
        csv_path = str(
            Path(__file__).parent.parent / "data" / "2016_Building_Energy_Benchmarking.csv"
        )

    logger.info(f"Chargement du fichier CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"  {len(df)} lignes, {len(df.columns)} colonnes")

    # Renommer les colonnes CSV → ORM
    df_renamed = df.rename(columns=CSV_TO_ORM)

    # Ne garder que les colonnes qui existent dans le modèle ORM
    valid_columns = [c for c in df_renamed.columns if c in CSV_TO_ORM.values()]
    df_orm = df_renamed[valid_columns].copy()

    # Convertir les NaN en None pour PostgreSQL
    df_orm = df_orm.where(df_orm.notna(), None)

    # Convertir DefaultData en booléen
    if "default_data" in df_orm.columns:
        df_orm["default_data"] = df_orm["default_data"].map(
            {"Yes": True, "No": False, True: True, False: False}
        )

    # Insertion par batch
    session = SessionLocal()
    try:
        # Vérifier si des données existent déjà
        existing = session.query(Building).count()
        if existing > 0:
            logger.warning(
                f"La table buildings contient déjà {existing} lignes. Insertion ignorée."
            )
            logger.info("Utilisez --reset pour réinitialiser les données.")
            return 0

        records = df_orm.to_dict("records")
        batch_size = 500
        inserted = 0

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            session.bulk_insert_mappings(Building, batch)
            session.commit()
            inserted += len(batch)
            logger.info(f"  Inséré {inserted}/{len(records)} lignes...")

        logger.info(f"{inserted} bâtiments insérés dans la table buildings")
        return inserted

    except Exception as e:
        session.rollback()
        logger.error(f"Erreur lors de l'insertion: {e}")
        raise
    finally:
        session.close()


def verify_data() -> None:
    """Vérifie les données insérées."""
    session = SessionLocal()
    try:
        count = session.query(Building).count()
        logger.info("\n=== Vérification ===")
        logger.info(f"  Buildings en base: {count}")

        if count > 0:
            # Quelques stats rapides
            result = session.execute(
                text("""
                    SELECT
                        COUNT(*) as total,
                        COUNT(DISTINCT building_type) as n_types,
                        COUNT(DISTINCT primary_property_type) as n_property_types,
                        AVG(site_energy_use) as avg_energy,
                        AVG(total_ghg_emissions) as avg_ghg
                    FROM buildings
                """)
            ).fetchone()

            logger.info(f"  Types de bâtiment: {result[1]}")
            logger.info(f"  Types de propriété: {result[2]}")
            logger.info(f"  Énergie moyenne: {result[3]:,.0f} kBtu")
            logger.info(f"  Émissions moyennes: {result[4]:.1f} tonnes CO2")

        # Vérifier les prédictions
        pred_count = session.execute(text("SELECT COUNT(*) FROM predictions")).scalar()
        logger.info(f"  Prédictions en base: {pred_count}")

    finally:
        session.close()


def main() -> None:
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Gestion de la base de données PostgreSQL deploy-ml"
    )
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Créer les tables (sans insérer de données)",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Insérer le dataset CSV dans la base",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Supprimer et recréer les tables",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Vérifier les données en base",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Chemin vers le fichier CSV (défaut: data/2016_Building_Energy_Benchmarking.csv)",
    )

    args = parser.parse_args()

    settings = get_settings()
    logger.info(f"Base de données: {settings.database_url}")

    if not any([args.create_tables, args.seed, args.reset, args.verify]):
        parser.print_help()
        return

    if args.reset:
        drop_tables()

    if args.create_tables or args.seed or args.reset:
        create_tables()

    if args.seed:
        seed_buildings(args.csv)

    if args.verify or args.seed:
        verify_data()

    logger.info("\nTerminé.")


if __name__ == "__main__":
    main()
