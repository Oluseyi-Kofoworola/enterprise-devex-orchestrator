"""API v1 router -- domain-specific endpoints.

Auto-generated from intent specification. Entities and endpoints
are derived from the business requirements, not hardcoded templates.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from api.v1.schemas import (IncidentCreate, IncidentResponse, AssetCreate, AssetResponse, SensorCreate, SensorResponse, ServiceRequestCreate, ServiceRequestResponse, TransitRouteCreate, TransitRouteResponse, VehicleCreate, VehicleResponse, ZoneCreate, ZoneResponse, WorkOrderCreate, WorkOrderResponse, AuditLogCreate, AuditLogResponse)
from core.dependencies import get_settings, get_repository
from core.config import Settings
from core.services import (IncidentService, AssetService, SensorService, ServiceRequestService, TransitRouteService, VehicleService, ZoneService, WorkOrderService, AuditLogService)
from azure.storage.blob import BlobServiceClient
from core.dependencies import get_blob_service

router = APIRouter()

# --- Incident CRUD ---
@router.get("/incidents", response_model=list[IncidentResponse], summary="List incidents")
async def list_incidents(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("incident", settings.storage_mode)
    svc = IncidentService(repo)
    return svc.list_all(status)

@router.post("/incidents", response_model=IncidentResponse, status_code=201, summary="Create incident")
async def create_incident(payload: IncidentCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("incident", settings.storage_mode)
    svc = IncidentService(repo)
    return svc.create(payload)

@router.get("/incidents/{incident_id}", summary="Get incident by ID")
async def get_incident(incident_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("incident", settings.storage_mode)
    svc = IncidentService(repo)
    record = svc.get(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record

@router.put("/incidents/{incident_id}", summary="Update incident")
async def update_incident(incident_id: str, payload: IncidentCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("incident", settings.storage_mode)
    svc = IncidentService(repo)
    record = svc.update(incident_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record

@router.delete("/incidents/{incident_id}", status_code=204, summary="Delete incident")
async def delete_incident(incident_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("incident", settings.storage_mode)
    svc = IncidentService(repo)
    if not svc.delete(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")


@router.post("/incidents/{incident_id}/triage", summary="AI-powered triage with severity + category classification")
async def triage_incident(incident_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("incident", settings.storage_mode)
    svc = IncidentService(repo)
    record = svc.triage(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record


@router.post("/incidents/{incident_id}/dispatch", summary="AI-recommended dispatch with unit matching")
async def dispatch_incident(incident_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("incident", settings.storage_mode)
    svc = IncidentService(repo)
    record = svc.dispatch(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record


@router.post("/incidents/{incident_id}/escalate", summary="Escalate to higher severity with AI justification")
async def escalate_incident(incident_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("incident", settings.storage_mode)
    svc = IncidentService(repo)
    record = svc.escalate(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record


@router.post("/incidents/{incident_id}/resolve", summary="Close incident with resolution notes and response metrics")
async def resolve_incident(incident_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("incident", settings.storage_mode)
    svc = IncidentService(repo)
    record = svc.resolve(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record


@router.post("/incidents/{incident_id}/correlate", summary="AI correlation with nearby incidents and sensor anomalies")
async def correlate_incident(incident_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("incident", settings.storage_mode)
    svc = IncidentService(repo)
    record = svc.correlate(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record

# --- Asset CRUD ---
@router.get("/assets", response_model=list[AssetResponse], summary="List assets")
async def list_assets(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("asset", settings.storage_mode)
    svc = AssetService(repo)
    return svc.list_all(status)

@router.post("/assets", response_model=AssetResponse, status_code=201, summary="Create asset")
async def create_asset(payload: AssetCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("asset", settings.storage_mode)
    svc = AssetService(repo)
    return svc.create(payload)

@router.get("/assets/{asset_id}", summary="Get asset by ID")
async def get_asset(asset_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("asset", settings.storage_mode)
    svc = AssetService(repo)
    record = svc.get(asset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
    return record

@router.put("/assets/{asset_id}", summary="Update asset")
async def update_asset(asset_id: str, payload: AssetCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("asset", settings.storage_mode)
    svc = AssetService(repo)
    record = svc.update(asset_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
    return record

@router.delete("/assets/{asset_id}", status_code=204, summary="Delete asset")
async def delete_asset(asset_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("asset", settings.storage_mode)
    svc = AssetService(repo)
    if not svc.delete(asset_id):
        raise HTTPException(status_code=404, detail="Asset not found")


@router.post("/assets/{asset_id}/predict", summary="AI failure prediction with confidence + time-to-failure")
async def predict_asset(asset_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("asset", settings.storage_mode)
    svc = AssetService(repo)
    record = svc.predict(asset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
    return record


@router.post("/assets/{asset_id}/inspect", summary="Record inspection with AI-generated health assessment")
async def inspect_asset(asset_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("asset", settings.storage_mode)
    svc = AssetService(repo)
    record = svc.inspect(asset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
    return record


@router.post("/assets/{asset_id}/schedule_maintenance", summary="AI-recommended maintenance scheduling")
async def schedule_maintenance_asset(asset_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("asset", settings.storage_mode)
    svc = AssetService(repo)
    record = svc.schedule_maintenance(asset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
    return record


@router.post("/assets/{asset_id}/decommission", summary="Retire asset with AI-generated replacement recommendation")
async def decommission_asset(asset_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("asset", settings.storage_mode)
    svc = AssetService(repo)
    record = svc.decommission(asset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
    return record

# --- Sensor CRUD ---
@router.get("/sensors", response_model=list[SensorResponse], summary="List sensors")
async def list_sensors(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("sensor", settings.storage_mode)
    svc = SensorService(repo)
    return svc.list_all(status)

@router.post("/sensors", response_model=SensorResponse, status_code=201, summary="Create sensor")
async def create_sensor(payload: SensorCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("sensor", settings.storage_mode)
    svc = SensorService(repo)
    return svc.create(payload)

@router.get("/sensors/{sensor_id}", summary="Get sensor by ID")
async def get_sensor(sensor_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("sensor", settings.storage_mode)
    svc = SensorService(repo)
    record = svc.get(sensor_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return record

@router.put("/sensors/{sensor_id}", summary="Update sensor")
async def update_sensor(sensor_id: str, payload: SensorCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("sensor", settings.storage_mode)
    svc = SensorService(repo)
    record = svc.update(sensor_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return record

@router.delete("/sensors/{sensor_id}", status_code=204, summary="Delete sensor")
async def delete_sensor(sensor_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("sensor", settings.storage_mode)
    svc = SensorService(repo)
    if not svc.delete(sensor_id):
        raise HTTPException(status_code=404, detail="Sensor not found")


@router.post("/sensors/{sensor_id}/calibrate", summary="Initiate sensor calibration cycle")
async def calibrate_sensor(sensor_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("sensor", settings.storage_mode)
    svc = SensorService(repo)
    record = svc.calibrate(sensor_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return record


@router.post("/sensors/{sensor_id}/acknowledge_alert", summary="Acknowledge sensor threshold alert")
async def acknowledge_alert_sensor(sensor_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("sensor", settings.storage_mode)
    svc = SensorService(repo)
    record = svc.acknowledge_alert(sensor_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return record


@router.post("/sensors/{sensor_id}/disable", summary="Temporarily disable sensor with reason")
async def disable_sensor(sensor_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("sensor", settings.storage_mode)
    svc = SensorService(repo)
    record = svc.disable(sensor_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return record

# --- ServiceRequest CRUD ---
@router.get("/service_requests", response_model=list[ServiceRequestResponse], summary="List servicerequests")
async def list_service_requests(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("service_request", settings.storage_mode)
    svc = ServiceRequestService(repo)
    return svc.list_all(status)

@router.post("/service_requests", response_model=ServiceRequestResponse, status_code=201, summary="Create servicerequest")
async def create_service_request(payload: ServiceRequestCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("service_request", settings.storage_mode)
    svc = ServiceRequestService(repo)
    return svc.create(payload)

@router.get("/service_requests/{service_request_id}", summary="Get servicerequest by ID")
async def get_service_request(service_request_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("service_request", settings.storage_mode)
    svc = ServiceRequestService(repo)
    record = svc.get(service_request_id)
    if not record:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")
    return record

@router.put("/service_requests/{service_request_id}", summary="Update servicerequest")
async def update_service_request(service_request_id: str, payload: ServiceRequestCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("service_request", settings.storage_mode)
    svc = ServiceRequestService(repo)
    record = svc.update(service_request_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")
    return record

@router.delete("/service_requests/{service_request_id}", status_code=204, summary="Delete servicerequest")
async def delete_service_request(service_request_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("service_request", settings.storage_mode)
    svc = ServiceRequestService(repo)
    if not svc.delete(service_request_id):
        raise HTTPException(status_code=404, detail="ServiceRequest not found")


@router.post("/service_requests/{service_request_id}/acknowledge", summary="Staff acknowledges receipt")
async def acknowledge_service_request(service_request_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("service_request", settings.storage_mode)
    svc = ServiceRequestService(repo)
    record = svc.acknowledge(service_request_id)
    if not record:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")
    return record


@router.post("/service_requests/{service_request_id}/assign", summary="Assign to maintenance team")
async def assign_service_request(service_request_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("service_request", settings.storage_mode)
    svc = ServiceRequestService(repo)
    record = svc.assign(service_request_id)
    if not record:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")
    return record


@router.post("/service_requests/{service_request_id}/complete", summary="Mark completed with resolution details")
async def complete_service_request(service_request_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("service_request", settings.storage_mode)
    svc = ServiceRequestService(repo)
    record = svc.complete(service_request_id)
    if not record:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")
    return record


@router.post("/service_requests/{service_request_id}/reject", summary="Reject with AI-generated explanation")
async def reject_service_request(service_request_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("service_request", settings.storage_mode)
    svc = ServiceRequestService(repo)
    record = svc.reject(service_request_id)
    if not record:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")
    return record


@router.post("/service_requests/{service_request_id}/check_duplicate", summary="AI semantic duplicate detection")
async def check_duplicate_service_request(service_request_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("service_request", settings.storage_mode)
    svc = ServiceRequestService(repo)
    record = svc.check_duplicate(service_request_id)
    if not record:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")
    return record

# --- TransitRoute CRUD ---
@router.get("/transit_routes", response_model=list[TransitRouteResponse], summary="List transitroutes")
async def list_transit_routes(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("transit_route", settings.storage_mode)
    svc = TransitRouteService(repo)
    return svc.list_all(status)

@router.post("/transit_routes", response_model=TransitRouteResponse, status_code=201, summary="Create transitroute")
async def create_transit_route(payload: TransitRouteCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("transit_route", settings.storage_mode)
    svc = TransitRouteService(repo)
    return svc.create(payload)

@router.get("/transit_routes/{transit_route_id}", summary="Get transitroute by ID")
async def get_transit_route(transit_route_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("transit_route", settings.storage_mode)
    svc = TransitRouteService(repo)
    record = svc.get(transit_route_id)
    if not record:
        raise HTTPException(status_code=404, detail="TransitRoute not found")
    return record

@router.put("/transit_routes/{transit_route_id}", summary="Update transitroute")
async def update_transit_route(transit_route_id: str, payload: TransitRouteCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("transit_route", settings.storage_mode)
    svc = TransitRouteService(repo)
    record = svc.update(transit_route_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="TransitRoute not found")
    return record

@router.delete("/transit_routes/{transit_route_id}", status_code=204, summary="Delete transitroute")
async def delete_transit_route(transit_route_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("transit_route", settings.storage_mode)
    svc = TransitRouteService(repo)
    if not svc.delete(transit_route_id):
        raise HTTPException(status_code=404, detail="TransitRoute not found")


@router.post("/transit_routes/{transit_route_id}/optimize", summary="AI route optimization based on ridership patterns")
async def optimize_transit_route(transit_route_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("transit_route", settings.storage_mode)
    svc = TransitRouteService(repo)
    record = svc.optimize(transit_route_id)
    if not record:
        raise HTTPException(status_code=404, detail="TransitRoute not found")
    return record


@router.post("/transit_routes/{transit_route_id}/reroute", summary="Activate alternative route due to incident")
async def reroute_transit_route(transit_route_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("transit_route", settings.storage_mode)
    svc = TransitRouteService(repo)
    record = svc.reroute(transit_route_id)
    if not record:
        raise HTTPException(status_code=404, detail="TransitRoute not found")
    return record


@router.post("/transit_routes/{transit_route_id}/suspend", summary="Suspend route with AI impact analysis")
async def suspend_transit_route(transit_route_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("transit_route", settings.storage_mode)
    svc = TransitRouteService(repo)
    record = svc.suspend(transit_route_id)
    if not record:
        raise HTTPException(status_code=404, detail="TransitRoute not found")
    return record


@router.post("/transit_routes/{transit_route_id}/restore", summary="Restore route to normal operations")
async def restore_transit_route(transit_route_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("transit_route", settings.storage_mode)
    svc = TransitRouteService(repo)
    record = svc.restore(transit_route_id)
    if not record:
        raise HTTPException(status_code=404, detail="TransitRoute not found")
    return record

# --- Vehicle CRUD ---
@router.get("/vehicles", response_model=list[VehicleResponse], summary="List vehicles")
async def list_vehicles(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("vehicle", settings.storage_mode)
    svc = VehicleService(repo)
    return svc.list_all(status)

@router.post("/vehicles", response_model=VehicleResponse, status_code=201, summary="Create vehicle")
async def create_vehicle(payload: VehicleCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("vehicle", settings.storage_mode)
    svc = VehicleService(repo)
    return svc.create(payload)

@router.get("/vehicles/{vehicle_id}", summary="Get vehicle by ID")
async def get_vehicle(vehicle_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("vehicle", settings.storage_mode)
    svc = VehicleService(repo)
    record = svc.get(vehicle_id)
    if not record:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return record

@router.put("/vehicles/{vehicle_id}", summary="Update vehicle")
async def update_vehicle(vehicle_id: str, payload: VehicleCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("vehicle", settings.storage_mode)
    svc = VehicleService(repo)
    record = svc.update(vehicle_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return record

@router.delete("/vehicles/{vehicle_id}", status_code=204, summary="Delete vehicle")
async def delete_vehicle(vehicle_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("vehicle", settings.storage_mode)
    svc = VehicleService(repo)
    if not svc.delete(vehicle_id):
        raise HTTPException(status_code=404, detail="Vehicle not found")


@router.post("/vehicles/{vehicle_id}/deploy", summary="Deploy vehicle to incident or assignment")
async def deploy_vehicle(vehicle_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("vehicle", settings.storage_mode)
    svc = VehicleService(repo)
    record = svc.deploy(vehicle_id)
    if not record:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return record


@router.post("/vehicles/{vehicle_id}/recall", summary="Recall vehicle to depot")
async def recall_vehicle(vehicle_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("vehicle", settings.storage_mode)
    svc = VehicleService(repo)
    record = svc.recall(vehicle_id)
    if not record:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return record


@router.post("/vehicles/{vehicle_id}/refuel", summary="Log refueling with gallons and cost")
async def refuel_vehicle(vehicle_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("vehicle", settings.storage_mode)
    svc = VehicleService(repo)
    record = svc.refuel(vehicle_id)
    if not record:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return record


@router.post("/vehicles/{vehicle_id}/schedule_maintenance", summary="AI-predicted maintenance scheduling")
async def schedule_maintenance_vehicle(vehicle_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("vehicle", settings.storage_mode)
    svc = VehicleService(repo)
    record = svc.schedule_maintenance(vehicle_id)
    if not record:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return record

# --- Zone CRUD ---
@router.get("/zones", response_model=list[ZoneResponse], summary="List zones")
async def list_zones(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("zone", settings.storage_mode)
    svc = ZoneService(repo)
    return svc.list_all(status)

@router.post("/zones", response_model=ZoneResponse, status_code=201, summary="Create zone")
async def create_zone(payload: ZoneCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("zone", settings.storage_mode)
    svc = ZoneService(repo)
    return svc.create(payload)

@router.get("/zones/{zone_id}", summary="Get zone by ID")
async def get_zone(zone_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("zone", settings.storage_mode)
    svc = ZoneService(repo)
    record = svc.get(zone_id)
    if not record:
        raise HTTPException(status_code=404, detail="Zone not found")
    return record

@router.put("/zones/{zone_id}", summary="Update zone")
async def update_zone(zone_id: str, payload: ZoneCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("zone", settings.storage_mode)
    svc = ZoneService(repo)
    record = svc.update(zone_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="Zone not found")
    return record

@router.delete("/zones/{zone_id}", status_code=204, summary="Delete zone")
async def delete_zone(zone_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("zone", settings.storage_mode)
    svc = ZoneService(repo)
    if not svc.delete(zone_id):
        raise HTTPException(status_code=404, detail="Zone not found")


@router.post("/zones/{zone_id}/alert", summary="Raise zone alert level with AI risk assessment")
async def alert_zone(zone_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("zone", settings.storage_mode)
    svc = ZoneService(repo)
    record = svc.alert(zone_id)
    if not record:
        raise HTTPException(status_code=404, detail="Zone not found")
    return record


@router.post("/zones/{zone_id}/evacuate", summary="Initiate zone evacuation protocol")
async def evacuate_zone(zone_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("zone", settings.storage_mode)
    svc = ZoneService(repo)
    record = svc.evacuate(zone_id)
    if not record:
        raise HTTPException(status_code=404, detail="Zone not found")
    return record


@router.post("/zones/{zone_id}/clear", summary="Clear zone alert status")
async def clear_zone(zone_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("zone", settings.storage_mode)
    svc = ZoneService(repo)
    record = svc.clear(zone_id)
    if not record:
        raise HTTPException(status_code=404, detail="Zone not found")
    return record

# --- WorkOrder CRUD ---
@router.get("/work_orders", response_model=list[WorkOrderResponse], summary="List workorders")
async def list_work_orders(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("work_order", settings.storage_mode)
    svc = WorkOrderService(repo)
    return svc.list_all(status)

@router.post("/work_orders", response_model=WorkOrderResponse, status_code=201, summary="Create workorder")
async def create_work_order(payload: WorkOrderCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("work_order", settings.storage_mode)
    svc = WorkOrderService(repo)
    return svc.create(payload)

@router.get("/work_orders/{work_order_id}", summary="Get workorder by ID")
async def get_work_order(work_order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("work_order", settings.storage_mode)
    svc = WorkOrderService(repo)
    record = svc.get(work_order_id)
    if not record:
        raise HTTPException(status_code=404, detail="WorkOrder not found")
    return record

@router.put("/work_orders/{work_order_id}", summary="Update workorder")
async def update_work_order(work_order_id: str, payload: WorkOrderCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("work_order", settings.storage_mode)
    svc = WorkOrderService(repo)
    record = svc.update(work_order_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="WorkOrder not found")
    return record

@router.delete("/work_orders/{work_order_id}", status_code=204, summary="Delete workorder")
async def delete_work_order(work_order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("work_order", settings.storage_mode)
    svc = WorkOrderService(repo)
    if not svc.delete(work_order_id):
        raise HTTPException(status_code=404, detail="WorkOrder not found")


@router.post("/work_orders/{work_order_id}/approve", summary="Approve work order for scheduling")
async def approve_work_order(work_order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("work_order", settings.storage_mode)
    svc = WorkOrderService(repo)
    record = svc.approve(work_order_id)
    if not record:
        raise HTTPException(status_code=404, detail="WorkOrder not found")
    return record


@router.post("/work_orders/{work_order_id}/schedule", summary="Set maintenance window")
async def schedule_work_order(work_order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("work_order", settings.storage_mode)
    svc = WorkOrderService(repo)
    record = svc.schedule(work_order_id)
    if not record:
        raise HTTPException(status_code=404, detail="WorkOrder not found")
    return record


@router.post("/work_orders/{work_order_id}/start", summary="Begin work execution")
async def start_work_order(work_order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("work_order", settings.storage_mode)
    svc = WorkOrderService(repo)
    record = svc.start(work_order_id)
    if not record:
        raise HTTPException(status_code=404, detail="WorkOrder not found")
    return record


@router.post("/work_orders/{work_order_id}/complete", summary="Complete with actual costs and notes")
async def complete_work_order(work_order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("work_order", settings.storage_mode)
    svc = WorkOrderService(repo)
    record = svc.complete(work_order_id)
    if not record:
        raise HTTPException(status_code=404, detail="WorkOrder not found")
    return record


@router.post("/work_orders/{work_order_id}/cancel", summary="Cancel with AI impact assessment")
async def cancel_work_order(work_order_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("work_order", settings.storage_mode)
    svc = WorkOrderService(repo)
    record = svc.cancel(work_order_id)
    if not record:
        raise HTTPException(status_code=404, detail="WorkOrder not found")
    return record

# --- AuditLog CRUD ---
@router.get("/audit_logs", response_model=list[AuditLogResponse], summary="List auditlogs")
async def list_audit_logs(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("audit_log", settings.storage_mode)
    svc = AuditLogService(repo)
    return svc.list_all(status)

@router.post("/audit_logs", response_model=AuditLogResponse, status_code=201, summary="Create auditlog")
async def create_audit_log(payload: AuditLogCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("audit_log", settings.storage_mode)
    svc = AuditLogService(repo)
    return svc.create(payload)

@router.get("/audit_logs/{audit_log_id}", summary="Get auditlog by ID")
async def get_audit_log(audit_log_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("audit_log", settings.storage_mode)
    svc = AuditLogService(repo)
    record = svc.get(audit_log_id)
    if not record:
        raise HTTPException(status_code=404, detail="AuditLog not found")
    return record

@router.put("/audit_logs/{audit_log_id}", summary="Update auditlog")
async def update_audit_log(audit_log_id: str, payload: AuditLogCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("audit_log", settings.storage_mode)
    svc = AuditLogService(repo)
    record = svc.update(audit_log_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="AuditLog not found")
    return record

@router.delete("/audit_logs/{audit_log_id}", status_code=204, summary="Delete auditlog")
async def delete_audit_log(audit_log_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("audit_log", settings.storage_mode)
    svc = AuditLogService(repo)
    if not svc.delete(audit_log_id):
        raise HTTPException(status_code=404, detail="AuditLog not found")


@router.get("/storage/containers", summary="List storage containers")
async def list_containers(
    storage: BlobServiceClient = Depends(get_blob_service),
):
    containers = [c["name"] for c in storage.list_containers(max_results=10)]
    return {"containers": containers}
