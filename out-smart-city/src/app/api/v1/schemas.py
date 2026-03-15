"""API v1 request/response schemas.

Auto-generated from intent specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

class IncidentCreate(BaseModel):
    """Schema for creating a incident."""

    title: str = Field(default=..., description="")
    description: str = Field(default=..., description="")
    category: str = Field(default=..., description="fire/medical/traffic/utility/environmental/security")
    severity: str = Field(default=..., description="critical/high/medium/low")
    latitude: float = Field(default=..., description="")
    longitude: float = Field(default=..., description="")
    zone_id: str = Field(default=..., description="")
    reporter_name: str = Field(default=..., description="")
    reporter_phone: str = Field(default=..., description="")
    affected_population: int = Field(default=..., description="")
    estimated_damage: float = Field(default=..., description="")
    ai_confidence: float = Field(default=..., description="")
    ai_triage_notes: str = Field(default=..., description="")
    photo_url: str = Field(default=..., description="")
    audio_transcript: str = Field(default=..., description="")
    assigned_units: list[str] = Field(default=..., description="")
    resolution_notes: str = Field(default=..., description="")
    response_time_minutes: float = Field(default=..., description="")


class IncidentResponse(BaseModel):
    """Schema returned by incident endpoints."""

    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="")
    description: str = Field(..., description="")
    category: str = Field(..., description="fire/medical/traffic/utility/environmental/security")
    severity: str = Field(..., description="critical/high/medium/low")
    status: str = Field(..., description="reported/triaged/dispatched/in_progress/resolved/closed")
    latitude: float = Field(..., description="")
    longitude: float = Field(..., description="")
    zone_id: str = Field(..., description="")
    reporter_name: str = Field(..., description="")
    reporter_phone: str = Field(..., description="")
    affected_population: int = Field(..., description="")
    estimated_damage: float = Field(..., description="")
    ai_confidence: float = Field(..., description="")
    ai_triage_notes: str = Field(..., description="")
    photo_url: str = Field(..., description="")
    audio_transcript: str = Field(..., description="")
    assigned_units: list[str] = Field(default_factory=list, description="")
    resolution_notes: str = Field(..., description="")
    response_time_minutes: float = Field(..., description="")
    created_at: str = Field(default="", description="Creation timestamp")


class AssetCreate(BaseModel):
    """Schema for creating a asset."""

    name: str = Field(default=..., description="")
    asset_type: str = Field(default=..., description="bridge/road/pipe/transformer/pump/signal/building/park")
    location_address: str = Field(default=..., description="")
    latitude: float = Field(default=..., description="")
    longitude: float = Field(default=..., description="")
    zone_id: str = Field(default=..., description="")
    install_date: str = Field(default=..., description="")
    expected_lifespan_years: int = Field(default=..., description="")
    manufacturer: str = Field(default=..., description="")
    model_number: str = Field(default=..., description="")
    last_inspection_date: str = Field(default=..., description="")
    health_score: float = Field(default=..., description="")
    replacement_cost: float = Field(default=..., description="")
    maintenance_budget: float = Field(default=..., description="")
    sensor_ids: list[str] = Field(default=..., description="")
    ai_failure_prediction: str = Field(default=..., description="")
    ai_health_trend: str = Field(default=..., description="")


class AssetResponse(BaseModel):
    """Schema returned by asset endpoints."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="")
    asset_type: str = Field(..., description="bridge/road/pipe/transformer/pump/signal/building/park")
    status: str = Field(..., description="operational/degraded/maintenance/offline/decommissioned")
    location_address: str = Field(..., description="")
    latitude: float = Field(..., description="")
    longitude: float = Field(..., description="")
    zone_id: str = Field(..., description="")
    install_date: str = Field(..., description="")
    expected_lifespan_years: int = Field(..., description="")
    manufacturer: str = Field(..., description="")
    model_number: str = Field(..., description="")
    last_inspection_date: str = Field(..., description="")
    health_score: float = Field(..., description="")
    replacement_cost: float = Field(..., description="")
    maintenance_budget: float = Field(..., description="")
    sensor_ids: list[str] = Field(default_factory=list, description="")
    ai_failure_prediction: str = Field(..., description="")
    ai_health_trend: str = Field(..., description="")
    created_at: str = Field(default="", description="Creation timestamp")


class SensorCreate(BaseModel):
    """Schema for creating a sensor."""

    name: str = Field(default=..., description="")
    sensor_type: str = Field(default=..., description="temperature/air_quality/water_flow/power_load/traffic/acoustic/vibration/pressure/humidity/radiation")
    latitude: float = Field(default=..., description="")
    longitude: float = Field(default=..., description="")
    zone_id: str = Field(default=..., description="")
    asset_id: str = Field(default=..., description="")
    vendor: str = Field(default=..., description="")
    protocol: str = Field(default=..., description="")
    last_reading_value: float = Field(default=..., description="")
    last_reading_unit: str = Field(default=..., description="")
    last_reading_timestamp: str = Field(default=..., description="")
    threshold_min: float = Field(default=..., description="")
    threshold_max: float = Field(default=..., description="")
    alert_enabled: bool = Field(default=..., description="")
    battery_level: float = Field(default=..., description="")
    firmware_version: str = Field(default=..., description="")
    calibration_date: str = Field(default=..., description="")


class SensorResponse(BaseModel):
    """Schema returned by sensor endpoints."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="")
    sensor_type: str = Field(..., description="temperature/air_quality/water_flow/power_load/traffic/acoustic/vibration/pressure/humidity/radiation")
    status: str = Field(..., description="online/offline/calibrating/error/maintenance")
    latitude: float = Field(..., description="")
    longitude: float = Field(..., description="")
    zone_id: str = Field(..., description="")
    asset_id: str = Field(..., description="")
    vendor: str = Field(..., description="")
    protocol: str = Field(..., description="")
    last_reading_value: float = Field(..., description="")
    last_reading_unit: str = Field(..., description="")
    last_reading_timestamp: str = Field(..., description="")
    threshold_min: float = Field(..., description="")
    threshold_max: float = Field(..., description="")
    alert_enabled: bool = Field(..., description="")
    battery_level: float = Field(..., description="")
    firmware_version: str = Field(..., description="")
    calibration_date: str = Field(..., description="")
    created_at: str = Field(default="", description="Creation timestamp")


class ServiceRequestCreate(BaseModel):
    """Schema for creating a servicerequest."""

    title: str = Field(default=..., description="")
    description: str = Field(default=..., description="")
    category: str = Field(default=..., description="pothole/streetlight/noise/graffiti/water/sewer/parks/trash/permits/other")
    priority: str = Field(default=..., description="urgent/high/medium/low")
    citizen_name: str = Field(default=..., description="")
    citizen_email: str = Field(default=..., description="")
    citizen_phone: str = Field(default=..., description="")
    latitude: float = Field(default=..., description="")
    longitude: float = Field(default=..., description="")
    zone_id: str = Field(default=..., description="")
    assigned_team: str = Field(default=..., description="")
    estimated_completion_date: str = Field(default=..., description="")
    ai_duplicate_score: float = Field(default=..., description="")
    ai_category_confidence: float = Field(default=..., description="")
    ai_suggested_resolution: str = Field(default=..., description="")
    photo_url: str = Field(default=..., description="")
    satisfaction_rating: int = Field(default=..., description="")


class ServiceRequestResponse(BaseModel):
    """Schema returned by servicerequest endpoints."""

    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="")
    description: str = Field(..., description="")
    category: str = Field(..., description="pothole/streetlight/noise/graffiti/water/sewer/parks/trash/permits/other")
    priority: str = Field(..., description="urgent/high/medium/low")
    status: str = Field(..., description="submitted/acknowledged/in_progress/awaiting_parts/scheduled/completed/rejected")
    citizen_name: str = Field(..., description="")
    citizen_email: str = Field(..., description="")
    citizen_phone: str = Field(..., description="")
    latitude: float = Field(..., description="")
    longitude: float = Field(..., description="")
    zone_id: str = Field(..., description="")
    assigned_team: str = Field(..., description="")
    estimated_completion_date: str = Field(..., description="")
    ai_duplicate_score: float = Field(..., description="")
    ai_category_confidence: float = Field(..., description="")
    ai_suggested_resolution: str = Field(..., description="")
    photo_url: str = Field(..., description="")
    satisfaction_rating: int = Field(..., description="")
    created_at: str = Field(default="", description="Creation timestamp")


class TransitRouteCreate(BaseModel):
    """Schema for creating a transitroute."""

    name: str = Field(default=..., description="")
    route_number: str = Field(default=..., description="")
    route_type: str = Field(default=..., description="bus/rail/ferry/shuttle")
    start_location: str = Field(default=..., description="")
    end_location: str = Field(default=..., description="")
    total_stops: int = Field(default=..., description="")
    daily_ridership: int = Field(default=..., description="")
    average_delay_minutes: float = Field(default=..., description="")
    on_time_percentage: float = Field(default=..., description="")
    fare_revenue_daily: float = Field(default=..., description="")
    operating_cost_daily: float = Field(default=..., description="")
    vehicle_count: int = Field(default=..., description="")
    zone_ids: list[str] = Field(default=..., description="")
    ai_demand_forecast: str = Field(default=..., description="")
    ai_optimization_notes: str = Field(default=..., description="")
    last_disruption_reason: str = Field(default=..., description="")


class TransitRouteResponse(BaseModel):
    """Schema returned by transitroute endpoints."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="")
    route_number: str = Field(..., description="")
    route_type: str = Field(..., description="bus/rail/ferry/shuttle")
    status: str = Field(..., description="active/delayed/suspended/rerouted/out_of_service")
    start_location: str = Field(..., description="")
    end_location: str = Field(..., description="")
    total_stops: int = Field(..., description="")
    daily_ridership: int = Field(..., description="")
    average_delay_minutes: float = Field(..., description="")
    on_time_percentage: float = Field(..., description="")
    fare_revenue_daily: float = Field(..., description="")
    operating_cost_daily: float = Field(..., description="")
    vehicle_count: int = Field(..., description="")
    zone_ids: list[str] = Field(default_factory=list, description="")
    ai_demand_forecast: str = Field(..., description="")
    ai_optimization_notes: str = Field(..., description="")
    last_disruption_reason: str = Field(..., description="")
    created_at: str = Field(default="", description="Creation timestamp")


class VehicleCreate(BaseModel):
    """Schema for creating a vehicle."""

    name: str = Field(default=..., description="")
    vehicle_type: str = Field(default=..., description="sedan/suv/truck/van/bus/ambulance/fire_engine/utility")
    license_plate: str = Field(default=..., description="")
    vin_number: str = Field(default=..., description="")
    current_latitude: float = Field(default=..., description="")
    current_longitude: float = Field(default=..., description="")
    assigned_department: str = Field(default=..., description="")
    driver_name: str = Field(default=..., description="")
    fuel_level_pct: float = Field(default=..., description="")
    odometer_miles: int = Field(default=..., description="")
    last_maintenance_date: str = Field(default=..., description="")
    next_maintenance_due: str = Field(default=..., description="")
    maintenance_cost_ytd: float = Field(default=..., description="")
    ai_maintenance_prediction: str = Field(default=..., description="")
    gps_speed_mph: float = Field(default=..., description="")
    engine_health_score: float = Field(default=..., description="")


class VehicleResponse(BaseModel):
    """Schema returned by vehicle endpoints."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="")
    vehicle_type: str = Field(..., description="sedan/suv/truck/van/bus/ambulance/fire_engine/utility")
    status: str = Field(..., description="available/deployed/maintenance/refueling/out_of_service")
    license_plate: str = Field(..., description="")
    vin_number: str = Field(..., description="")
    current_latitude: float = Field(..., description="")
    current_longitude: float = Field(..., description="")
    assigned_department: str = Field(..., description="")
    driver_name: str = Field(..., description="")
    fuel_level_pct: float = Field(..., description="")
    odometer_miles: int = Field(..., description="")
    last_maintenance_date: str = Field(..., description="")
    next_maintenance_due: str = Field(..., description="")
    maintenance_cost_ytd: float = Field(..., description="")
    ai_maintenance_prediction: str = Field(..., description="")
    gps_speed_mph: float = Field(..., description="")
    engine_health_score: float = Field(..., description="")
    created_at: str = Field(default="", description="Creation timestamp")


class ZoneCreate(BaseModel):
    """Schema for creating a zone."""

    name: str = Field(default=..., description="")
    zone_code: str = Field(default=..., description="")
    zone_type: str = Field(default=..., description="residential/commercial/industrial/mixed/park/transit_hub")
    population: int = Field(default=..., description="")
    area_sq_miles: float = Field(default=..., description="")
    council_district: int = Field(default=..., description="")
    emergency_contacts: list[str] = Field(default=..., description="")
    active_incident_count: int = Field(default=..., description="")
    active_sensor_count: int = Field(default=..., description="")
    active_asset_count: int = Field(default=..., description="")
    air_quality_index: float = Field(default=..., description="")
    noise_level_db: float = Field(default=..., description="")
    power_load_pct: float = Field(default=..., description="")
    ai_risk_score: float = Field(default=..., description="")
    ai_trend_summary: str = Field(default=..., description="")


class ZoneResponse(BaseModel):
    """Schema returned by zone endpoints."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="")
    zone_code: str = Field(..., description="")
    zone_type: str = Field(..., description="residential/commercial/industrial/mixed/park/transit_hub")
    status: str = Field(..., description="normal/alert/emergency/evacuation/construction")
    population: int = Field(..., description="")
    area_sq_miles: float = Field(..., description="")
    council_district: int = Field(..., description="")
    emergency_contacts: list[str] = Field(default_factory=list, description="")
    active_incident_count: int = Field(..., description="")
    active_sensor_count: int = Field(..., description="")
    active_asset_count: int = Field(..., description="")
    air_quality_index: float = Field(..., description="")
    noise_level_db: float = Field(..., description="")
    power_load_pct: float = Field(..., description="")
    ai_risk_score: float = Field(..., description="")
    ai_trend_summary: str = Field(..., description="")
    created_at: str = Field(default="", description="Creation timestamp")


class WorkOrderCreate(BaseModel):
    """Schema for creating a workorder."""

    title: str = Field(default=..., description="")
    description: str = Field(default=..., description="")
    work_type: str = Field(default=..., description="preventive/corrective/emergency/inspection/replacement")
    priority: str = Field(default=..., description="critical/high/medium/low")
    asset_id: str = Field(default=..., description="")
    assigned_team: str = Field(default=..., description="")
    scheduled_date: str = Field(default=..., description="")
    estimated_hours: float = Field(default=..., description="")
    actual_hours: float = Field(default=..., description="")
    parts_cost: float = Field(default=..., description="")
    labor_cost: float = Field(default=..., description="")
    total_cost: float = Field(default=..., description="")
    ai_generated: bool = Field(default=..., description="")
    ai_justification: str = Field(default=..., description="")
    completion_notes: str = Field(default=..., description="")
    quality_rating: int = Field(default=..., description="")


class WorkOrderResponse(BaseModel):
    """Schema returned by workorder endpoints."""

    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="")
    description: str = Field(..., description="")
    work_type: str = Field(..., description="preventive/corrective/emergency/inspection/replacement")
    priority: str = Field(..., description="critical/high/medium/low")
    status: str = Field(..., description="created/approved/scheduled/in_progress/on_hold/completed/cancelled")
    asset_id: str = Field(..., description="")
    assigned_team: str = Field(..., description="")
    scheduled_date: str = Field(..., description="")
    estimated_hours: float = Field(..., description="")
    actual_hours: float = Field(..., description="")
    parts_cost: float = Field(..., description="")
    labor_cost: float = Field(..., description="")
    total_cost: float = Field(..., description="")
    ai_generated: bool = Field(..., description="")
    ai_justification: str = Field(..., description="")
    completion_notes: str = Field(..., description="")
    quality_rating: int = Field(..., description="")
    created_at: str = Field(default="", description="Creation timestamp")


class AuditLogCreate(BaseModel):
    """Schema for creating a auditlog."""

    event_type: str = Field(default=..., description="chat/agent_call/tool_invocation/content_filter/embedding/search/file_upload")
    agent_name: str = Field(default=..., description="")
    user_id: str = Field(default=..., description="")
    user_role: str = Field(default=..., description="")
    prompt_text: str = Field(default=..., description="")
    completion_text: str = Field(default=..., description="")
    token_count_prompt: int = Field(default=..., description="")
    token_count_completion: int = Field(default=..., description="")
    latency_ms: int = Field(default=..., description="")
    model_name: str = Field(default=..., description="")
    content_safety_result: str = Field(default=..., description="")
    content_safety_categories: str = Field(default=..., description="")
    pii_detected: bool = Field(default=..., description="")
    session_id: str = Field(default=..., description="")
    correlation_id: str = Field(default=..., description="")
    ip_address: str = Field(default=..., description="")


class AuditLogResponse(BaseModel):
    """Schema returned by auditlog endpoints."""

    id: str = Field(..., description="Unique identifier")
    event_type: str = Field(..., description="chat/agent_call/tool_invocation/content_filter/embedding/search/file_upload")
    agent_name: str = Field(..., description="")
    user_id: str = Field(..., description="")
    user_role: str = Field(..., description="")
    prompt_text: str = Field(..., description="")
    completion_text: str = Field(..., description="")
    token_count_prompt: int = Field(..., description="")
    token_count_completion: int = Field(..., description="")
    latency_ms: int = Field(..., description="")
    model_name: str = Field(..., description="")
    content_safety_result: str = Field(..., description="")
    content_safety_categories: str = Field(..., description="")
    pii_detected: bool = Field(..., description="")
    session_id: str = Field(..., description="")
    correlation_id: str = Field(..., description="")
    ip_address: str = Field(..., description="")
    status: str = Field(..., description="success/filtered/error/rate_limited")
    created_at: str = Field(default="", description="Creation timestamp")

