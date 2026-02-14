"""Tests fonctionnels des endpoints API.

Teste chaque endpoint individuellement avec le client FastAPI.
Couvre les cas nominaux, les erreurs et les cas limites.
"""

import pytest


class TestHealthEndpoints:
    """Tests pour les endpoints de sante."""

    def test_root_returns_ok(self, client):
        """GET / retourne un status ok."""
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "models_loaded" in data

    def test_health_returns_healthy(self, client):
        """GET /health retourne un status healthy."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["models_loaded"] is True

    def test_health_response_schema(self, client):
        """La reponse health a le bon schema."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert set(data.keys()) == {"status", "version", "models_loaded"}
        assert isinstance(data["version"], str)
        assert isinstance(data["models_loaded"], bool)


class TestPredictionEndpoint:
    """Tests pour POST /predict."""

    def test_predict_valid_input(self, client, valid_building_input):
        """Une prediction avec des donnees valides retourne 200."""
        response = client.post("/api/v1/predict", json=valid_building_input)
        assert response.status_code == 200
        data = response.json()
        assert "energy_prediction_kbtu" in data
        assert "co2_prediction_tons" in data
        assert "prediction_id" in data
        assert data["energy_prediction_kbtu"] > 0
        assert data["co2_prediction_tons"] > 0

    def test_predict_minimal_input(self, client, minimal_building_input):
        """Une prediction avec le payload minimal fonctionne."""
        response = client.post("/api/v1/predict", json=minimal_building_input)
        assert response.status_code == 200
        data = response.json()
        assert data["energy_prediction_kbtu"] > 0
        assert data["co2_prediction_tons"] > 0

    def test_predict_returns_unique_ids(self, client, valid_building_input):
        """Chaque prediction a un ID unique."""
        r1 = client.post("/api/v1/predict", json=valid_building_input)
        r2 = client.post("/api/v1/predict", json=valid_building_input)
        assert r1.json()["prediction_id"] != r2.json()["prediction_id"]

    def test_predict_same_input_same_result(self, client, valid_building_input):
        """Le meme input produit le meme resultat (deterministe)."""
        r1 = client.post("/api/v1/predict", json=valid_building_input)
        r2 = client.post("/api/v1/predict", json=valid_building_input)
        assert r1.json()["energy_prediction_kbtu"] == pytest.approx(
            r2.json()["energy_prediction_kbtu"], rel=1e-6
        )
        assert r1.json()["co2_prediction_tons"] == pytest.approx(
            r2.json()["co2_prediction_tons"], rel=1e-6
        )

    def test_predict_empty_body(self, client):
        """Un body vide retourne 422."""
        response = client.post("/api/v1/predict", json={})
        assert response.status_code == 422

    def test_predict_missing_required_field(self, client):
        """Un champ requis manquant retourne 422."""
        response = client.post(
            "/api/v1/predict",
            json={
                "NumberofBuildings": 1,
                # PropertyGFATotal manquant
                "PropertyGFABuilding(s)": 45000,
                "LargestPropertyUseTypeGFA": 45000,
                "PrimaryPropertyType": "Office",
                "LargestPropertyUseType": "Office",
            },
        )
        assert response.status_code == 422

    def test_predict_invalid_type(self, client):
        """Un type invalide retourne 422."""
        response = client.post(
            "/api/v1/predict",
            json={
                "NumberofBuildings": "not_a_number",
                "PropertyGFATotal": 50000,
                "PropertyGFABuilding(s)": 45000,
                "LargestPropertyUseTypeGFA": 45000,
                "PrimaryPropertyType": "Office",
                "LargestPropertyUseType": "Office",
            },
        )
        assert response.status_code == 422

    def test_predict_negative_surface(self, client):
        """Une surface negative retourne 422 (validation Pydantic)."""
        response = client.post(
            "/api/v1/predict",
            json={
                "NumberofBuildings": 1,
                "PropertyGFATotal": -50000,
                "PropertyGFABuilding(s)": 45000,
                "LargestPropertyUseTypeGFA": 45000,
                "PrimaryPropertyType": "Office",
                "LargestPropertyUseType": "Office",
            },
        )
        assert response.status_code == 422

    def test_predict_zero_buildings(self, client):
        """Zero batiments retourne 422 (ge=1)."""
        response = client.post(
            "/api/v1/predict",
            json={
                "NumberofBuildings": 0,
                "PropertyGFATotal": 50000,
                "PropertyGFABuilding(s)": 45000,
                "LargestPropertyUseTypeGFA": 45000,
                "PrimaryPropertyType": "Office",
                "LargestPropertyUseType": "Office",
            },
        )
        assert response.status_code == 422

    def test_predict_large_building(self, client):
        """Une tres grande surface fonctionne."""
        response = client.post(
            "/api/v1/predict",
            json={
                "NumberofBuildings": 5,
                "NumberofFloors": 50,
                "PropertyGFATotal": 5_000_000,
                "PropertyGFAParking": 500_000,
                "PropertyGFABuilding(s)": 4_500_000,
                "LargestPropertyUseTypeGFA": 3_000_000,
                "SecondLargestPropertyUseTypeGFA": 1_000_000,
                "ThirdLargestPropertyUseTypeGFA": 500_000,
                "PrimaryPropertyType": "Hotel",
                "LargestPropertyUseType": "Hotel",
                "BuildingType": "NonResidential",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["energy_prediction_kbtu"] > 0

    def test_predict_various_property_types(self, client):
        """Differents types de propriete sont acceptes."""
        for prop_type in ["Office", "Hotel", "Retail Store", "Warehouse"]:
            response = client.post(
                "/api/v1/predict",
                json={
                    "NumberofBuildings": 1,
                    "PropertyGFATotal": 50000,
                    "PropertyGFABuilding(s)": 45000,
                    "LargestPropertyUseTypeGFA": 45000,
                    "PrimaryPropertyType": prop_type,
                    "LargestPropertyUseType": prop_type,
                },
            )
            assert response.status_code == 200, f"Echec pour {prop_type}"

    def test_predict_wrong_method(self, client):
        """/predict n'accepte que POST."""
        response = client.get("/api/v1/predict")
        assert response.status_code == 405


class TestModelsEndpoint:
    """Tests pour GET /models/info."""

    def test_models_info_returns_200(self, client):
        """L'endpoint retourne les metadonnees des modeles."""
        response = client.get("/api/v1/models/info")
        assert response.status_code == 200
        data = response.json()
        assert "energy_model" in data
        assert "co2_model" in data

    def test_models_info_content(self, client):
        """Les metadonnees contiennent les champs attendus."""
        response = client.get("/api/v1/models/info")
        data = response.json()
        for model_key in ["energy_model", "co2_model"]:
            model = data[model_key]
            assert "algorithm" in model
            assert "r2_cv" in model
            assert "numeric_features" in model
            assert "categorical_features" in model
            assert "target" in model


class TestDatabaseEndpoints:
    """Tests pour les endpoints /db/."""

    def test_buildings_list_empty(self, client):
        """La liste des batiments est vide si rien en base."""
        response = client.get("/api/v1/db/buildings")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["buildings"] == []

    def test_buildings_list_with_data(self, client):
        """La liste retourne les batiments inseres."""
        from src.db.models import Building

        session = client._test_session_factory()
        session.add(
            Building(
                ose_building_id=1,
                data_year=2016,
                building_type="NonResidential",
                primary_property_type="Office",
                property_name="Test",
                property_gfa_total=50000,
            )
        )
        session.commit()
        session.close()

        response = client.get("/api/v1/db/buildings")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["buildings"][0]["property_name"] == "Test"

    def test_buildings_pagination(self, client):
        """La pagination fonctionne (limit/skip)."""
        from src.db.models import Building

        session = client._test_session_factory()
        for i in range(5):
            session.add(
                Building(
                    ose_building_id=i + 1,
                    data_year=2016,
                    building_type="NonResidential",
                    primary_property_type="Office",
                    property_name=f"B{i}",
                )
            )
        session.commit()
        session.close()

        response = client.get("/api/v1/db/buildings?limit=2&skip=0")
        data = response.json()
        assert data["total"] == 5
        assert len(data["buildings"]) == 2

        response2 = client.get("/api/v1/db/buildings?limit=2&skip=2")
        data2 = response2.json()
        assert len(data2["buildings"]) == 2

    def test_buildings_filter_by_type(self, client):
        """Le filtre par type de batiment fonctionne."""
        from src.db.models import Building

        session = client._test_session_factory()
        session.add(
            Building(
                ose_building_id=1,
                data_year=2016,
                building_type="NonResidential",
                primary_property_type="Office",
            )
        )
        session.add(
            Building(
                ose_building_id=2,
                data_year=2016,
                building_type="Campus",
                primary_property_type="University",
            )
        )
        session.commit()
        session.close()

        response = client.get("/api/v1/db/buildings?building_type=Campus")
        data = response.json()
        assert data["total"] == 1
        assert data["buildings"][0]["building_type"] == "Campus"

    def test_building_by_id_found(self, client):
        """Un batiment existant est retourne par son OSEBuildingID."""
        from src.db.models import Building

        session = client._test_session_factory()
        session.add(
            Building(
                ose_building_id=42,
                data_year=2016,
                building_type="NonResidential",
                primary_property_type="Hotel",
                property_name="Hotel Test",
            )
        )
        session.commit()
        session.close()

        response = client.get("/api/v1/db/buildings/42")
        assert response.status_code == 200
        assert response.json()["property_name"] == "Hotel Test"

    def test_building_by_id_not_found(self, client):
        """Un batiment inexistant retourne 404."""
        response = client.get("/api/v1/db/buildings/99999")
        assert response.status_code == 404

    def test_predictions_history_empty(self, client):
        """L'historique est vide sans prediction."""
        response = client.get("/api/v1/db/predictions/history")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["predictions"] == []

    def test_predictions_history_after_predict(self, client, valid_building_input):
        """L'historique contient la prediction apres un POST /predict."""
        client.post("/api/v1/predict", json=valid_building_input)

        response = client.get("/api/v1/db/predictions/history")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        pred = data["predictions"][0]
        assert pred["source"] == "api"
        assert pred["primary_property_type"] == "Office"
        assert pred["energy_prediction_kbtu"] > 0

    def test_stats_empty_db(self, client):
        """Les stats sur une base vide retournent un message."""
        response = client.get("/api/v1/db/stats/buildings")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0 or data.get("buildings", {}).get("total") == 0

    def test_stats_with_data(self, client):
        """Les stats retournent les bonnes valeurs."""
        from src.db.models import Building

        session = client._test_session_factory()
        for i in range(3):
            session.add(
                Building(
                    ose_building_id=i + 1,
                    data_year=2016,
                    building_type="NonResidential",
                    primary_property_type="Office",
                    year_built=2000,
                )
            )
        session.commit()
        session.close()

        response = client.get("/api/v1/db/stats/buildings")
        assert response.status_code == 200
        data = response.json()
        assert data["buildings"]["total"] == 3


class TestNonExistentEndpoints:
    """Tests pour les routes inexistantes."""

    def test_404_unknown_route(self, client):
        """Une route inconnue retourne 404."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_404_wrong_api_version(self, client):
        """Une mauvaise version d'API retourne 404."""
        response = client.get("/api/v2/health")
        assert response.status_code == 404
