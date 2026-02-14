CREATE TABLE IF NOT EXISTS buildings (
    id                              SERIAL PRIMARY KEY,
    ose_building_id                 INTEGER NOT NULL UNIQUE,
    data_year                       INTEGER NOT NULL,

    building_type                   VARCHAR(100) NOT NULL,
    primary_property_type           VARCHAR(200) NOT NULL,
    property_name                   VARCHAR(500),
    address                         VARCHAR(500),
    city                            VARCHAR(100),
    state                           VARCHAR(10),
    zip_code                        VARCHAR(10),
    neighborhood                    VARCHAR(200),

    latitude                        DOUBLE PRECISION,
    longitude                       DOUBLE PRECISION,

    year_built                      INTEGER,
    number_of_buildings             DOUBLE PRECISION,
    number_of_floors                INTEGER,
    property_gfa_total              INTEGER,
    property_gfa_parking            INTEGER,
    property_gfa_building           INTEGER,

    list_of_all_property_use_types  TEXT,
    largest_property_use_type       VARCHAR(200),
    largest_property_use_type_gfa   DOUBLE PRECISION,
    second_largest_property_use_type     VARCHAR(200),
    second_largest_property_use_type_gfa DOUBLE PRECISION,
    third_largest_property_use_type      VARCHAR(200),
    third_largest_property_use_type_gfa  DOUBLE PRECISION,

    energy_star_score               DOUBLE PRECISION,
    site_eui                        DOUBLE PRECISION,
    site_eui_wn                     DOUBLE PRECISION,
    source_eui                      DOUBLE PRECISION,
    source_eui_wn                   DOUBLE PRECISION,
    site_energy_use                 DOUBLE PRECISION,
    site_energy_use_wn              DOUBLE PRECISION,

    steam_use                       DOUBLE PRECISION,
    electricity_kwh                 DOUBLE PRECISION,
    electricity_kbtu                DOUBLE PRECISION,
    natural_gas_therms              DOUBLE PRECISION,
    natural_gas_kbtu                DOUBLE PRECISION,

    total_ghg_emissions             DOUBLE PRECISION,
    ghg_emissions_intensity         DOUBLE PRECISION,

    default_data                    BOOLEAN,
    compliance_status               VARCHAR(100),
    outlier                         VARCHAR(200)
);

-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_buildings_ose_id ON buildings (ose_building_id);
CREATE INDEX IF NOT EXISTS idx_buildings_type ON buildings (building_type);
CREATE INDEX IF NOT EXISTS idx_buildings_property_type ON buildings (primary_property_type);
CREATE INDEX IF NOT EXISTS idx_buildings_neighborhood ON buildings (neighborhood);

CREATE TABLE IF NOT EXISTS predictions (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    building_id                     INTEGER REFERENCES buildings(id),

    number_of_buildings             INTEGER NOT NULL,
    number_of_floors                DOUBLE PRECISION,
    property_gfa_total              DOUBLE PRECISION NOT NULL,
    property_gfa_parking            DOUBLE PRECISION,
    property_gfa_building           DOUBLE PRECISION NOT NULL,
    largest_property_use_type_gfa   DOUBLE PRECISION NOT NULL,
    second_largest_property_use_type_gfa DOUBLE PRECISION,
    third_largest_property_use_type_gfa  DOUBLE PRECISION,

    building_age                    INTEGER,
    has_multiple_buildings           INTEGER,
    floors_per_building             DOUBLE PRECISION,
    has_secondary_use               INTEGER,
    distance_to_center              DOUBLE PRECISION,
    has_electricity                 INTEGER,
    has_natural_gas                 INTEGER,
    has_steam                       INTEGER,
    surface_gas_interaction         DOUBLE PRECISION,

    building_type                   VARCHAR(100),
    primary_property_type           VARCHAR(200),
    largest_property_use_type       VARCHAR(200),
    second_largest_property_use_type     VARCHAR(200),
    third_largest_property_use_type      VARCHAR(200),

    energy_prediction_kbtu          DOUBLE PRECISION NOT NULL,
    co2_prediction_tons             DOUBLE PRECISION NOT NULL,

    prediction_duration_ms          DOUBLE PRECISION,
    source                          VARCHAR(50) DEFAULT 'api'
);

-- Index pour les requêtes sur les prédictions
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions (created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_building_id ON predictions (building_id);
CREATE INDEX IF NOT EXISTS idx_predictions_property_type ON predictions (primary_property_type);
