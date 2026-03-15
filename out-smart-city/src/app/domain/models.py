"""Domain models — auto-generated from intent specification."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class Incident:
    id: str = ""
    title: str = ""
    description: str = ""
    category: str = ""
    severity: str = ""
    status: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    zone_id: str = ""
    reporter_name: str = ""
    reporter_phone: str = ""
    affected_population: int = 0
    estimated_damage: float = 0.0
    ai_confidence: float = 0.0
    ai_triage_notes: str = ""
    photo_url: str = ""
    audio_transcript: str = ""
    assigned_units: list[str] = field(default_factory=list)
    resolution_notes: str = ""
    response_time_minutes: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Asset:
    id: str = ""
    name: str = ""
    asset_type: str = ""
    status: str = ""
    location_address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    zone_id: str = ""
    install_date: str = ""
    expected_lifespan_years: int = 0
    manufacturer: str = ""
    model_number: str = ""
    last_inspection_date: str = ""
    health_score: float = 0.0
    replacement_cost: float = 0.0
    maintenance_budget: float = 0.0
    sensor_ids: list[str] = field(default_factory=list)
    ai_failure_prediction: str = ""
    ai_health_trend: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Sensor:
    id: str = ""
    name: str = ""
    sensor_type: str = ""
    status: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    zone_id: str = ""
    asset_id: str = ""
    vendor: str = ""
    protocol: str = ""
    last_reading_value: float = 0.0
    last_reading_unit: str = ""
    last_reading_timestamp: str = ""
    threshold_min: float = 0.0
    threshold_max: float = 0.0
    alert_enabled: bool = False
    battery_level: float = 0.0
    firmware_version: str = ""
    calibration_date: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ServiceRequest:
    id: str = ""
    title: str = ""
    description: str = ""
    category: str = ""
    priority: str = ""
    status: str = ""
    citizen_name: str = ""
    citizen_email: str = ""
    citizen_phone: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    zone_id: str = ""
    assigned_team: str = ""
    estimated_completion_date: str = ""
    ai_duplicate_score: float = 0.0
    ai_category_confidence: float = 0.0
    ai_suggested_resolution: str = ""
    photo_url: str = ""
    satisfaction_rating: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TransitRoute:
    id: str = ""
    name: str = ""
    route_number: str = ""
    route_type: str = ""
    status: str = ""
    start_location: str = ""
    end_location: str = ""
    total_stops: int = 0
    daily_ridership: int = 0
    average_delay_minutes: float = 0.0
    on_time_percentage: float = 0.0
    fare_revenue_daily: float = 0.0
    operating_cost_daily: float = 0.0
    vehicle_count: int = 0
    zone_ids: list[str] = field(default_factory=list)
    ai_demand_forecast: str = ""
    ai_optimization_notes: str = ""
    last_disruption_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Vehicle:
    id: str = ""
    name: str = ""
    vehicle_type: str = ""
    status: str = ""
    license_plate: str = ""
    vin_number: str = ""
    current_latitude: float = 0.0
    current_longitude: float = 0.0
    assigned_department: str = ""
    driver_name: str = ""
    fuel_level_pct: float = 0.0
    odometer_miles: int = 0
    last_maintenance_date: str = ""
    next_maintenance_due: str = ""
    maintenance_cost_ytd: float = 0.0
    ai_maintenance_prediction: str = ""
    gps_speed_mph: float = 0.0
    engine_health_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Zone:
    id: str = ""
    name: str = ""
    zone_code: str = ""
    zone_type: str = ""
    status: str = ""
    population: int = 0
    area_sq_miles: float = 0.0
    council_district: int = 0
    emergency_contacts: list[str] = field(default_factory=list)
    active_incident_count: int = 0
    active_sensor_count: int = 0
    active_asset_count: int = 0
    air_quality_index: float = 0.0
    noise_level_db: float = 0.0
    power_load_pct: float = 0.0
    ai_risk_score: float = 0.0
    ai_trend_summary: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class WorkOrder:
    id: str = ""
    title: str = ""
    description: str = ""
    work_type: str = ""
    priority: str = ""
    status: str = ""
    asset_id: str = ""
    assigned_team: str = ""
    scheduled_date: str = ""
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    parts_cost: float = 0.0
    labor_cost: float = 0.0
    total_cost: float = 0.0
    ai_generated: bool = False
    ai_justification: str = ""
    completion_notes: str = ""
    quality_rating: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AuditLog:
    id: str = ""
    event_type: str = ""
    agent_name: str = ""
    user_id: str = ""
    user_role: str = ""
    prompt_text: str = ""
    completion_text: str = ""
    token_count_prompt: int = 0
    token_count_completion: int = 0
    latency_ms: int = 0
    model_name: str = ""
    content_safety_result: str = ""
    content_safety_categories: str = ""
    pii_detected: bool = False
    session_id: str = ""
    correlation_id: str = ""
    ip_address: str = ""
    status: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

