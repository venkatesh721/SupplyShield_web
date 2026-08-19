"""API contract tests that do not require a live CognoDB instance."""

from fastapi.testclient import TestClient

from app import graph_service
from app.database import database
from app.main import app

client = TestClient(app)


def test_health_reports_connected_database(monkeypatch):
    monkeypatch.setattr(database, "verify_connectivity", lambda: None)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


def test_dashboard_summary_returns_graph_totals(monkeypatch):
    class Result:
        def single(self):
            return {"total_suppliers": 20, "active_suppliers": 17, "high_risk_suppliers": 4, "total_products": 12, "critical_single_source_components": 4, "open_risk_events": 6}
    class Session:
        def run(self, _query, _parameters): return Result()
        def __enter__(self): return self
        def __exit__(self, *_args): return None
    class Driver:
        def session(self): return Session()
    monkeypatch.setattr(database, "driver", lambda: Driver())
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    assert response.json()["critical_single_source_components"] == 4


def test_single_source_component_contract(monkeypatch):
    monkeypatch.setattr(graph_service, "single_source_components", lambda: [{"id": "CMP-02", "name": "Lithium Battery Cell", "category": "energy", "criticality": "critical", "supplier_id": "SUP-006", "supplier_name": "Kanto Battery Co.", "supplier_region": "East Asia"}])
    response = client.get("/api/risk/single-source-components")
    assert response.status_code == 200
    assert response.json()[0]["supplier_id"] == "SUP-006"


def test_disruption_simulation_contract(monkeypatch):
    simulation = {"supplier_id": "SUP-006", "affected_components": [{"id": "CMP-02", "name": "Lithium Battery Cell", "severity": "critical", "alternatives": []}], "affected_products": [{"id": "PRD-03", "name": "Helios EV Charger", "severity": "critical"}], "affected_warehouses": [{"id": "WH-01", "name": "Rotterdam Hub", "severity": "critical"}], "affected_customer_regions": [{"id": "REG-02", "name": "Europe", "severity": "critical"}], "components_with_no_alternative": [{"id": "CMP-02", "name": "Lithium Battery Cell", "category": "energy", "criticality": "critical"}]}
    monkeypatch.setattr(graph_service, "disruption_simulation", lambda _id: simulation)
    response = client.post("/api/disruptions/simulate", json={"supplier_id": "SUP-006"})
    assert response.status_code == 200
    assert response.json()["components_with_no_alternative"][0]["id"] == "CMP-02"
