// Shared TypeScript type definitions

// Domain-specific types — auto-generated from business entities

export interface Incident {
  id: string;
  title: string;
  description: string;
  category: string;
  severity: string;
  status: string;
  latitude: number;
  longitude: number;
  zone_id: string;
  reporter_name: string;
  reporter_phone: string;
  affected_population: number;
  estimated_damage: number;
  ai_confidence: number;
  ai_triage_notes: string;
  photo_url: string;
  audio_transcript: string;
  assigned_units: string[];
  resolution_notes: string;
  response_time_minutes: number;
}

export interface Asset {
  id: string;
  name: string;
  asset_type: string;
  status: string;
  location_address: string;
  latitude: number;
  longitude: number;
  zone_id: string;
  install_date: string;
  expected_lifespan_years: number;
  manufacturer: string;
  model_number: string;
  last_inspection_date: string;
  health_score: number;
  replacement_cost: number;
  maintenance_budget: number;
  sensor_ids: string[];
  ai_failure_prediction: string;
  ai_health_trend: string;
}

export interface Sensor {
  id: string;
  name: string;
  sensor_type: string;
  status: string;
  latitude: number;
  longitude: number;
  zone_id: string;
  asset_id: string;
  vendor: string;
  protocol: string;
  last_reading_value: number;
  last_reading_unit: string;
  last_reading_timestamp: string;
  threshold_min: number;
  threshold_max: number;
  alert_enabled: boolean;
  battery_level: number;
  firmware_version: string;
  calibration_date: string;
}

export interface ServiceRequest {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  citizen_name: string;
  citizen_email: string;
  citizen_phone: string;
  latitude: number;
  longitude: number;
  zone_id: string;
  assigned_team: string;
  estimated_completion_date: string;
  ai_duplicate_score: number;
  ai_category_confidence: number;
  ai_suggested_resolution: string;
  photo_url: string;
  satisfaction_rating: number;
}

export interface TransitRoute {
  id: string;
  name: string;
  route_number: string;
  route_type: string;
  status: string;
  start_location: string;
  end_location: string;
  total_stops: number;
  daily_ridership: number;
  average_delay_minutes: number;
  on_time_percentage: number;
  fare_revenue_daily: number;
  operating_cost_daily: number;
  vehicle_count: number;
  zone_ids: string[];
  ai_demand_forecast: string;
  ai_optimization_notes: string;
  last_disruption_reason: string;
}

export interface Vehicle {
  id: string;
  name: string;
  vehicle_type: string;
  status: string;
  license_plate: string;
  vin_number: string;
  current_latitude: number;
  current_longitude: number;
  assigned_department: string;
  driver_name: string;
  fuel_level_pct: number;
  odometer_miles: number;
  last_maintenance_date: string;
  next_maintenance_due: string;
  maintenance_cost_ytd: number;
  ai_maintenance_prediction: string;
  gps_speed_mph: number;
  engine_health_score: number;
}

export interface Zone {
  id: string;
  name: string;
  zone_code: string;
  zone_type: string;
  status: string;
  population: number;
  area_sq_miles: number;
  council_district: number;
  emergency_contacts: string[];
  active_incident_count: number;
  active_sensor_count: number;
  active_asset_count: number;
  air_quality_index: number;
  noise_level_db: number;
  power_load_pct: number;
  ai_risk_score: number;
  ai_trend_summary: string;
}

export interface WorkOrder {
  id: string;
  title: string;
  description: string;
  work_type: string;
  priority: string;
  status: string;
  asset_id: string;
  assigned_team: string;
  scheduled_date: string;
  estimated_hours: number;
  actual_hours: number;
  parts_cost: number;
  labor_cost: number;
  total_cost: number;
  ai_generated: boolean;
  ai_justification: string;
  completion_notes: string;
  quality_rating: number;
}

export interface AuditLog {
  id: string;
  event_type: string;
  agent_name: string;
  user_id: string;
  user_role: string;
  prompt_text: string;
  completion_text: string;
  token_count_prompt: number;
  token_count_completion: number;
  latency_ms: number;
  model_name: string;
  content_safety_result: string;
  content_safety_categories: string;
  pii_detected: boolean;
  session_id: string;
  correlation_id: string;
  ip_address: string;
  status: string;
}
