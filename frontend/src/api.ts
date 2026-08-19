const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { headers: { 'Content-Type': 'application/json', ...options?.headers }, ...options })
  if (!response.ok) throw new Error('Request failed')
  return response.json() as Promise<T>
}

export type Supplier = { id: string; name: string; country: string; reliability_score: number; status: string; region?: string; supplied_component_count: number; active_risk_count: number }
export type Product = { id: string; name: string; category: string; component_count: number; warehouse_count: number; supply_risk_level: string }
export type Summary = { total_suppliers: number; active_suppliers: number; high_risk_suppliers: number; total_products: number; critical_single_source_components: number; open_risk_events: number }
export type SupplyChain = { id: string; name: string; category: string; required_components: Array<{ id: string; name: string; category: string; criticality: string; suppliers: Array<{id:string;name:string;status:string;reliability_score:number;region?:string}>}>; warehouses: Array<{id:string;name:string;city:string;capacity:number;stock_quantity:number;served_regions:string[]}> }
