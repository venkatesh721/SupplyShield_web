"""FastAPI application for SupplyShield."""

from contextlib import asynccontextmanager
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware

from .database import DatabaseConfigurationError, DatabaseConnectionError, database
from . import graph_service
from .schemas import (DisruptionRequest, DisruptionSimulation, NetworkGraph, ProductListItem,
                      ProductSupplyChain, SingleSourceComponent, SupplierDetail, SupplierListItem)

load_dotenv()


DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:6969",
    "http://127.0.0.1:6969",
    "https://supplyshield-web-git-main-venkatesh721s-projects.vercel.app",
    "https://supplyshield-web.vercel.app",
)


def cors_origins() -> list[str]:
    """Return the built-in frontend origins plus deployment-specific additions."""
    configured = os.getenv("CORS_ORIGINS", "")
    extra_origins = tuple(origin.strip() for origin in configured.split(",") if origin.strip())
    return list(dict.fromkeys((*DEFAULT_CORS_ORIGINS, *extra_origins)))


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    database.close()


app = FastAPI(title="SupplyShield API", version="0.1.0", lifespan=lifespan)
# Register middleware before route declarations so browser OPTIONS preflights are handled.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def graph_error(detail: str, action):
    """Map expected database failures to a safe service-unavailable response."""
    try:
        return action()
    except (DatabaseConfigurationError, DatabaseConnectionError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=detail) from exc


@app.get("/health")
def health() -> dict[str, str]:
    """Confirm API availability and safely test the configured Bolt connection."""
    try:
        database.verify_connectivity()
    except DatabaseConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DatabaseConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "healthy", "database": "connected"}


@app.get("/api/dashboard/summary")
def dashboard_summary() -> dict[str, int]:
    """Return graph-derived operational and supply-risk totals."""
    # Independent graph counts avoid denormalized counters and stay correct as relationships change.
    query = """
    CALL { MATCH (s:Supplier) RETURN count(s) AS total_suppliers }
    CALL { MATCH (s:Supplier {status: 'active'}) RETURN count(s) AS active_suppliers }
    CALL {
      MATCH (s:Supplier)-[:HAS_RISK]->(r:RiskEvent)
      WHERE r.status = 'open' AND r.severity IN ['high', 'critical']
      RETURN count(DISTINCT s) AS high_risk_suppliers
    }
    CALL { MATCH (p:Product) RETURN count(p) AS total_products }
    CALL {
      MATCH (c:Component {criticality: 'critical'})
      WHERE size([(c)<-[:SUPPLIES]-(:Supplier) | 1]) = 1
      RETURN count(c) AS critical_single_source_components
    }
    CALL { MATCH (r:RiskEvent {status: 'open'}) RETURN count(r) AS open_risk_events }
    RETURN total_suppliers, active_suppliers, high_risk_suppliers, total_products,
           critical_single_source_components, open_risk_events
    """
    try:
        with database.driver().session() as session:
            record = session.run(query, {}).single()
    except (DatabaseConfigurationError, DatabaseConnectionError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Unable to retrieve dashboard data.") from exc

    return dict(record)


@app.get("/api/suppliers", response_model=list[SupplierListItem])
def list_suppliers(
    search: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None, pattern="^(active|affected|inactive)$"),
    region: str | None = Query(default=None, max_length=100),
) -> list[dict]:
    return graph_error("Unable to retrieve suppliers.", lambda: graph_service.suppliers(search, status, region))


@app.get("/api/suppliers/{supplier_id}", response_model=SupplierDetail)
def get_supplier(supplier_id: str = Path(min_length=1, max_length=100, pattern="^[A-Za-z0-9_-]+$")) -> dict:
    result = graph_error("Unable to retrieve supplier details.", lambda: graph_service.supplier_detail(supplier_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return result


@app.get("/api/products", response_model=list[ProductListItem])
def list_products() -> list[dict]:
    return graph_error("Unable to retrieve products.", graph_service.products)


@app.get("/api/products/{product_id}/supply-chain", response_model=ProductSupplyChain)
def get_product_supply_chain(product_id: str = Path(min_length=1, max_length=100, pattern="^[A-Za-z0-9_-]+$")) -> dict:
    result = graph_error("Unable to retrieve product supply chain.", lambda: graph_service.product_supply_chain(product_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return result


@app.post("/api/disruptions/simulate", response_model=DisruptionSimulation, status_code=200)
def simulate_disruption(request: DisruptionRequest) -> dict:
    result = graph_error("Unable to simulate supplier disruption.", lambda: graph_service.disruption_simulation(request.supplier_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return result


@app.get("/api/risk/single-source-components", response_model=list[SingleSourceComponent])
def get_single_source_components() -> list[dict]:
    return graph_error("Unable to retrieve single-source component risks.", graph_service.single_source_components)


@app.get("/api/network", response_model=NetworkGraph)
def get_network() -> dict:
    return graph_error("Unable to retrieve supply network.", graph_service.network)
