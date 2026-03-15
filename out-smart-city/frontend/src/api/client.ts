const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Domain-specific API — auto-generated from business entities
export const api = {
  // Incident
  listIncidents: (status?: string) =>
    request<any[]>(status ? `/incidents?status=${status}` : '/incidents'),
  getIncident: (id: string) => request<any>(`/incidents/${id}`),
  createIncident: (data: any) =>
    request<any>('/incidents', { method: 'POST', body: JSON.stringify(data) }),
  triageIncident: (id: string) =>
    request<any>(`/incidents/${id}/triage`, { method: 'POST' }),
  dispatchIncident: (id: string) =>
    request<any>(`/incidents/${id}/dispatch`, { method: 'POST' }),
  escalateIncident: (id: string) =>
    request<any>(`/incidents/${id}/escalate`, { method: 'POST' }),
  resolveIncident: (id: string) =>
    request<any>(`/incidents/${id}/resolve`, { method: 'POST' }),
  correlateIncident: (id: string) =>
    request<any>(`/incidents/${id}/correlate`, { method: 'POST' }),

  // Asset
  listAssets: (status?: string) =>
    request<any[]>(status ? `/assets?status=${status}` : '/assets'),
  getAsset: (id: string) => request<any>(`/assets/${id}`),
  createAsset: (data: any) =>
    request<any>('/assets', { method: 'POST', body: JSON.stringify(data) }),
  predictAsset: (id: string) =>
    request<any>(`/assets/${id}/predict`, { method: 'POST' }),
  inspectAsset: (id: string) =>
    request<any>(`/assets/${id}/inspect`, { method: 'POST' }),
  schedule_maintenanceAsset: (id: string) =>
    request<any>(`/assets/${id}/schedule_maintenance`, { method: 'POST' }),
  decommissionAsset: (id: string) =>
    request<any>(`/assets/${id}/decommission`, { method: 'POST' }),

  // Sensor
  listSensors: (status?: string) =>
    request<any[]>(status ? `/sensors?status=${status}` : '/sensors'),
  getSensor: (id: string) => request<any>(`/sensors/${id}`),
  createSensor: (data: any) =>
    request<any>('/sensors', { method: 'POST', body: JSON.stringify(data) }),
  calibrateSensor: (id: string) =>
    request<any>(`/sensors/${id}/calibrate`, { method: 'POST' }),
  acknowledge_alertSensor: (id: string) =>
    request<any>(`/sensors/${id}/acknowledge_alert`, { method: 'POST' }),
  disableSensor: (id: string) =>
    request<any>(`/sensors/${id}/disable`, { method: 'POST' }),

  // ServiceRequest
  listServiceRequests: (status?: string) =>
    request<any[]>(status ? `/service_requests?status=${status}` : '/service_requests'),
  getServiceRequest: (id: string) => request<any>(`/service_requests/${id}`),
  createServiceRequest: (data: any) =>
    request<any>('/service_requests', { method: 'POST', body: JSON.stringify(data) }),
  acknowledgeServiceRequest: (id: string) =>
    request<any>(`/service_requests/${id}/acknowledge`, { method: 'POST' }),
  assignServiceRequest: (id: string) =>
    request<any>(`/service_requests/${id}/assign`, { method: 'POST' }),
  completeServiceRequest: (id: string) =>
    request<any>(`/service_requests/${id}/complete`, { method: 'POST' }),
  rejectServiceRequest: (id: string) =>
    request<any>(`/service_requests/${id}/reject`, { method: 'POST' }),
  check_duplicateServiceRequest: (id: string) =>
    request<any>(`/service_requests/${id}/check_duplicate`, { method: 'POST' }),

  // TransitRoute
  listTransitRoutes: (status?: string) =>
    request<any[]>(status ? `/transit_routes?status=${status}` : '/transit_routes'),
  getTransitRoute: (id: string) => request<any>(`/transit_routes/${id}`),
  createTransitRoute: (data: any) =>
    request<any>('/transit_routes', { method: 'POST', body: JSON.stringify(data) }),
  optimizeTransitRoute: (id: string) =>
    request<any>(`/transit_routes/${id}/optimize`, { method: 'POST' }),
  rerouteTransitRoute: (id: string) =>
    request<any>(`/transit_routes/${id}/reroute`, { method: 'POST' }),
  suspendTransitRoute: (id: string) =>
    request<any>(`/transit_routes/${id}/suspend`, { method: 'POST' }),
  restoreTransitRoute: (id: string) =>
    request<any>(`/transit_routes/${id}/restore`, { method: 'POST' }),

  // Vehicle
  listVehicles: (status?: string) =>
    request<any[]>(status ? `/vehicles?status=${status}` : '/vehicles'),
  getVehicle: (id: string) => request<any>(`/vehicles/${id}`),
  createVehicle: (data: any) =>
    request<any>('/vehicles', { method: 'POST', body: JSON.stringify(data) }),
  deployVehicle: (id: string) =>
    request<any>(`/vehicles/${id}/deploy`, { method: 'POST' }),
  recallVehicle: (id: string) =>
    request<any>(`/vehicles/${id}/recall`, { method: 'POST' }),
  refuelVehicle: (id: string) =>
    request<any>(`/vehicles/${id}/refuel`, { method: 'POST' }),
  schedule_maintenanceVehicle: (id: string) =>
    request<any>(`/vehicles/${id}/schedule_maintenance`, { method: 'POST' }),

  // Zone
  listZones: (status?: string) =>
    request<any[]>(status ? `/zones?status=${status}` : '/zones'),
  getZone: (id: string) => request<any>(`/zones/${id}`),
  createZone: (data: any) =>
    request<any>('/zones', { method: 'POST', body: JSON.stringify(data) }),
  alertZone: (id: string) =>
    request<any>(`/zones/${id}/alert`, { method: 'POST' }),
  evacuateZone: (id: string) =>
    request<any>(`/zones/${id}/evacuate`, { method: 'POST' }),
  clearZone: (id: string) =>
    request<any>(`/zones/${id}/clear`, { method: 'POST' }),

  // WorkOrder
  listWorkOrders: (status?: string) =>
    request<any[]>(status ? `/work_orders?status=${status}` : '/work_orders'),
  getWorkOrder: (id: string) => request<any>(`/work_orders/${id}`),
  createWorkOrder: (data: any) =>
    request<any>('/work_orders', { method: 'POST', body: JSON.stringify(data) }),
  approveWorkOrder: (id: string) =>
    request<any>(`/work_orders/${id}/approve`, { method: 'POST' }),
  scheduleWorkOrder: (id: string) =>
    request<any>(`/work_orders/${id}/schedule`, { method: 'POST' }),
  startWorkOrder: (id: string) =>
    request<any>(`/work_orders/${id}/start`, { method: 'POST' }),
  completeWorkOrder: (id: string) =>
    request<any>(`/work_orders/${id}/complete`, { method: 'POST' }),
  cancelWorkOrder: (id: string) =>
    request<any>(`/work_orders/${id}/cancel`, { method: 'POST' }),

  // AuditLog
  listAuditLogs: (status?: string) =>
    request<any[]>(status ? `/audit_logs?status=${status}` : '/audit_logs'),
  getAuditLog: (id: string) => request<any>(`/audit_logs/${id}`),
  createAuditLog: (data: any) =>
    request<any>('/audit_logs', { method: 'POST', body: JSON.stringify(data) }),
};