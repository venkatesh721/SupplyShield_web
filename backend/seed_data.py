"""Idempotently seed SupplyShield's fictional CognoDB graph.

Run from backend after configuring .env: python seed_data.py
"""

from pathlib import Path
import sys

from dotenv import load_dotenv

from app.database import DatabaseConfigurationError, DatabaseConnectionError, database

load_dotenv(Path(__file__).resolve().parent / ".env")

SUPPLIERS = [
    {"id": "SUP-001", "name": "Apex Micro Systems", "country": "Taiwan", "reliability_score": 94, "status": "active"},
    {"id": "SUP-002", "name": "Nordic Precision AB", "country": "Sweden", "reliability_score": 91, "status": "active"},
    {"id": "SUP-003", "name": "Pacific Circuit Works", "country": "Malaysia", "reliability_score": 82, "status": "affected"},
    {"id": "SUP-004", "name": "Rhein Industrial GmbH", "country": "Germany", "reliability_score": 96, "status": "active"},
    {"id": "SUP-005", "name": "Solstice Materials", "country": "United States", "reliability_score": 88, "status": "active"},
    {"id": "SUP-006", "name": "Kanto Battery Co.", "country": "Japan", "reliability_score": 93, "status": "active"},
    {"id": "SUP-007", "name": "Andean Copper Ltd.", "country": "Chile", "reliability_score": 79, "status": "affected"},
    {"id": "SUP-008", "name": "Delta Plastics Vietnam", "country": "Vietnam", "reliability_score": 86, "status": "active"},
    {"id": "SUP-009", "name": "Bharat Fasteners", "country": "India", "reliability_score": 84, "status": "active"},
    {"id": "SUP-010", "name": "Maple Optics Inc.", "country": "Canada", "reliability_score": 92, "status": "active"},
    {"id": "SUP-011", "name": "Iberia Packaging SA", "country": "Spain", "reliability_score": 89, "status": "active"},
    {"id": "SUP-012", "name": "Eastern Rare Earths", "country": "China", "reliability_score": 67, "status": "inactive"},
    {"id": "SUP-013", "name": "Orion Semiconductors", "country": "South Korea", "reliability_score": 90, "status": "active"},
    {"id": "SUP-014", "name": "Sahara Logistics Parts", "country": "Morocco", "reliability_score": 81, "status": "active"},
    {"id": "SUP-015", "name": "Alpine Motion AG", "country": "Switzerland", "reliability_score": 95, "status": "active"},
    {"id": "SUP-016", "name": "Mekong Cable Solutions", "country": "Thailand", "reliability_score": 83, "status": "affected"},
    {"id": "SUP-017", "name": "Great Lakes Steel", "country": "United States", "reliability_score": 90, "status": "active"},
    {"id": "SUP-018", "name": "Baltic Sensor Labs", "country": "Estonia", "reliability_score": 87, "status": "active"},
    {"id": "SUP-019", "name": "Lusitania Textiles", "country": "Portugal", "reliability_score": 85, "status": "active"},
    {"id": "SUP-020", "name": "Queensland Composites", "country": "Australia", "reliability_score": 91, "status": "active"},
]

COMPONENTS = [
    {"id": "CMP-01", "name": "Power Management IC", "category": "electronics", "criticality": "critical"}, {"id": "CMP-02", "name": "Lithium Battery Cell", "category": "energy", "criticality": "critical"}, {"id": "CMP-03", "name": "Copper Busbar", "category": "electrical", "criticality": "high"}, {"id": "CMP-04", "name": "ABS Housing", "category": "mechanical", "criticality": "medium"}, {"id": "CMP-05", "name": "M8 Fastener Kit", "category": "hardware", "criticality": "low"}, {"id": "CMP-06", "name": "Optical Sensor", "category": "electronics", "criticality": "high"}, {"id": "CMP-07", "name": "Thermal Paste", "category": "materials", "criticality": "medium"}, {"id": "CMP-08", "name": "Rare Earth Magnet", "category": "magnetics", "criticality": "critical"}, {"id": "CMP-09", "name": "Wiring Harness", "category": "electrical", "criticality": "high"}, {"id": "CMP-10", "name": "Gear Assembly", "category": "mechanical", "criticality": "high"}, {"id": "CMP-11", "name": "Steel Chassis", "category": "mechanical", "criticality": "medium"}, {"id": "CMP-12", "name": "RF Module", "category": "electronics", "criticality": "critical"}, {"id": "CMP-13", "name": "Pressure Sensor", "category": "electronics", "criticality": "high"}, {"id": "CMP-14", "name": "Paperboard Carton", "category": "packaging", "criticality": "low"}, {"id": "CMP-15", "name": "Polymer Seal", "category": "materials", "criticality": "medium"}, {"id": "CMP-16", "name": "Servo Motor", "category": "motion", "criticality": "high"}, {"id": "CMP-17", "name": "Camera Lens", "category": "optics", "criticality": "medium"}, {"id": "CMP-18", "name": "Control PCB", "category": "electronics", "criticality": "critical"}, {"id": "CMP-19", "name": "Aluminium Heat Sink", "category": "thermal", "criticality": "medium"}, {"id": "CMP-20", "name": "Waterproof Gasket", "category": "materials", "criticality": "low"}, {"id": "CMP-21", "name": "Fiber Cable", "category": "electrical", "criticality": "high"}, {"id": "CMP-22", "name": "Carbon Fiber Panel", "category": "composites", "criticality": "medium"}, {"id": "CMP-23", "name": "Display Panel", "category": "electronics", "criticality": "high"}, {"id": "CMP-24", "name": "Cooling Fan", "category": "thermal", "criticality": "medium"}, {"id": "CMP-25", "name": "Safety Relay", "category": "electronics", "criticality": "critical"},
]

PRODUCTS = [{"id": f"PRD-{i:02}", "name": name, "category": category} for i, (name, category) in enumerate([("Atlas Industrial Drone", "aerospace"), ("Nexus Smart Meter", "energy"), ("Helios EV Charger", "mobility"), ("Vantage Security Camera", "security"), ("Pulse Medical Monitor", "healthcare"), ("Terra Field Robot", "robotics"), ("Orbit Tracking Unit", "logistics"), ("AeroSense Gateway", "iot"), ("Forge Automation Cell", "industrial"), ("Lumen Smart Light", "building"), ("Stride E-Bike", "mobility"), ("Harbor Navigation Beacon", "marine")], 1)]
WAREHOUSES = [{"id": "WH-01", "name": "Rotterdam Hub", "city": "Rotterdam", "capacity": 180000}, {"id": "WH-02", "name": "Singapore Hub", "city": "Singapore", "capacity": 155000}, {"id": "WH-03", "name": "Chicago Hub", "city": "Chicago", "capacity": 210000}, {"id": "WH-04", "name": "Dubai Hub", "city": "Dubai", "capacity": 125000}, {"id": "WH-05", "name": "Sydney Hub", "city": "Sydney", "capacity": 95000}]
REGIONS = [{"id": "REG-01", "name": "North America", "risk_level": "medium"}, {"id": "REG-02", "name": "Europe", "risk_level": "low"}, {"id": "REG-03", "name": "East Asia", "risk_level": "high"}, {"id": "REG-04", "name": "Southeast Asia", "risk_level": "high"}, {"id": "REG-05", "name": "South Asia", "risk_level": "medium"}, {"id": "REG-06", "name": "Latin America", "risk_level": "medium"}, {"id": "REG-07", "name": "Middle East & Africa", "risk_level": "medium"}, {"id": "REG-08", "name": "Oceania", "risk_level": "low"}]
RISKS = [{"id": "RISK-01", "type": "Port disruption", "severity": "high", "description": "Port congestion delaying component exports.", "status": "open"}, {"id": "RISK-02", "type": "Factory fire", "severity": "critical", "description": "Production line shutdown after factory fire.", "status": "open"}, {"id": "RISK-03", "type": "Quality recall", "severity": "high", "description": "Elevated defect rate under investigation.", "status": "open"}, {"id": "RISK-04", "type": "Labor action", "severity": "medium", "description": "Planned workforce stoppage.", "status": "open"}, {"id": "RISK-05", "type": "Flooding", "severity": "high", "description": "Monsoon flooding affects outbound transport.", "status": "open"}, {"id": "RISK-06", "type": "Export restriction", "severity": "critical", "description": "Export controls affect rare earth materials.", "status": "open"}, {"id": "RISK-07", "type": "Cyber incident", "severity": "medium", "description": "Supplier systems being restored.", "status": "mitigated"}, {"id": "RISK-08", "type": "Shipping delay", "severity": "low", "description": "Weather-related vessel delay.", "status": "closed"}]

# Multiple sources for common parts; CMP-02, CMP-08, CMP-12, CMP-25 deliberately have one source.
SUPPLIES = [("SUP-001", "CMP-01", 21, 18.4), ("SUP-013", "CMP-01", 18, 19.1), ("SUP-006", "CMP-02", 35, 42.0), ("SUP-007", "CMP-03", 28, 7.5), ("SUP-017", "CMP-03", 14, 8.1), ("SUP-008", "CMP-04", 16, 3.2), ("SUP-009", "CMP-05", 12, 1.1), ("SUP-010", "CMP-06", 24, 14.8), ("SUP-018", "CMP-06", 20, 15.5), ("SUP-005", "CMP-07", 10, 4.7), ("SUP-012", "CMP-08", 45, 26.0), ("SUP-016", "CMP-09", 30, 6.2), ("SUP-003", "CMP-09", 26, 6.8), ("SUP-015", "CMP-10", 22, 33.0), ("SUP-004", "CMP-10", 19, 35.5), ("SUP-017", "CMP-11", 15, 12.2), ("SUP-013", "CMP-12", 40, 48.0), ("SUP-018", "CMP-13", 18, 13.2), ("SUP-011", "CMP-14", 9, 0.9), ("SUP-008", "CMP-15", 14, 1.8), ("SUP-015", "CMP-16", 25, 39.0), ("SUP-010", "CMP-17", 20, 17.0), ("SUP-001", "CMP-18", 23, 31.0), ("SUP-003", "CMP-18", 29, 33.5), ("SUP-004", "CMP-19", 12, 8.4), ("SUP-005", "CMP-20", 10, 1.3), ("SUP-016", "CMP-21", 27, 9.5), ("SUP-020", "CMP-22", 33, 24.0), ("SUP-003", "CMP-23", 25, 28.0), ("SUP-005", "CMP-24", 11, 5.5), ("SUP-014", "CMP-24", 17, 6.1), ("SUP-001", "CMP-25", 21, 16.0)]

def rows_for_links(links, fields): return [dict(zip(fields, link)) for link in links]

def seed(session, query, rows): session.run(query, {"rows": rows}).consume()

def main() -> None:
    database.verify_connectivity()
    with database.driver().session() as session:
        constraints = [
            "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (n:Supplier) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (n:Component) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT warehouse_id IF NOT EXISTS FOR (n:Warehouse) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT region_id IF NOT EXISTS FOR (n:Region) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT riskevent_id IF NOT EXISTS FOR (n:RiskEvent) REQUIRE n.id IS UNIQUE",
        ]
        for query in constraints:
            session.run(query, {}).consume()
        node_seeds = [
            ("UNWIND $rows AS row MERGE (n:Supplier {id: row.id}) SET n += row", SUPPLIERS),
            ("UNWIND $rows AS row MERGE (n:Component {id: row.id}) SET n += row", COMPONENTS),
            ("UNWIND $rows AS row MERGE (n:Product {id: row.id}) SET n += row", PRODUCTS),
            ("UNWIND $rows AS row MERGE (n:Warehouse {id: row.id}) SET n += row", WAREHOUSES),
            ("UNWIND $rows AS row MERGE (n:Region {id: row.id}) SET n += row", REGIONS),
            ("UNWIND $rows AS row MERGE (n:RiskEvent {id: row.id}) SET n += row", RISKS),
        ]
        for query, rows in node_seeds:
            seed(session, query, rows)
        seed(session, "UNWIND $rows AS row MATCH (s:Supplier {id: row.supplier_id}), (c:Component {id: row.component_id}) MERGE (s)-[r:SUPPLIES]->(c) SET r.lead_time_days=row.lead_time_days, r.unit_cost=row.unit_cost", rows_for_links(SUPPLIES, ["supplier_id", "component_id", "lead_time_days", "unit_cost"]))
        usage = [(f"CMP-{i:02}", f"PRD-{((i-1) % 12)+1:02}", (i % 4)+1) for i in range(1, 26)]
        seed(session, "UNWIND $rows AS row MATCH (c:Component {id: row.component_id}), (p:Product {id: row.product_id}) MERGE (c)-[r:USED_IN]->(p) SET r.quantity_required=row.quantity_required", rows_for_links(usage, ["component_id", "product_id", "quantity_required"]))
        stock = [(f"PRD-{i:02}", f"WH-{((i-1) % 5)+1:02}", 450 + i * 85) for i in range(1, 13)]
        seed(session, "UNWIND $rows AS row MATCH (p:Product {id: row.product_id}), (w:Warehouse {id: row.warehouse_id}) MERGE (p)-[r:STORED_AT]->(w) SET r.stock_quantity=row.stock_quantity", rows_for_links(stock, ["product_id", "warehouse_id", "stock_quantity"]))
        seed(session, "UNWIND $rows AS row MATCH (w:Warehouse {id: row.warehouse_id}), (r:Region {id: row.region_id}) MERGE (w)-[:SERVES]->(r)", rows_for_links([("WH-01", "REG-02"), ("WH-02", "REG-04"), ("WH-03", "REG-01"), ("WH-04", "REG-07"), ("WH-05", "REG-08")], ["warehouse_id", "region_id"]))
        supplier_regions = [(f"SUP-{i:03}", region) for i, region in enumerate(["REG-03", "REG-02", "REG-04", "REG-02", "REG-01", "REG-03", "REG-06", "REG-04", "REG-05", "REG-01", "REG-02", "REG-03", "REG-03", "REG-07", "REG-02", "REG-04", "REG-01", "REG-02", "REG-02", "REG-08"], 1)]
        seed(session, "UNWIND $rows AS row MATCH (s:Supplier {id: row.supplier_id}), (r:Region {id: row.region_id}) MERGE (s)-[:LOCATED_IN]->(r)", rows_for_links(supplier_regions, ["supplier_id", "region_id"]))
        seed(session, "UNWIND $rows AS row MATCH (s:Supplier {id: row.supplier_id}), (r:RiskEvent {id: row.risk_id}) MERGE (s)-[:HAS_RISK]->(r)", rows_for_links([("SUP-003", "RISK-01"), ("SUP-003", "RISK-03"), ("SUP-007", "RISK-02"), ("SUP-016", "RISK-05"), ("SUP-012", "RISK-06"), ("SUP-009", "RISK-04"), ("SUP-018", "RISK-07"), ("SUP-014", "RISK-08")], ["supplier_id", "risk_id"]))
        seed(session, "UNWIND $rows AS row MATCH (s:Supplier {id: row.supplier_id}), (a:Supplier {id: row.alternative_id}) MERGE (s)-[:ALTERNATIVE_FOR]->(a)", rows_for_links([("SUP-013", "SUP-001"), ("SUP-018", "SUP-010"), ("SUP-017", "SUP-007"), ("SUP-004", "SUP-015"), ("SUP-005", "SUP-008"), ("SUP-001", "SUP-013")], ["supplier_id", "alternative_id"]))
    print("SupplyShield graph seed completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except DatabaseConfigurationError:
        print("CognoDB is not configured. Copy .env.example to .env and add valid credentials.", file=sys.stderr)
        raise SystemExit(1)
    except DatabaseConnectionError:
        print("Unable to connect to CognoDB. Check the service and your local connection settings.", file=sys.stderr)
        raise SystemExit(1)
