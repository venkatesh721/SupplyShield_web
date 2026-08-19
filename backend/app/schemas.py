"""Pydantic contracts exposed by the SupplyShield API."""

from pydantic import BaseModel, Field


class SupplierListItem(BaseModel):
    id: str; name: str; country: str; reliability_score: float; status: str
    region: str | None = None; supplied_component_count: int; active_risk_count: int


class ComponentInfo(BaseModel):
    id: str; name: str; category: str; criticality: str


class RiskEventInfo(BaseModel):
    id: str; type: str; severity: str; description: str; status: str


class SupplierDetail(SupplierListItem):
    components: list[ComponentInfo]; risk_events: list[RiskEventInfo]
    alternative_suppliers: list[SupplierListItem]; affected_products: list[ComponentInfo]


class ProductListItem(BaseModel):
    id: str; name: str; category: str; component_count: int; warehouse_count: int; supply_risk_level: str


class SupplyChainSupplier(BaseModel):
    id: str; name: str; status: str; reliability_score: float; region: str | None = None


class SupplyChainComponent(ComponentInfo):
    suppliers: list[SupplyChainSupplier]


class WarehouseInfo(BaseModel):
    id: str; name: str; city: str; capacity: int; stock_quantity: int; served_regions: list[str]


class ProductSupplyChain(BaseModel):
    id: str; name: str; category: str; required_components: list[SupplyChainComponent]; warehouses: list[WarehouseInfo]


class DisruptionRequest(BaseModel):
    supplier_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


class AlternativeSupplier(BaseModel):
    id: str; name: str; region: str | None = None; reliability_score: float


class Impact(BaseModel):
    id: str; name: str; severity: str


class ComponentImpact(Impact):
    alternatives: list[AlternativeSupplier]


class DisruptionSimulation(BaseModel):
    supplier_id: str; affected_components: list[ComponentImpact]; affected_products: list[Impact]
    affected_warehouses: list[Impact]; affected_customer_regions: list[Impact]
    components_with_no_alternative: list[ComponentInfo]


class SingleSourceComponent(ComponentInfo):
    supplier_id: str; supplier_name: str; supplier_region: str | None = None


class NetworkNode(BaseModel):
    id: str; type: str; label: str; data: dict[str, object]


class NetworkEdge(BaseModel):
    id: str; source: str; target: str; type: str; data: dict[str, object]


class NetworkGraph(BaseModel):
    nodes: list[NetworkNode]; edges: list[NetworkEdge]
