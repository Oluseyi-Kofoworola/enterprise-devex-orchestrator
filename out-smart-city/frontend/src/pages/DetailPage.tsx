import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge';

const tabConfig: Record<string, any> = {
  'incidents': {
    label: 'Incidents',
    entityName: 'Incident',
    columns: ['id', 'title', 'description', 'category', 'severity', 'status', 'latitude', 'longitude', 'zone_id', 'reporter_name', 'reporter_phone', 'affected_population', 'estimated_damage', 'ai_confidence', 'ai_triage_notes', 'photo_url', 'audio_transcript', 'assigned_units', 'resolution_notes', 'response_time_minutes'],
    headers: ['Id', 'Title', 'Description', 'Category', 'Severity', 'Status', 'Latitude', 'Longitude', 'Zone Id', 'Reporter Name', 'Reporter Phone', 'Affected Population', 'Estimated Damage', 'Ai Confidence', 'Ai Triage Notes', 'Photo Url', 'Audio Transcript', 'Assigned Units', 'Resolution Notes', 'Response Time Minutes'],
    hasStatus: true,
    actions: ['triage', 'dispatch', 'escalate', 'resolve', 'correlate'],
  },
  'assets': {
    label: 'Assets',
    entityName: 'Asset',
    columns: ['id', 'name', 'asset_type', 'status', 'location_address', 'latitude', 'longitude', 'zone_id', 'install_date', 'expected_lifespan_years', 'manufacturer', 'model_number', 'last_inspection_date', 'health_score', 'replacement_cost', 'maintenance_budget', 'sensor_ids', 'ai_failure_prediction', 'ai_health_trend'],
    headers: ['Id', 'Name', 'Asset Type', 'Status', 'Location Address', 'Latitude', 'Longitude', 'Zone Id', 'Install Date', 'Expected Lifespan Years', 'Manufacturer', 'Model Number', 'Last Inspection Date', 'Health Score', 'Replacement Cost', 'Maintenance Budget', 'Sensor Ids', 'Ai Failure Prediction', 'Ai Health Trend'],
    hasStatus: true,
    actions: ['predict', 'inspect', 'schedule_maintenance', 'decommission'],
  },
  'sensors': {
    label: 'Sensors',
    entityName: 'Sensor',
    columns: ['id', 'name', 'sensor_type', 'status', 'latitude', 'longitude', 'zone_id', 'asset_id', 'vendor', 'protocol', 'last_reading_value', 'last_reading_unit', 'last_reading_timestamp', 'threshold_min', 'threshold_max', 'alert_enabled', 'battery_level', 'firmware_version', 'calibration_date'],
    headers: ['Id', 'Name', 'Sensor Type', 'Status', 'Latitude', 'Longitude', 'Zone Id', 'Asset Id', 'Vendor', 'Protocol', 'Last Reading Value', 'Last Reading Unit', 'Last Reading Timestamp', 'Threshold Min', 'Threshold Max', 'Alert Enabled', 'Battery Level', 'Firmware Version', 'Calibration Date'],
    hasStatus: true,
    actions: ['calibrate', 'acknowledge_alert', 'disable'],
  },
  'service_requests': {
    label: 'ServiceRequests',
    entityName: 'ServiceRequest',
    columns: ['id', 'title', 'description', 'category', 'priority', 'status', 'citizen_name', 'citizen_email', 'citizen_phone', 'latitude', 'longitude', 'zone_id', 'assigned_team', 'estimated_completion_date', 'ai_duplicate_score', 'ai_category_confidence', 'ai_suggested_resolution', 'photo_url', 'satisfaction_rating'],
    headers: ['Id', 'Title', 'Description', 'Category', 'Priority', 'Status', 'Citizen Name', 'Citizen Email', 'Citizen Phone', 'Latitude', 'Longitude', 'Zone Id', 'Assigned Team', 'Estimated Completion Date', 'Ai Duplicate Score', 'Ai Category Confidence', 'Ai Suggested Resolution', 'Photo Url', 'Satisfaction Rating'],
    hasStatus: true,
    actions: ['acknowledge', 'assign', 'complete', 'reject', 'check_duplicate'],
  },
  'transit_routes': {
    label: 'TransitRoutes',
    entityName: 'TransitRoute',
    columns: ['id', 'name', 'route_number', 'route_type', 'status', 'start_location', 'end_location', 'total_stops', 'daily_ridership', 'average_delay_minutes', 'on_time_percentage', 'fare_revenue_daily', 'operating_cost_daily', 'vehicle_count', 'zone_ids', 'ai_demand_forecast', 'ai_optimization_notes', 'last_disruption_reason'],
    headers: ['Id', 'Name', 'Route Number', 'Route Type', 'Status', 'Start Location', 'End Location', 'Total Stops', 'Daily Ridership', 'Average Delay Minutes', 'On Time Percentage', 'Fare Revenue Daily', 'Operating Cost Daily', 'Vehicle Count', 'Zone Ids', 'Ai Demand Forecast', 'Ai Optimization Notes', 'Last Disruption Reason'],
    hasStatus: true,
    actions: ['optimize', 'reroute', 'suspend', 'restore'],
  },
  'vehicles': {
    label: 'Vehicles',
    entityName: 'Vehicle',
    columns: ['id', 'name', 'vehicle_type', 'status', 'license_plate', 'vin_number', 'current_latitude', 'current_longitude', 'assigned_department', 'driver_name', 'fuel_level_pct', 'odometer_miles', 'last_maintenance_date', 'next_maintenance_due', 'maintenance_cost_ytd', 'ai_maintenance_prediction', 'gps_speed_mph', 'engine_health_score'],
    headers: ['Id', 'Name', 'Vehicle Type', 'Status', 'License Plate', 'Vin Number', 'Current Latitude', 'Current Longitude', 'Assigned Department', 'Driver Name', 'Fuel Level Pct', 'Odometer Miles', 'Last Maintenance Date', 'Next Maintenance Due', 'Maintenance Cost Ytd', 'Ai Maintenance Prediction', 'Gps Speed Mph', 'Engine Health Score'],
    hasStatus: true,
    actions: ['deploy', 'recall', 'refuel', 'schedule_maintenance'],
  },
  'zones': {
    label: 'Zones',
    entityName: 'Zone',
    columns: ['id', 'name', 'zone_code', 'zone_type', 'status', 'population', 'area_sq_miles', 'council_district', 'emergency_contacts', 'active_incident_count', 'active_sensor_count', 'active_asset_count', 'air_quality_index', 'noise_level_db', 'power_load_pct', 'ai_risk_score', 'ai_trend_summary'],
    headers: ['Id', 'Name', 'Zone Code', 'Zone Type', 'Status', 'Population', 'Area Sq Miles', 'Council District', 'Emergency Contacts', 'Active Incident Count', 'Active Sensor Count', 'Active Asset Count', 'Air Quality Index', 'Noise Level Db', 'Power Load Pct', 'Ai Risk Score', 'Ai Trend Summary'],
    hasStatus: true,
    actions: ['alert', 'evacuate', 'clear'],
  },
  'work_orders': {
    label: 'WorkOrders',
    entityName: 'WorkOrder',
    columns: ['id', 'title', 'description', 'work_type', 'priority', 'status', 'asset_id', 'assigned_team', 'scheduled_date', 'estimated_hours', 'actual_hours', 'parts_cost', 'labor_cost', 'total_cost', 'ai_generated', 'ai_justification', 'completion_notes', 'quality_rating'],
    headers: ['Id', 'Title', 'Description', 'Work Type', 'Priority', 'Status', 'Asset Id', 'Assigned Team', 'Scheduled Date', 'Estimated Hours', 'Actual Hours', 'Parts Cost', 'Labor Cost', 'Total Cost', 'Ai Generated', 'Ai Justification', 'Completion Notes', 'Quality Rating'],
    hasStatus: true,
    actions: ['approve', 'schedule', 'start', 'complete', 'cancel'],
  },
  'audit_logs': {
    label: 'AuditLogs',
    entityName: 'AuditLog',
    columns: ['id', 'event_type', 'agent_name', 'user_id', 'user_role', 'prompt_text', 'completion_text', 'token_count_prompt', 'token_count_completion', 'latency_ms', 'model_name', 'content_safety_result', 'content_safety_categories', 'pii_detected', 'session_id', 'correlation_id', 'ip_address', 'status'],
    headers: ['Id', 'Event Type', 'Agent Name', 'User Id', 'User Role', 'Prompt Text', 'Completion Text', 'Token Count Prompt', 'Token Count Completion', 'Latency Ms', 'Model Name', 'Content Safety Result', 'Content Safety Categories', 'Pii Detected', 'Session Id', 'Correlation Id', 'Ip Address', 'Status'],
    hasStatus: true,
    actions: [],
  },
};
const tabKeys = Object.keys(tabConfig);

const API_BASE = '/api/v1';

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [item, setItem] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const entityType = searchParams.get('type') || tabKeys[0];
  const config = tabConfig[entityType];

  useEffect(() => {
    if (id && entityType) {
      fetch(`${API_BASE}/${entityType}/${id}`)
        .then(r => r.json())
        .then(setItem)
        .finally(() => setLoading(false));
    }
  }, [id, entityType]);

  const handleAction = async (action: string) => {
    await fetch(`${API_BASE}/${entityType}/${id}/${action}`, { method: 'POST' });
    const updated = await fetch(`${API_BASE}/${entityType}/${id}`).then(r => r.json());
    setItem(updated);
  };

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;
  if (!item) return <p className="text-center py-12 text-red-500">Not found</p>;

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/')} className="text-blue-600 hover:underline text-sm">
        &larr; Back to Dashboard
      </button>
      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold">{config?.entityName || 'Item'} Detail</h1>
          {item.status && <StatusBadge status={item.status} />}
        </div>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          {config?.columns?.filter((c: string) => c !== 'status').map((col: string) => (
            <div key={col}>
              <dt className="text-gray-500 capitalize">{col.replace(/_/g, ' ')}</dt>
              <dd className="font-medium mt-1">
                {col === 'id' ? item[col] : String(item[col] ?? '\u2014')}
              </dd>
            </div>
          ))}
        </dl>
        {config?.hasStatus && config?.actions?.length > 0 && (
          <div className="mt-6 flex gap-3">
            {config.actions.map((action: string) => (
              <button
                key={action}
                onClick={() => handleAction(action)}
                className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 capitalize"
              >
                {action}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
