"""Parameterized read-only graph queries for SupplyShield."""

from collections import defaultdict
from typing import Any

from .database import database


def _rows(query: str, **parameters: Any) -> list[dict[str, Any]]:
    """Run a parameterized Cypher read query and return JSON-friendly records."""
    with database.driver().session() as session:
        return [record.data() for record in session.run(query, parameters)]


def suppliers(search: str | None, status: str | None, region: str | None) -> list[dict[str, Any]]:
    # Graph aggregation counts components and open risks without application-side joins.
    return _rows("""
        MATCH (s:Supplier)
        OPTIONAL MATCH (s)-[:LOCATED_IN]->(region:Region)
        OPTIONAL MATCH (s)-[:SUPPLIES]->(component:Component)
        OPTIONAL MATCH (s)-[:HAS_RISK]->(risk:RiskEvent {status: 'open'})
        WITH s, region, count(DISTINCT component) AS supplied_component_count,
             count(DISTINCT risk) AS active_risk_count
        WHERE ($search IS NULL OR toLower(s.name) CONTAINS toLower($search))
          AND ($status IS NULL OR s.status = $status)
          AND ($region IS NULL OR region.id = $region OR region.name = $region)
        RETURN s.id AS id, s.name AS name, s.country AS country,
               s.reliability_score AS reliability_score, s.status AS status,
               region.name AS region, supplied_component_count, active_risk_count
        ORDER BY s.name
    """, search=search, status=status, region=region)


def supplier_detail(supplier_id: str) -> dict[str, Any] | None:
    # Traversing outward captures supplier dependencies and downstream product exposure in one query.
    rows = _rows("""
        MATCH (s:Supplier {id: $supplier_id})
        OPTIONAL MATCH (s)-[:LOCATED_IN]->(region:Region)
        OPTIONAL MATCH (s)-[:SUPPLIES]->(component:Component)-[:USED_IN]->(product:Product)
        OPTIONAL MATCH (s)-[:HAS_RISK]->(risk:RiskEvent)
        OPTIONAL MATCH (s)-[:ALTERNATIVE_FOR]->(alternative:Supplier)
        OPTIONAL MATCH (alternative)-[:LOCATED_IN]->(alternative_region:Region)
        RETURN s.id AS id, s.name AS name, s.country AS country, s.reliability_score AS reliability_score,
          s.status AS status, region.name AS region,
          collect(DISTINCT CASE WHEN component IS NULL THEN NULL ELSE {id: component.id, name: component.name, category: component.category, criticality: component.criticality} END) AS components,
          collect(DISTINCT CASE WHEN risk IS NULL THEN NULL ELSE {id: risk.id, type: risk.type, severity: risk.severity, description: risk.description, status: risk.status} END) AS risk_events,
          collect(DISTINCT CASE WHEN alternative IS NULL THEN NULL ELSE {id: alternative.id, name: alternative.name, country: alternative.country, reliability_score: alternative.reliability_score, status: alternative.status, region: alternative_region.name, supplied_component_count: 0, active_risk_count: 0} END) AS alternative_suppliers,
          collect(DISTINCT CASE WHEN product IS NULL THEN NULL ELSE {id: product.id, name: product.name, category: product.category, criticality: 'downstream'} END) AS affected_products
    """, supplier_id=supplier_id)
    if not rows:
        return None
    result = rows[0]
    for key in ("components", "risk_events", "alternative_suppliers", "affected_products"):
        result[key] = [item for item in result[key] if item is not None]
    # Existing list fields are already computed; list-item risk counts are not meaningful in this view.
    result["supplied_component_count"] = len(result["components"])
    result["active_risk_count"] = sum(r["status"] == "open" for r in result["risk_events"])
    return result


def products() -> list[dict[str, Any]]:
    # A component's supplier/risk neighborhood determines product risk without a fixed join depth.
    return _rows("""
        MATCH (p:Product)
        OPTIONAL MATCH (c:Component)-[:USED_IN]->(p)
        OPTIONAL MATCH (p)-[:STORED_AT]->(w:Warehouse)
        WITH p, collect(DISTINCT c) AS components, count(DISTINCT w) AS warehouse_count
        CALL {
          WITH components
          UNWIND components AS c
          OPTIONAL MATCH (s:Supplier)-[:SUPPLIES]->(c)
          OPTIONAL MATCH (s)-[:HAS_RISK]->(r:RiskEvent {status: 'open'})
          WITH c, collect(DISTINCT s) AS suppliers, collect(DISTINCT r.severity) AS severities
          RETURN max(CASE WHEN size(suppliers) = 1 OR 'critical' IN severities THEN 3 WHEN 'high' IN severities THEN 2 ELSE 1 END) AS risk_score
        }
        RETURN p.id AS id, p.name AS name, p.category AS category, size(components) AS component_count,
          warehouse_count, CASE risk_score WHEN 3 THEN 'high' WHEN 2 THEN 'medium' ELSE 'low' END AS supply_risk_level
        ORDER BY p.name
    """)


def product_supply_chain(product_id: str) -> dict[str, Any] | None:
    # Multi-hop graph traversal returns the full Product→Component→Supplier and Product→Warehouse→Region topology.
    rows = _rows("""
        MATCH (p:Product {id: $product_id})
        OPTIONAL MATCH (c:Component)-[:USED_IN]->(p)
        OPTIONAL MATCH (s:Supplier)-[:SUPPLIES]->(c)
        OPTIONAL MATCH (s)-[:LOCATED_IN]->(supplier_region:Region)
        OPTIONAL MATCH (p)-[stock:STORED_AT]->(w:Warehouse)
        OPTIONAL MATCH (w)-[:SERVES]->(served_region:Region)
        RETURN p.id AS product_id, p.name AS product_name, p.category AS product_category,
          c.id AS component_id, c.name AS component_name, c.category AS component_category, c.criticality AS component_criticality,
          s.id AS supplier_id, s.name AS supplier_name, s.status AS supplier_status, s.reliability_score AS supplier_reliability_score, supplier_region.name AS supplier_region,
          w.id AS warehouse_id, w.name AS warehouse_name, w.city AS warehouse_city, w.capacity AS warehouse_capacity, stock.stock_quantity AS stock_quantity, served_region.name AS served_region
    """, product_id=product_id)
    if not rows:
        return None
    first = rows[0]; components: dict[str, dict] = {}; warehouses: dict[str, dict] = {}
    for row in rows:
        if row["component_id"]:
            component = components.setdefault(row["component_id"], {"id": row["component_id"], "name": row["component_name"], "category": row["component_category"], "criticality": row["component_criticality"], "suppliers": []})
            if row["supplier_id"] and not any(s["id"] == row["supplier_id"] for s in component["suppliers"]): component["suppliers"].append({"id": row["supplier_id"], "name": row["supplier_name"], "status": row["supplier_status"], "reliability_score": row["supplier_reliability_score"], "region": row["supplier_region"]})
        if row["warehouse_id"]:
            warehouse = warehouses.setdefault(row["warehouse_id"], {"id": row["warehouse_id"], "name": row["warehouse_name"], "city": row["warehouse_city"], "capacity": row["warehouse_capacity"], "stock_quantity": row["stock_quantity"], "served_regions": []})
            if row["served_region"] and row["served_region"] not in warehouse["served_regions"]: warehouse["served_regions"].append(row["served_region"])
    return {"id": first["product_id"], "name": first["product_name"], "category": first["product_category"], "required_components": list(components.values()), "warehouses": list(warehouses.values())}


def disruption_simulation(supplier_id: str) -> dict[str, Any] | None:
    # This multi-hop traversal calculates all operational ripple effects of losing a supplier.
    impacts = _rows("""
        MATCH (s:Supplier {id: $supplier_id})-[:SUPPLIES]->(c:Component)-[:USED_IN]->(p:Product)-[:STORED_AT]->(w:Warehouse)-[:SERVES]->(region:Region)
        RETURN DISTINCT c.id AS component_id, c.name AS component_name, c.category AS component_category, c.criticality AS component_criticality,
          p.id AS product_id, p.name AS product_name, w.id AS warehouse_id, w.name AS warehouse_name, region.id AS region_id, region.name AS region_name
    """, supplier_id=supplier_id)
    exists = _rows("MATCH (s:Supplier {id: $supplier_id}) RETURN s.id AS id", supplier_id=supplier_id)
    if not exists: return None
    component_ids = list({row["component_id"] for row in impacts})
    # The alternate supplier query ranks different-region, reliable, risk-free active candidates first.
    alternatives = _rows("""
        UNWIND $component_ids AS component_id
        MATCH (failed:Supplier {id: $supplier_id})-[:SUPPLIES]->(c:Component {id: component_id})
        OPTIONAL MATCH (failed)-[:LOCATED_IN]->(failed_region:Region)
        OPTIONAL MATCH (candidate:Supplier {status: 'active'})-[:SUPPLIES]->(c)
        WHERE candidate <> failed AND NOT EXISTS {
          MATCH (candidate)-[:HAS_RISK]->(candidate_risk:RiskEvent {status: 'open'}) WHERE candidate_risk.severity IN ['high', 'critical']
        }
        OPTIONAL MATCH (candidate)-[:LOCATED_IN]->(candidate_region:Region)
        WITH c, failed_region, candidate, candidate_region
        ORDER BY CASE WHEN candidate_region.id <> failed_region.id THEN 0 ELSE 1 END, candidate.reliability_score DESC
        RETURN c.id AS component_id, collect(CASE WHEN candidate IS NULL THEN NULL ELSE {id: candidate.id, name: candidate.name, region: candidate_region.name, reliability_score: candidate.reliability_score} END) AS alternatives
    """, supplier_id=supplier_id, component_ids=component_ids)
    alternatives_by_component = {row["component_id"]: [a for a in row["alternatives"] if a] for row in alternatives}
    components: dict[str, dict] = {}; products: dict[str, dict] = {}; warehouses: dict[str, dict] = {}; regions: dict[str, dict] = {}
    for row in impacts:
        alts = alternatives_by_component.get(row["component_id"], [])
        severity = "critical" if not alts or row["component_criticality"] == "critical" else "high" if row["component_criticality"] == "high" else "medium"
        components[row["component_id"]] = {"id": row["component_id"], "name": row["component_name"], "severity": severity, "alternatives": alts, "category": row["component_category"], "criticality": row["component_criticality"]}
        products[row["product_id"]] = {"id": row["product_id"], "name": row["product_name"], "severity": severity}
        warehouses[row["warehouse_id"]] = {"id": row["warehouse_id"], "name": row["warehouse_name"], "severity": severity}
        regions[row["region_id"]] = {"id": row["region_id"], "name": row["region_name"], "severity": severity}
    no_alternative = [{key: value[key] for key in ("id", "name", "category", "criticality")} for value in components.values() if not value["alternatives"]]
    return {"supplier_id": supplier_id, "affected_components": list(components.values()), "affected_products": list(products.values()), "affected_warehouses": list(warehouses.values()), "affected_customer_regions": list(regions.values()), "components_with_no_alternative": no_alternative}


def single_source_components() -> list[dict[str, Any]]:
    # Degree counting in the graph identifies active supply single points of failure directly.
    return _rows("""
        MATCH (s:Supplier {status: 'active'})-[:SUPPLIES]->(c:Component)
        WITH c, collect(s) AS suppliers
        WHERE size(suppliers) = 1
        WITH c, suppliers[0] AS supplier
        OPTIONAL MATCH (supplier)-[:LOCATED_IN]->(region:Region)
        RETURN c.id AS id, c.name AS name, c.category AS category, c.criticality AS criticality,
          supplier.id AS supplier_id, supplier.name AS supplier_name, region.name AS supplier_region
        ORDER BY c.criticality DESC, c.name
    """)


def network() -> dict[str, list[dict[str, Any]]]:
    # A graph-native relationship scan produces visualization nodes and edges without a relational assembly table.
    rows = _rows("""
        MATCH (source)-[relationship:SUPPLIES|USED_IN|STORED_AT|SERVES|LOCATED_IN|HAS_RISK|ALTERNATIVE_FOR]->(target)
        RETURN source.id AS source_id, labels(source)[0] AS source_type, source.name AS source_name, properties(source) AS source_data,
          type(relationship) AS relationship_type, properties(relationship) AS relationship_data,
          target.id AS target_id, labels(target)[0] AS target_type, target.name AS target_name, properties(target) AS target_data
    """)
    nodes: dict[str, dict] = {}; edges: dict[str, dict] = {}
    for row in rows:
        for prefix in ("source", "target"):
            node_id = row[f"{prefix}_id"]
            nodes.setdefault(node_id, {"id": node_id, "type": row[f"{prefix}_type"], "label": row[f"{prefix}_name"] or node_id, "data": row[f"{prefix}_data"]})
        edge_id = f"{row['source_id']}:{row['relationship_type']}:{row['target_id']}"
        edges[edge_id] = {"id": edge_id, "source": row["source_id"], "target": row["target_id"], "type": row["relationship_type"], "data": row["relationship_data"]}
    return {"nodes": list(nodes.values()), "edges": list(edges.values())}
