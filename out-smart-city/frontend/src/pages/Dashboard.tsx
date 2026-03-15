import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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

export default function Dashboard() {
  const [allData, setAllData] = useState<Record<string, any[]>>({});
  const [activeTab, setActiveTab] = useState(tabKeys[0]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [search, setSearch] = useState('');

  const fetchAll = () => {
    setLoading(true);
    Promise.all(
      tabKeys.map(key =>
        fetch(`${API_BASE}/${key}`).then(r => r.json()).catch(() => [])
      )
    ).then(results => {
      const data: Record<string, any[]> = {};
      tabKeys.forEach((key, i) => { data[key] = results[i]; });
      setAllData(data);
    }).finally(() => setLoading(false));
  };

  useEffect(() => { fetchAll(); const t = setInterval(fetchAll, 30000); return () => clearInterval(t); }, []);

  const config = tabConfig[activeTab];
  const currentData = allData[activeTab] || [];
  const filteredData = search
    ? currentData.filter((item: any) =>
        Object.values(item).some(v =>
          String(v).toLowerCase().includes(search.toLowerCase())
        )
      )
    : currentData;

  const handleCreate = async () => {
    try {
      await fetch(`${API_BASE}/${activeTab}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      setShowCreate(false);
      setFormData({});
      fetchAll();
    } catch { /* ignore */ }
  };

  const handleAction = async (action: string, id: string) => {
    await fetch(`${API_BASE}/${activeTab}/${id}/${action}`, { method: 'POST' });
    fetchAll();
  };

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;

  const createFields = config.columns.filter((c: string) => c !== 'id' && c !== 'status');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{config.label}</h1>
        <div className="flex gap-3">
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search..."
            className="border rounded-lg px-3 py-2 text-sm w-64"
          />
          <button
            onClick={() => setShowCreate(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700"
          >
            + Create {config.entityName}
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {tabKeys.map(key => (
          <div
            key={key}
            onClick={() => setActiveTab(key)}
            className={`bg-white rounded-xl shadow p-4 cursor-pointer border-2 transition ${
              activeTab === key ? 'border-blue-500' : 'border-transparent hover:border-gray-200'
            }`}
          >
            <p className="text-sm text-gray-500">{tabConfig[key].label}</p>
            <p className="text-2xl font-bold text-blue-700">{(allData[key] || []).length}</p>
          </div>
        ))}
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b">
        {tabKeys.map(key => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
              activeTab === key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tabConfig[key].label} ({(allData[key] || []).length})
          </button>
        ))}
      </div>

      {/* Data Table */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {config.headers.map((h: string) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {h}
                </th>
              ))}
              {config.hasStatus && config.actions.length > 0 && (
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filteredData.map((item: any) => (
              <tr key={item.id} className="hover:bg-gray-50">
                {config.columns.map((col: string) => (
                  <td key={col} className="px-4 py-3 text-sm">
                    {col === 'id' ? (
                      <Link to={`/detail/${item.id}?type=${activeTab}`} className="text-blue-600 hover:underline font-mono">
                        {item.id?.slice(0, 8)}
                      </Link>
                    ) : col === 'status' ? (
                      <StatusBadge status={item[col] || ''} />
                    ) : (
                      String(item[col] ?? '')
                    )}
                  </td>
                ))}
                {config.hasStatus && config.actions.length > 0 && (
                  <td className="px-4 py-3 text-sm">
                    <div className="flex gap-1">
                      {config.actions.map((action: string) => (
                        <button
                          key={action}
                          onClick={() => handleAction(action, item.id)}
                          className="px-2 py-1 text-xs rounded bg-gray-100 hover:bg-gray-200 capitalize"
                        >
                          {action}
                        </button>
                      ))}
                    </div>
                  </td>
                )}
              </tr>
            ))}
            {filteredData.length === 0 && (
              <tr>
                <td colSpan={config.columns.length + (config.hasStatus && config.actions.length > 0 ? 1 : 0)}
                    className="px-4 py-8 text-center text-gray-400">
                  No {config.label.toLowerCase()} found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">Create {config.entityName}</h2>
            <div className="space-y-3">
              {createFields.map((field: string) => (
                <div key={field}>
                  <label className="block text-sm font-medium text-gray-700 mb-1 capitalize">
                    {field.replace(/_/g, ' ')}
                  </label>
                  <input
                    value={formData[field] || ''}
                    onChange={e => setFormData(prev => ({ ...prev, [field]: e.target.value }))}
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                    placeholder={`Enter ${field.replace(/_/g, ' ')}`}
                  />
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => { setShowCreate(false); setFormData({}); }}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
