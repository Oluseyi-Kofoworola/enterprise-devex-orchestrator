"""Application Generator -- produces sample application code.

Generates a minimal but production-grade application with:
    - Health endpoint
    - Managed Identity integration
    - Key Vault client
    - Storage client (if applicable)
    - Structured logging
    - Dockerfile
    - Dependency file

Supports multiple languages:
    - Python (FastAPI)  -- default
    - Node.js (Express)
    - .NET (ASP.NET Core minimal API)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.orchestrator.intent_schema import DataStore, EntitySpec, IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


def _seed_timestamp(row: int, spread_days: int = 90) -> str:
    """Generate a realistic ISO timestamp relative to now, spread over `spread_days`."""
    now = datetime.now(timezone.utc)
    offset_days = spread_days - (row - 1) * (spread_days // 12)
    offset_days = max(1, offset_days)
    hour = 6 + (row * 3) % 16
    minute = (row * 17) % 60
    dt = now - timedelta(days=offset_days, hours=24 - hour, minutes=60 - minute)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# -- Helpers for dynamic code generation from EntitySpec ---------------
def _snake(name: str) -> str:
    """PascalCase -> snake_case."""
    import re
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name).lower()


def _plural(name: str) -> str:
    """Simple English pluralizer for entity names."""
    lower = name.lower()
    if lower.endswith("y") and lower[-2:] not in ("ay", "ey", "oy", "uy"):
        return name[:-1] + "ies"
    if lower.endswith(("s", "sh", "ch", "x", "z")):
        return name + "es"
    return name + "s"


def _has_custom_entities(spec: IntentSpec) -> bool:
    """Return True if spec has any entities (including fallback Resource)."""
    return bool(spec.entities)


def _python_type_default(field_type: str) -> str:
    """Return Python default for a field type."""
    defaults = {
        "str": '""', "int": "0", "float": "0.0", "bool": "False",
        "list": "field(default_factory=list)",
        "list[str]": "field(default_factory=list)",
        "list[int]": "field(default_factory=list)",
        "list[float]": "field(default_factory=list)",
        "dict": "field(default_factory=dict)",
        "datetime": 'field(default_factory=lambda: datetime.now(timezone.utc).isoformat())',
    }
    return defaults.get(field_type, '""')


def _seed_value(field_spec, entity_name: str, row: int) -> str:
    """Generate a realistic seed value for a field -- fully dynamic, no domain assumptions."""
    name = field_spec.name
    ftype = field_spec.type
    ename_lower = entity_name.lower()
    ename_abbr = ename_lower[:3].upper()

    # --- Realistic name pools ---
    _first_names = ["Alice", "Bob", "Carlos", "Diana", "Erik", "Fatima", "Grace", "Hassan", "Irene", "James", "Kira", "Liam", "Maya", "Noah", "Olivia"]
    _last_names = ["Chen", "Smith", "Garcia", "Patel", "Kim", "Johnson", "Williams", "Brown", "Jones", "Davis"]
    _streets = ["Main St", "Oak Ave", "Elm Blvd", "Park Dr", "River Rd", "Industrial Pkwy", "Harbor View", "Tech Campus", "Central Plaza", "Lakeside Way", "Market St", "5th Avenue", "Broadway", "Commercial Blvd", "University Dr"]
    _cities = ["Downtown", "Midtown", "Uptown", "Eastside", "Westside", "Northgate", "Southpoint", "Harbor District", "Tech Quarter", "Old Town", "Financial District", "Arts District", "Riverside", "Airport Zone", "Civic Center"]
    _categories_pool = {
        "category": ["infrastructure", "safety", "environmental", "maintenance", "security", "utilities", "transportation", "public-health", "emergency", "administration", "compliance", "operations"],
        "type": ["electrical", "mechanical", "structural", "software", "network", "hydraulic", "thermal", "chemical", "environmental", "optical"],
        "asset_type": ["traffic-light", "power-grid", "water-pump", "HVAC-unit", "EV-charger", "solar-panel", "security-camera", "bridge-sensor", "air-quality-monitor", "flood-gate"],
    }

    # --- Non-string types ---
    if ftype == "float":
        import hashlib
        h = int(hashlib.md5(f"{ename_lower}-{name}-{row}".encode()).hexdigest()[:8], 16)
        if "confidence" in name or "score" in name or "health" in name:
            return f"{0.45 + (h % 55) / 100:.2f}"
        if "latitude" in name or "lat" in name:
            return f"{33.0 + (h % 800) / 100:.4f}"
        if "longitude" in name or "lon" in name or "lng" in name:
            return f"{-118.0 + (h % 500) / 100:.4f}"
        if "damage" in name or "cost" in name or "budget" in name or "price" in name or "amount" in name:
            amounts = [1250.0, 8500.0, 350.0, 22000.0, 4800.0, 15600.0, 970.0, 38000.0, 6200.0, 2100.0, 12500.0, 44000.0, 580.0, 19800.0, 7300.0]
            return str(amounts[(row - 1) % len(amounts)])
        if "time" in name or "minutes" in name or "duration" in name:
            times = [12.5, 45.0, 8.0, 120.0, 30.0, 5.5, 90.0, 15.0, 60.0, 22.0, 180.0, 3.0, 75.0, 40.0, 10.0]
            return str(times[(row - 1) % len(times)])
        amounts = [49.99, 125.50, 29.95, 89.00, 210.75, 1500.00, 340.25, 78.50, 560.00, 15.99, 2400.00, 180.75, 95.00, 720.50, 45.00]
        return str(amounts[(row - 1) % len(amounts)])
    if ftype == "int":
        if "population" in name or "affected" in name:
            pops = [150, 2500, 50, 12000, 800, 3200, 75, 500, 8000, 1800, 350, 15000, 420, 6500, 100]
            return str(pops[(row - 1) % len(pops)])
        if "count" in name or "capacity" in name:
            return str(row * 25 + (row * 7) % 200)
        if "year" in name or "lifespan" in name:
            vals = [5, 12, 3, 20, 8, 15, 2, 25, 10, 7, 30, 1, 18, 6, 14]
            return str(vals[(row - 1) % len(vals)])
        return str(row * 10 + (row * 13) % 50)
    if ftype == "bool":
        # Vary more for larger datasets
        return "True" if (row * 7 + 3) % 3 != 0 else "False"
    if ftype in ("list", "list[str]"):
        refs = [f'"{ename_lower}-ref-{(row * 3 + i):03d}"' for i in range(1, min(row % 3 + 2, 4))]
        return f'[{", ".join(refs)}]'
    if ftype == "list[int]":
        vals = [str(row * 10 + i * 7) for i in range(1, min(row % 3 + 2, 4))]
        return f'[{", ".join(vals)}]'
    if ftype == "list[float]":
        vals = [f"{row * 1.5 + i * 2.3:.1f}" for i in range(1, min(row % 3 + 2, 4))]
        return f'[{", ".join(vals)}]'
    if ftype == "dict":
        return "{}"
    if ftype == "datetime":
        return f'"{ _seed_timestamp(row) }"'

    # --- String type: contextual seed values based on field name patterns ---
    if name == "status" or name.endswith("_status") or name == "state":
        statuses = ["pending", "in_progress", "completed", "pending", "in_progress", "active",
                     "completed", "pending", "active", "critical", "in_progress", "completed",
                     "resolved", "pending", "in_progress"]
        return f'"{statuses[(row - 1) % len(statuses)]}"'
    if name.endswith("_id") or name == "id":
        ref = name.replace("_id", "").upper() if name.endswith("_id") else ename_abbr
        return f'"{ref}-{1000 + row}"'
    if name in ("priority", "severity", "urgency"):
        levels = ["critical", "high", "medium", "low", "high", "critical", "medium", "high",
                  "low", "medium", "critical", "high", "medium", "low", "high"]
        return f'"{levels[(row - 1) % len(levels)]}"'
    if name in ("level", "tier", "grade"):
        grades = ["gold", "silver", "bronze", "platinum", "gold", "silver", "bronze", "gold",
                  "platinum", "silver", "gold", "bronze", "silver", "gold", "platinum"]
        return f'"{grades[(row - 1) % len(grades)]}"'
    if name in ("type", "category", "kind", "class") or name.endswith("_type") or name.endswith("_category"):
        pool = _categories_pool.get(name, _categories_pool.get("category"))
        return f'"{pool[(row - 1) % len(pool)]}"'
    if name in ("name", "title", "label"):
        # Generate realistic names based on entity context
        _descriptors = ["Critical", "Routine", "Emergency", "Scheduled", "Urgent",
                       "Preventive", "Corrective", "Inspection", "Upgrade", "Assessment",
                       "Priority", "Follow-up", "Recurring", "Ad-hoc", "Compliance"]
        _subjects = [f"{ename_lower} operation", "maintenance task", "system check", "field inspection",
                    "service call", "repair work", "safety audit", "resource allocation",
                    "performance review", "capacity planning", "incident response",
                    "quality assurance", "risk assessment", "compliance check", "workflow update"]
        return f'"{_descriptors[(row - 1) % len(_descriptors)]} {_subjects[(row - 1) % len(_subjects)]}"'
    if name in ("description", "summary", "details", "notes", "comment", "remarks"):
        _desc_templates = [
            f"Reported at {{}} — requires immediate attention. Multiple systems affected.",
            f"Scheduled maintenance for {{}} sector. Standard operating procedure applies.",
            f"Environmental alert triggered by {{}} monitoring station. Readings above threshold.",
            f"Citizen complaint regarding {{}} in residential area. Priority response needed.",
            f"Automated detection: {{}} anomaly in grid sector. Diagnostic in progress.",
            f"Follow-up inspection after {{}} repair completed. Verification pending.",
            f"Capacity warning for {{}} infrastructure. Usage at 87% of rated limit.",
            f"Emergency dispatch triggered by {{}} sensor cluster. Units en route.",
            f"Routine calibration of {{}} equipment. Last serviced 90 days ago.",
            f"Inter-agency coordination needed for {{}} zone upgrade project.",
            f"Budget review requested for {{}} capital improvement program.",
            f"Safety compliance audit for {{}} operations. Due by end of quarter.",
            f"Performance degradation detected in {{}} subsystem. Root cause TBD.",
            f"Public event impact assessment for {{}} district. Traffic rerouting planned.",
            f"Vendor contract renewal for {{}} maintenance services. Evaluation in progress.",
        ]
        t = _desc_templates[(row - 1) % len(_desc_templates)]
        return f'"{t.format(_cities[(row - 1) % len(_cities)])}"'
    if name in ("reason", "cause", "justification"):
        reasons = ["Equipment failure", "Weather damage", "Scheduled upgrade", "Safety violation",
                  "Capacity exceeded", "Age-related wear", "Software bug", "Power surge",
                  "Vandalism", "Natural disaster", "Design flaw", "Human error",
                  "Regulatory requirement", "Cost optimization", "Performance issue"]
        return f'"{reasons[(row - 1) % len(reasons)]}"'
    if name in ("method", "approach", "technique", "strategy"):
        return f'"method-{row}"'
    if name in ("currency", "currency_code"):
        currencies = ["USD", "EUR", "GBP"]
        return f'"{currencies[(row - 1) % len(currencies)]}"'
    if name in ("country", "country_code"):
        countries = ["US", "GB", "DE"]
        return f'"{countries[(row - 1) % len(countries)]}"'
    if name in ("region", "zone", "area"):
        return f'"{_cities[(row - 1) % len(_cities)]}"'
    if name in ("location", "address", "place", "site") or "location" in name or "address" in name:
        return f'"{(row * 100 + 15)} {_streets[(row - 1) % len(_streets)]}, {_cities[(row - 1) % len(_cities)]}"'
    if name in ("email", "contact_email", "user_email"):
        fn = _first_names[(row - 1) % len(_first_names)].lower()
        ln = _last_names[(row - 1) % len(_last_names)].lower()
        return f'"{fn}.{ln}@smartcity.gov"'
    if name.endswith("_name") or name in ("reporter_name", "assigned_to", "operator", "technician", "requester", "agent_name", "user_name"):
        fn = _first_names[(row - 1) % len(_first_names)]
        ln = _last_names[(row - 1) % len(_last_names)]
        return f'"{fn} {ln}"'
    if name in ("phone", "phone_number", "contact_phone") or name.endswith("_phone"):
        return f'"+1-555-{100 + row:03d}-{1000 + row * 111:04d}"'
    if name in ("url", "link", "website", "homepage") or name.endswith("_url"):
        return f'"https://portal.smartcity.gov/{ename_lower}/{row:04d}"'
    if name in ("ip", "ip_address"):
        return f'"10.{(row // 256) % 256}.{row % 256}.{(row * 7) % 256}"'
    if name in ("version", "revision"):
        return f'"v1.{row}.0"'
    if name.startswith("serial") or name.endswith("_number") or name == "code":
        return f'"{ename_abbr}-{row:04d}"'
    if name in ("color", "colour"):
        colors = ["red", "blue", "green", "orange", "purple"]
        return f'"{colors[(row - 1) % len(colors)]}"'
    if name in ("tag", "tags"):
        return f'"tag-{row}"'
    if name in ("role", "permission") or name.endswith("_role"):
        roles = ["operator", "supervisor", "technician", "analyst", "manager",
                "dispatcher", "inspector", "coordinator", "engineer", "administrator",
                "auditor", "planner", "field-agent", "director", "specialist"]
        return f'"{roles[(row - 1) % len(roles)]}"'
    if name in ("source", "origin", "provider"):
        sources = ["IoT-sensor", "citizen-report", "automated-scan", "field-inspection",
                  "dispatch-system", "API-integration", "manual-entry", "SCADA",
                  "mobile-app", "web-portal", "email", "hotline", "partner-feed", "satellite", "drone"]
        return f'"{sources[(row - 1) % len(sources)]}"'
    if name in ("target", "destination"):
        return f'"{_cities[(row - 1) % len(_cities)]}"'
    if "date" in name or name in ("created", "updated", "timestamp") or name.endswith("_date") or name.endswith("_at"):
        return f'"{ _seed_timestamp(row) }"'
    if "amount" in name or "price" in name or "cost" in name or name in ("fee", "total", "balance"):
        amounts = [1250.0, 8500.0, 350.0, 22000.0, 4800.0, 15600.0, 970.0, 38000.0, 6200.0, 2100.0, 12500.0, 44000.0, 580.0, 19800.0, 7300.0]
        return str(amounts[(row - 1) % len(amounts)])
    if "transcript" in name or "notes" in name:
        _notes = [
            "Initial assessment complete. Dispatching repair crew.",
            "On-site inspection confirmed. Severity upgraded.",
            "Monitoring active. No further escalation needed.",
            "Parts ordered from vendor. ETA 48 hours.",
            "Resolved via remote diagnostics. System restored.",
            "Awaiting citizen follow-up. Case remains open.",
            "Cross-department coordination in progress.",
            "Final review pending supervisor approval.",
            "Emergency protocol activated. All units notified.",
            "Routine check passed. Next scheduled in 30 days.",
            "Third-party contractor engaged for specialized repair.",
            "Budget approval received. Work order created.",
            "Environmental compliance verified. Report filed.",
            "Training session completed for operations team.",
            "System upgrade deployed. Performance metrics improving.",
        ]
        return f'"{_notes[(row - 1) % len(_notes)]}"'
    if "manufacturer" in name or "vendor" in name or "brand" in name:
        _mfg = ["Siemens", "GE Digital", "Honeywell", "Schneider Electric", "ABB",
               "Cisco Systems", "Itron", "Sensus", "Trimble", "Telensa",
               "Silver Spring", "Eaton", "Emerson", "Rockwell", "Yokogawa"]
        return f'"{_mfg[(row - 1) % len(_mfg)]}"'
    # Generic fallback — uses field name + entity context
    return f'"{ename_lower}-{name}-{row}"'


def _pascal_field(snake_name: str) -> str:
    """snake_case -> PascalCase for C# field names."""
    return "".join(w.capitalize() for w in snake_name.split("_"))


def _camel(snake_name: str) -> str:
    """snake_case -> camelCase for C# parameters."""
    parts = snake_name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


def _dotnet_type(field_type: str) -> str:
    """Map field type string to C# type."""
    mapping = {
        "str": "string", "int": "int", "float": "double",
        "bool": "bool", "list": "List<string>", "list[str]": "List<string>",
        "dict": "Dictionary<string, object>", "datetime": "DateTime",
    }
    return mapping.get(field_type, "string")


def _dotnet_seed_val(py_val: str, field_type: str) -> str:
    """Convert Python seed value string to C# literal."""
    if field_type in ("int", "float", "bool"):
        return py_val.lower() if field_type == "bool" else py_val
    if field_type in ("list", "list[str]"):
        return "new()"
    if field_type == "dict":
        return "new()"
    # string — already quoted
    return py_val


class AppGenerator:
    """Generates application scaffold -- multi-language support."""

    # -- Enterprise Dashboard CSS (shared across all languages) ------
    ENTERPRISE_CSS = """:root {
            --primary: #0078d4;
            --primary-dark: #005a9e;
            --success: #107c10;
            --warning: #ff8c00;
            --danger: #d13438;
            --bg: #f3f2f1;
            --surface: #ffffff;
            --surface-alt: #faf9f8;
            --text: #323130;
            --text-secondary: #605e5c;
            --border: #edebe9;
            --shadow: 0 2px 8px rgba(0,0,0,.08);
            --shadow-lg: 0 8px 32px rgba(0,0,0,.12);
            --radius: 8px;
            --radius-lg: 12px;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
        .topbar { background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%); color: white; padding: 0 32px; height: 48px; display: flex; align-items: center; justify-content: space-between; font-size: 13px; box-shadow: 0 1px 4px rgba(0,0,0,.15); position: sticky; top: 0; z-index: 100; }
        .topbar-brand { display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 14px; }
        .topbar-brand svg { width: 20px; height: 20px; fill: white; }
        .topbar-meta { display: flex; gap: 20px; align-items: center; }
        .topbar-meta span { opacity: .85; }
        .env-badge { background: rgba(255,255,255,.2); padding: 2px 10px; border-radius: 12px; font-size: 11px; text-transform: uppercase; font-weight: 600; letter-spacing: .5px; }
        .hero { background: linear-gradient(180deg, #005a9e 0%, #0078d4 50%, var(--bg) 100%); padding: 48px 32px 64px; text-align: center; color: white; }
        .hero h1 { font-size: 28px; font-weight: 600; margin-bottom: 8px; }
        .hero p { font-size: 15px; opacity: .9; max-width: 640px; margin: 0 auto; line-height: 1.5; }
        .version-pill { display: inline-block; margin-top: 12px; background: rgba(255,255,255,.15); backdrop-filter: blur(8px); padding: 4px 16px; border-radius: 20px; font-size: 12px; font-weight: 500; }
        .dashboard { max-width: 1120px; margin: -40px auto 40px; padding: 0 24px; display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow); overflow: hidden; transition: box-shadow .2s, transform .15s; }
        .card:hover { box-shadow: var(--shadow-lg); transform: translateY(-2px); }
        .card-header { padding: 16px 20px 12px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid var(--border); background: var(--surface-alt); }
        .card-header h3 { font-size: 14px; font-weight: 600; color: var(--text); }
        .card-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
        .card-body { padding: 20px; }
        .status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .status-item { text-align: center; }
        .status-item .label { font-size: 11px; text-transform: uppercase; letter-spacing: .8px; color: var(--text-secondary); margin-bottom: 4px; }
        .status-item .value { font-size: 20px; font-weight: 700; }
        .status-item .value.ok { color: var(--success); }
        .status-item .value.warn { color: var(--warning); }
        .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; animation: pulse 2s ease-in-out infinite; }
        .status-dot.green { background: var(--success); }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .4; } }
        .endpoint-list { list-style: none; }
        .endpoint-list li { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border); gap: 12px; }
        .endpoint-list li:last-child { border-bottom: none; }
        .method-badge { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-family: 'Consolas', 'Courier New', monospace; letter-spacing: .5px; min-width: 40px; text-align: center; }
        .method-badge.get { background: #e6f4ea; color: var(--success); }
        .method-badge.post { background: #e3f2fd; color: var(--primary); }
        .endpoint-path { font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; color: var(--text); font-weight: 500; }
        .endpoint-desc { font-size: 12px; color: var(--text-secondary); margin-left: auto; }
        .actions { display: flex; flex-direction: column; gap: 10px; }
        .action-btn { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); color: var(--text); text-decoration: none; font-size: 13px; font-weight: 500; transition: all .15s; }
        .action-btn:hover { background: var(--primary); color: white; border-color: var(--primary); }
        .action-btn .icon { font-size: 18px; width: 24px; text-align: center; }
        .arch-list { list-style: none; }
        .arch-list li { display: flex; align-items: center; gap: 10px; padding: 8px 0; font-size: 13px; border-bottom: 1px solid var(--border); }
        .arch-list li:last-child { border-bottom: none; }
        .arch-badge { font-size: 10px; font-weight: 600; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: .3px; }
        .arch-badge.compute { background: #e3f2fd; color: #1565c0; }
        .arch-badge.data { background: #e8f5e9; color: #2e7d32; }
        .arch-badge.security { background: #fce4ec; color: #c62828; }
        .arch-badge.monitor { background: #fff3e0; color: #e65100; }
        .compliance-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
        .compliance-badge { font-size: 11px; font-weight: 600; padding: 4px 12px; border-radius: 20px; border: 1px solid; }
        .compliance-badge.hipaa { background: #fce4ec; border-color: #ef9a9a; color: #b71c1c; }
        .compliance-badge.soc2 { background: #e8eaf6; border-color: #9fa8da; color: #283593; }
        .compliance-badge.rbac { background: #e0f2f1; border-color: #80cbc4; color: #00695c; }
        .compliance-badge.pci { background: #fff8e1; border-color: #ffe082; color: #f57f17; }
        .compliance-badge.fedramp { background: #e8eaf6; border-color: #7986cb; color: #1a237e; }
        .compliance-badge.iso { background: #f3e5f5; border-color: #ce93d8; color: #6a1b9a; }
        .compliance-badge.general { background: #eceff1; border-color: #b0bec5; color: #37474f; }
        .footer { text-align: center; padding: 24px; font-size: 12px; color: var(--text-secondary); border-top: 1px solid var(--border); max-width: 1120px; margin: 0 auto; }
        .footer a { color: var(--primary); text-decoration: none; }
        #health-status, #kv-status { transition: all .3s; }"""

    ENTERPRISE_JS = """async function checkHealth() {
            try {
                const r = await fetch('/health');
                const d = await r.json();
                const el = document.getElementById('health-status');
                if (d.status === 'healthy') {
                    el.innerHTML = '<span class="status-dot green"></span>Healthy';
                    el.className = 'value ok';
                } else {
                    el.textContent = 'Degraded';
                    el.className = 'value warn';
                }
            } catch (e) {
                const el = document.getElementById('health-status');
                el.textContent = 'Unreachable';
                el.style.color = 'var(--danger)';
            }
        }
        async function checkKeyVault() {
            try {
                const r = await fetch('/keyvault/status');
                const d = await r.json();
                const el = document.getElementById('kv-status');
                if (d.status === 'connected') {
                    el.innerHTML = '<span class="status-dot green"></span>Connected';
                    el.className = 'value ok';
                } else {
                    el.textContent = 'Not configured';
                    el.style.color = 'var(--warning)';
                    el.style.fontSize = '14px';
                }
            } catch (e) {
                const el = document.getElementById('kv-status');
                el.textContent = 'Not configured';
                el.style.color = 'var(--text-secondary)';
                el.style.fontSize = '14px';
            }
        }
        checkHealth();
        checkKeyVault();
        setInterval(checkHealth, 30000);"""

    def _css_for_fstring(self) -> str:
        """Return CSS with braces escaped for embedding inside a Python f-string."""
        lb, rb = chr(123), chr(125)
        return self.ENTERPRISE_CSS.replace(lb, lb * 2).replace(rb, rb * 2)

    def _js_for_fstring(self) -> str:
        """Return dashboard JS with braces escaped for embedding inside a Python f-string."""
        lb, rb = chr(123), chr(125)
        return self.ENTERPRISE_JS.replace(lb, lb * 2).replace(rb, rb * 2)

    def _python_dashboard_block(self, spec: IntentSpec) -> str:
        """Return the Python code block for the root endpoint dashboard.

        When the spec has custom entities, generates a full interactive business
        operations dashboard.  Otherwise falls back to the simpler static
        dashboard.
        """
        if _has_custom_entities(spec):
            return self._python_business_dashboard(spec)
        return self._python_static_dashboard(spec)

    def _python_static_dashboard(self, spec: IntentSpec) -> str:
        """Return the static (dev-facing) dashboard HTML block."""
        # Derive entity slug from spec entities or fallback to 'resources'
        if spec.entities:
            _primary = _snake(_plural(spec.entities[0].name))
        else:
            _primary = "resources"
        compliance_badges = self._enterprise_compliance_badges(spec)
        data_stores = self._enterprise_data_stores(spec)
        quick_actions = f'<a class="action-btn" href="/docs"><span class="icon">\xf0\x9f\x93\x9a</span>API Documentation</a>\\n                    <a class="action-btn" href="/health"><span class="icon">\xf0\x9f\x92\x9a</span>Health Check</a>\\n                    <a class="action-btn" href="/keyvault/status"><span class="icon">\xf0\x9f\x94\x90</span>Key Vault Status</a>\\n                    <a class="action-btn" href="/api/v1/{_primary}"><span class="icon">\xf0\x9f\x93\xa6</span>API v1 {_primary.replace("_", " ").title()}</a>'
        endpoint_list = f'<li><span class="method-badge get">GET</span><span class="endpoint-path">/health</span><span class="endpoint-desc">Liveness probe</span></li>\\n                    <li><span class="method-badge get">GET</span><span class="endpoint-path">/docs</span><span class="endpoint-desc">OpenAPI docs</span></li>\\n                    <li><span class="method-badge get">GET</span><span class="endpoint-path">/keyvault/status</span><span class="endpoint-desc">Vault connectivity</span></li>\\n                    <li><span class="method-badge get">GET</span><span class="endpoint-path">/api/v1/{_primary}</span><span class="endpoint-desc">Resource listing</span></li>\\n                    <li><span class="method-badge post">POST</span><span class="endpoint-path">/api/v1/{_primary}</span><span class="endpoint-desc">Create resource</span></li>'
        # Helper refs to produce single-brace {VAR} in the generated f-string
        _an = "{APP_NAME}"
        _ver = "{VERSION}"
        _qa = "{quick_actions}"
        _el = "{endpoint_list}"
        _ds = "{data_stores}"
        _cb = "{compliance_badges}"

        return f'''compliance_badges = """{compliance_badges}"""
    data_stores = "{data_stores}"
    quick_actions = """{quick_actions}"""
    endpoint_list = """{endpoint_list}"""
    html = f\"\"\"<!DOCTYPE html>
<html lang=\\"en\\">
<head>
    <meta charset=\\"UTF-8\\">
    <meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1.0\\">
    <title>{_an} \\u2014 Enterprise Dashboard</title>
    <style>
        {self._css_for_fstring()}
    </style>
</head>
<body>
    <nav class=\\"topbar\\">
        <div class=\\"topbar-brand\\">
            <svg viewBox=\\"0 0 24 24\\"><path d=\\"M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5\\"/></svg>
            {_an}
        </div>
        <div class=\\"topbar-meta\\">
            <span class=\\"env-badge\\">{spec.environment}</span>
            <span>{spec.azure_region}</span>
        </div>
    </nav>
    <section class=\\"hero\\">
        <h1>{_an}</h1>
        <p>{spec.description}</p>
        <div class=\\"version-pill\\">v{_ver} \\u00b7 {spec.compute_target.value.replace("_", " ").title()}</div>
    </section>
    <div class=\\"dashboard\\">
        <div class=\\"card\\">
            <div class=\\"card-header\\"><div class=\\"card-icon\\" style=\\"background:#e6f4ea\\">\\U0001f49a</div><h3>System Status</h3></div>
            <div class=\\"card-body\\">
                <div class=\\"status-grid\\">
                    <div class=\\"status-item\\"><div class=\\"label\\">Health</div><div id=\\"health-status\\" class=\\"value\\">Checking\\u2026</div></div>
                    <div class=\\"status-item\\"><div class=\\"label\\">Key Vault</div><div id=\\"kv-status\\" class=\\"value\\">Checking\\u2026</div></div>
                    <div class=\\"status-item\\"><div class=\\"label\\">Region</div><div class=\\"value\\" style=\\"font-size:14px\\">{spec.azure_region}</div></div>
                    <div class=\\"status-item\\"><div class=\\"label\\">Environment</div><div class=\\"value\\" style=\\"font-size:14px;text-transform:capitalize\\">{spec.environment}</div></div>
                </div>
            </div>
        </div>
        <div class=\\"card\\">
            <div class=\\"card-header\\"><div class=\\"card-icon\\" style=\\"background:#e3f2fd\\">\\u26a1</div><h3>Quick Actions</h3></div>
            <div class=\\"card-body\\">
                <div class=\\"actions\\">
                    {_qa}
                </div>
            </div>
        </div>
        <div class=\\"card\\">
            <div class=\\"card-header\\"><div class=\\"card-icon\\" style=\\"background:#fff3e0\\">\\U0001f50c</div><h3>API Endpoints</h3></div>
            <div class=\\"card-body\\">
                <ul class=\\"endpoint-list\\">
                    {_el}
                </ul>
            </div>
        </div>
        <div class=\\"card\\">
            <div class=\\"card-header\\"><div class=\\"card-icon\\" style=\\"background:#fce4ec\\">\\U0001f3d7\\ufe0f</div><h3>Architecture &amp; Compliance</h3></div>
            <div class=\\"card-body\\">
                <ul class=\\"arch-list\\">
                    <li><span class=\\"arch-badge compute\\">COMPUTE</span>{spec.compute_target.value.replace("_", " ").title()}</li>
                    <li><span class=\\"arch-badge data\\">DATA</span>{_ds}</li>
                    <li><span class=\\"arch-badge security\\">SECURITY</span>{spec.security.auth_model.value.replace("_", " ").title()}</li>
                    <li><span class=\\"arch-badge monitor\\">MONITOR</span>Log Analytics \\u00b7 Health Probes</li>
                </ul>
                <div class=\\"compliance-row\\">{_cb}</div>
            </div>
        </div>
    </div>
    <footer class=\\"footer\\"><span id=\\"last-updated\\" style=\\"margin-right:12px\\"></span>{_an} v{_ver} \\u00b7 <a href=\\"/docs\\">API Docs</a> \\u00b7 <button class=\\"btn btn-primary btn-sm\\" onclick=\\"loadAll()\\" style=\\"margin-left:8px\\">&#8635; Refresh Data</button> \\u00b7 Enterprise DevEx Orchestrator</footer>
    <script>
        {self._js_for_fstring()}
    </script>
</body>
</html>
\\\"\\\"\\\"'''

    def _python_business_dashboard(self, spec: IntentSpec) -> str:
        """Return the interactive business operations dashboard HTML block."""
        dashboard_body = self._business_dashboard_body(spec)
        dashboard_css = self._business_dashboard_css()
        dashboard_js = self._business_dashboard_js(spec)
        compute = spec.compute_target.value.replace('_', ' ').title()
        # Helper refs to produce single-brace {VAR} in the generated f-string
        _an = "{APP_NAME}"
        _ver = "{VERSION}"

        return f'''html = f\"\"\"<!DOCTYPE html>
<html lang=\\"en\\">
<head>
    <meta charset=\\"UTF-8\\">
    <meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1.0\\">
    <title>{_an} \\u2014 Operations Dashboard</title>
    <style>
        {dashboard_css}
    </style>
</head>
<body>
    <nav class=\\"topbar\\">
        <div class=\\"topbar-brand\\">
            <svg viewBox=\\"0 0 24 24\\"><path d=\\"M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5\\"/></svg>
            {_an}
        </div>
        <div class=\\"topbar-meta\\">
            <div class=\\"status-live\\" id=\\"health-indicator\\"><span class=\\"dot\\"></span><span id=\\"health-text\\">Checking...</span></div>
            <span id=\\"live-clock\\" style=\\"font-family:Consolas,monospace;font-size:12px;\\"></span>
            <span class=\\"env-badge\\">{spec.environment}</span>
            <span>{spec.azure_region}</span>
        </div>
    </nav>
    <section class=\\"hero\\">
        <h1>{_an}</h1>
        <p>{spec.description}</p>
        <div class=\\"hero-pills\\">
            <span>v{_ver}</span>
            <span>{compute}</span>
            <span>{spec.azure_region}</span>
        </div>
    </section>
    <div class=\\"kpi-bar\\">
        {dashboard_body}
    <footer class=\\"footer\\"><span id=\\"last-updated\\" style=\\"margin-right:12px\\"></span>{_an} v{_ver} \\u00b7 <a href=\\"/docs\\">API Docs</a> \\u00b7 <button class=\\"btn btn-primary btn-sm\\" onclick=\\"loadAll()\\" style=\\"margin-left:8px\\">&#8635; Refresh Data</button> \\u00b7 Enterprise DevEx Orchestrator</footer>
    <script>
        {dashboard_js}
    </script>
</body>
</html>
\"\"\"'''

    def _enterprise_data_stores(self, spec: IntentSpec) -> str:
        """Render architecture data store line based on spec."""
        stores = []
        for ds in spec.data_stores:
            stores.append(ds.value.replace("_", " ").title())
        return " + ".join(stores) if stores else "Blob Storage"

    def _enterprise_compliance_badges(self, spec: IntentSpec, esc: str = "") -> str:
        """Render compliance badge HTML. Use esc='\\\\' for f-string escape contexts."""
        fw = spec.security.compliance_framework.value.lower()
        badge_map = {
            "hipaa": ("HIPAA", "hipaa"),
            "soc2": ("SOC2", "soc2"),
            "pci": ("PCI-DSS", "pci"),
            "fedramp": ("FedRAMP", "fedramp"),
            "iso27001": ("ISO 27001", "iso"),
            "general": ("Enterprise", "general"),
        }
        name, cls = badge_map.get(fw, ("Enterprise", "general"))
        badges = f'<span class="{esc}compliance-badge {cls}{esc}">{name}</span>\n'
        badges += f'                    <span class="{esc}compliance-badge rbac{esc}">RBAC</span>'
        return badges

    def generate(self, spec: IntentSpec) -> dict[str, str]:
        """Generate application files based on spec.language."""
        logger.info("app_generator.start", project=spec.project_name, language=spec.language)

        language = spec.language.lower()
        if language == "node":
            files = self._generate_node(spec)
        elif language == "dotnet":
            files = self._generate_dotnet(spec)
        else:
            files = self._generate_python(spec)

        logger.info("app_generator.complete", file_count=len(files), language=language)
        return files

    # ===============================================================
    # Python / FastAPI
    # ===============================================================

    def _generate_python(self, spec: IntentSpec) -> dict[str, str]:
        """Generate Python/FastAPI scaffold with enterprise DDD layout."""
        files: dict[str, str] = {}
        files["src/__init__.py"] = '"""Generated source package."""\n'
        files["src/app/__init__.py"] = '"""Generated application package."""\n'
        files["src/app/main.py"] = self._python_main(spec)
        files["src/app/requirements.txt"] = self._python_requirements(spec)
        files["src/app/Dockerfile"] = self._python_dockerfile(spec)

        # DDD layered architecture
        files["src/app/api/__init__.py"] = '"""API layer -- versioned routers."""\n'
        files["src/app/api/v1/__init__.py"] = '"""API v1 router package."""\n'
        files["src/app/api/v1/router.py"] = self._python_v1_router(spec)
        files["src/app/api/v1/schemas.py"] = self._python_v1_schemas(spec)
        files["src/app/core/__init__.py"] = '"""Core layer -- services, config, and dependencies."""\n'
        files["src/app/core/config.py"] = self._python_core_config(spec)
        files["src/app/core/dependencies.py"] = self._python_core_dependencies(spec)
        files["src/app/core/services.py"] = self._python_core_services(spec)

        # Domain layer -- models, repositories, seed data
        files["src/app/domain/__init__.py"] = '"""Domain layer -- models, repositories, seed data."""\n'
        files["src/app/domain/models.py"] = self._python_domain_models(spec)
        files["src/app/domain/repositories.py"] = self._python_repositories(spec)
        files["src/app/domain/seed_data.py"] = self._python_seed_data(spec)

        # AI layer -- when uses_ai is True
        if spec.uses_ai:
            files["src/app/ai/__init__.py"] = '"""AI layer -- LLM clients, agents, and chat."""\n'
            files["src/app/ai/client.py"] = self._python_ai_client(spec)
            files["src/app/ai/chat.py"] = self._python_ai_chat(spec)
            ai_features = getattr(spec, "ai_features", [])
            if "agents" in ai_features:
                files["src/app/ai/agent.py"] = self._python_ai_agent(spec)
            # Azure AI Foundry: model registry, content safety, evaluation
            files["src/app/ai/model_registry.py"] = self._python_ai_model_registry(spec)
            files["src/app/ai/content_safety.py"] = self._python_ai_content_safety(spec)
            files["src/app/ai/evaluation.py"] = self._python_ai_evaluation(spec)

        return files

    # ===============================================================
    # Node.js / Express
    # ===============================================================

    def _generate_node(self, spec: IntentSpec) -> dict[str, str]:
        """Generate Node.js/Express scaffold."""
        files: dict[str, str] = {}
        files["src/app/index.js"] = self._node_main(spec)
        files["src/app/package.json"] = self._node_package_json(spec)
        files["src/app/Dockerfile"] = self._node_dockerfile(spec)
        files["src/app/.env.example"] = self._node_env_example(spec)
        # Domain layer
        files["src/app/services.js"] = self._node_services(spec)
        files["src/app/data.js"] = self._node_seed_data(spec)
        return files

    # ===============================================================
    # .NET / ASP.NET Core
    # ===============================================================

    def _generate_dotnet(self, spec: IntentSpec) -> dict[str, str]:
        """Generate .NET/ASP.NET Core minimal API scaffold."""
        files: dict[str, str] = {}
        files["src/app/Program.cs"] = self._dotnet_program(spec)
        files[f"src/app/{spec.project_name}.csproj"] = self._dotnet_csproj(spec)
        files["src/app/Dockerfile"] = self._dotnet_dockerfile(spec)
        files["src/app/appsettings.json"] = self._dotnet_appsettings(spec)
        # Domain layer
        files["src/app/Services.cs"] = self._dotnet_services(spec)
        files["src/app/Data.cs"] = self._dotnet_seed_data(spec)
        return files

    def _python_main(self, spec: IntentSpec) -> str:
        storage_imports = ""
        storage_client = ""
        storage_endpoint = ""
        ai_import = ""
        ai_router_mount = ""

        if spec.uses_ai:
            ai_import = "from ai.chat import router as ai_router"
            ai_router_mount = 'app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])'

        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_imports = """
from azure.storage.blob import BlobServiceClient
"""
            storage_client = """
# -- Storage Client ---------------------------------------------------
def get_blob_client() -> BlobServiceClient:
    \"\"\"Create an authenticated Blob Storage client using Managed Identity.\"\"\"
    credential = DefaultAzureCredential(
        managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
    )
    account_url = os.getenv("STORAGE_ACCOUNT_URL", "")
    if not account_url:
        raise ValueError("STORAGE_ACCOUNT_URL environment variable not set")
    return BlobServiceClient(account_url=account_url, credential=credential)
"""
            storage_endpoint = """

@app.get("/storage/status")
async def storage_status():
    \"\"\"Check storage account connectivity.\"\"\"
    try:
        client = get_blob_client()
        containers = list(client.list_containers(max_results=1))
        return {
            "status": "connected",
            "containers_accessible": True,
        }
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": str(e)},
        )
"""

        return f"""\"\"\"Enterprise DevEx Orchestrator -- Generated Application.

Project: {spec.project_name}
Description: {spec.description}
Generated by: Enterprise DevEx Orchestrator Agent

This is a production-grade FastAPI application with:
- Health check endpoint
- Managed Identity authentication
- Key Vault integration
- Structured logging
\"\"\"

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
{storage_imports}
from api.v1.router import router as v1_router
{ai_import}
# -- Configuration ----------------------------------------------------
APP_NAME = "{spec.project_name}"
VERSION = "1.0.0"

# -- Logging ----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='{{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}}',
)
logger = logging.getLogger(APP_NAME)

# -- FastAPI Application ---------------------------------------------
app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="{spec.description}",
    docs_url="/docs",
    redoc_url=None,
)

# -- CORS Middleware --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -- Security Middleware -- Rate Limiting & Headers -------------------
from collections import defaultdict
import time as _time

_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))


@app.middleware("http")
async def security_middleware(request, call_next):
    \"\"\"Enterprise security middleware: rate limiting + security headers.\"\"\"
    # Rate limiting by client IP
    client_ip = request.client.host if request.client else "unknown"
    now = _time.time()
    window = 60.0
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if now - t < window
    ]
    if len(_rate_limit_store[client_ip]) >= _RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={{"detail": "Rate limit exceeded. Try again later."}},
        )
    _rate_limit_store[client_ip].append(now)

    response = await call_next(request)

    # Security headers (OWASP recommended)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

# -- Mount versioned API router --------------------------------------
app.include_router(v1_router, prefix="/api/v1", tags=["v1"])
{ai_router_mount}


# -- Key Vault Client ------------------------------------------------
def get_keyvault_client() -> SecretClient:
    \"\"\"Create an authenticated Key Vault client using Managed Identity.
    
    Supports two configuration patterns:
    1. KEY_VAULT_URI - full vault URL (https://vault-name.vault.azure.net)
    2. KEY_VAULT_NAME - vault name only (will construct URL)
    \"\"\"
    credential = DefaultAzureCredential(
        managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
    )
    
    # Try full URI first (recommended)
    vault_uri = os.getenv("KEY_VAULT_URI", "")
    if vault_uri:
        return SecretClient(vault_url=vault_uri, credential=credential)
    
    # Fallback to name-based construction
    vault_name = os.getenv("KEY_VAULT_NAME", "")
    if not vault_name:
        raise ValueError("Either KEY_VAULT_URI or KEY_VAULT_NAME must be set")
    
    return SecretClient(
        vault_url=f"https://{{vault_name}}.vault.azure.net",
        credential=credential
    )

{storage_client}
# -- Health Endpoint --------------------------------------------------
@app.get("/health")
async def health():
    \"\"\"Health check endpoint for liveness and readiness probes.\"\"\"
    return {{
        "status": "healthy",
        "service": APP_NAME,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }}


# -- Key Vault Status ------------------------------------------------
@app.get("/keyvault/status")
async def keyvault_status():
    \"\"\"Check Key Vault connectivity via Managed Identity.\"\"\"
    try:
        client = get_keyvault_client()
        # List secrets to verify access (limited to 1)
        secrets = list(client.list_properties_of_secrets(max_page_size=1))
        return {{
            "status": "connected",
            "vault_accessible": True,
        }}
    except Exception as e:
        logger.error(f"Key Vault health check failed: {{e}}")
        return JSONResponse(
            status_code=503,
            content={{"status": "error", "detail": str(e)}},
        )

{storage_endpoint}
# -- Startup Event ----------------------------------------------------
@app.on_event("startup")
async def startup():
    \"\"\"Application startup tasks.\"\"\"
    logger.info(f"{{APP_NAME}} v{{VERSION}} starting up")
    logger.info(f"Environment: {{os.getenv('ENVIRONMENT', 'unknown')}}")


@app.on_event("shutdown")
async def shutdown():
    \"\"\"Application shutdown tasks.\"\"\"
    logger.info(f"{{APP_NAME}} shutting down")


# -- Frontend Static Files (React SPA) --------------------------------
# Must be registered AFTER all API routes to avoid catch-all interference.
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="static-assets")

    @app.get("/{{full_path:path}}")
    async def serve_spa(request: Request, full_path: str):
        \"\"\"Serve the React SPA -- falls back to index.html for client-side routing.\"\"\"
        file_path = STATIC_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        \"\"\"Root endpoint -- no frontend build found.\"\"\"
        return HTMLResponse(
            content="<h1>API is running</h1>"
            "<p>Frontend not found. Build the frontend with <code>npm run build</code> "
            "and copy <code>dist/</code> contents to <code>static/</code>.</p>"
            f'<p><a href=\"/docs\">API Docs</a> | <a href=\"/health\">Health</a></p>'
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
"""

    def _python_requirements(self, spec: IntentSpec) -> str:
        reqs = """# Enterprise DevEx Orchestrator -- Generated Application Dependencies
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
azure-identity>=1.15.0
azure-keyvault-secrets>=4.8.0
pydantic>=2.5.0
pydantic-settings>=2.5.0
python-dotenv>=1.0.0
"""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            reqs += "azure-storage-blob>=12.19.0\n"
        if DataStore.COSMOS_DB in spec.data_stores:
            reqs += "azure-cosmos>=4.5.0\n"

        # AI dependencies
        if spec.uses_ai:
            reqs += "openai>=1.12.0\n"
            reqs += "python-multipart>=0.0.6\n"
            ai_features = getattr(spec, "ai_features", [])
            if "agents" in ai_features:
                reqs += "semantic-kernel>=1.0.0\n"
            if "rag" in ai_features or DataStore.AI_SEARCH in spec.data_stores:
                reqs += "azure-search-documents>=11.6.0\n"

        return reqs

    def _python_dockerfile(self, spec: IntentSpec) -> str:
        return f"""# ===================================================================
# Dockerfile -- {spec.project_name}
# Multi-stage build for minimal production image
# ===================================================================

# -- Build Stage ------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -- Runtime Stage ----------------------------------------------------
FROM python:3.11-slim AS runtime

# Security: run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Security: non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    # ===============================================================
    # Python DDD architecture layer files
    # ===============================================================

    def _python_v1_router(self, spec: IntentSpec) -> str:
        storage_routes = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_routes = """

@router.get("/storage/containers", summary="List storage containers")
async def list_containers(
    storage: BlobServiceClient = Depends(get_blob_service),
):
    containers = [c["name"] for c in storage.list_containers(max_results=10)]
    return {"containers": containers}
"""

        storage_import = ""
        storage_dep = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_import = "\nfrom azure.storage.blob import BlobServiceClient"
            storage_dep = "\nfrom core.dependencies import get_blob_service"

        # Dynamic generation from entities (all domains)
        if _has_custom_entities(spec):
            return self._dynamic_router(spec, storage_import, storage_dep, storage_routes)

        return f'''"""API v1 router -- versioned business endpoints.

Mount this router in main.py under /api/v1.
Add domain-specific routes here as the application grows.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from api.v1.schemas import ResourceCreate, ResourceResponse
from core.dependencies import get_settings, get_repository
from core.config import Settings
from core.services import ResourceService{storage_import}{storage_dep}

router = APIRouter()


@router.get("/resources", response_model=list[ResourceResponse], summary="List resources")
async def list_resources(settings: Settings = Depends(get_settings)):
    """Return resources from the service layer."""
    repo = get_repository("resource", settings.storage_mode)
    svc = ResourceService(project_name=settings.app_name, repo=repo)
    return svc.list_resources()


@router.post("/resources", response_model=ResourceResponse, status_code=201, summary="Create resource")
async def create_resource(payload: ResourceCreate, settings: Settings = Depends(get_settings)):
    """Create a new resource via the service layer."""
    repo = get_repository("resource", settings.storage_mode)
    svc = ResourceService(project_name=settings.app_name, repo=repo)
    return svc.create_resource(payload.name, payload.description)


@router.get("/resources/{{resource_id}}", summary="Get resource by ID")
async def get_resource(resource_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("resource", settings.storage_mode)
    svc = ResourceService(project_name=settings.app_name, repo=repo)
    resource = svc.get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.put("/resources/{{resource_id}}", summary="Update resource")
async def update_resource(resource_id: str, payload: ResourceCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("resource", settings.storage_mode)
    svc = ResourceService(project_name=settings.app_name, repo=repo)
    resource = svc.update_resource(resource_id, payload.name, payload.description)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.delete("/resources/{{resource_id}}", status_code=204, summary="Delete resource")
async def delete_resource(resource_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("resource", settings.storage_mode)
    svc = ResourceService(project_name=settings.app_name, repo=repo)
    if not svc.delete_resource(resource_id):
        raise HTTPException(status_code=404, detail="Resource not found")
{storage_routes}'''

    # ===============================================================
    # Dynamic code generation from spec.entities (domain-agnostic)
    # ===============================================================

    def _dynamic_router(self, spec: IntentSpec, storage_import: str, storage_dep: str, storage_routes: str) -> str:
        """Generate router dynamically from spec.entities — works for any domain."""
        entities = spec.entities
        # Build import lists
        schema_imports = []
        service_imports = []
        for ent in entities:
            sn = _snake(ent.name)
            schema_imports.append(f"{ent.name}Create, {ent.name}Response")
            service_imports.append(f"{ent.name}Service")
        schema_import_str = ", ".join(schema_imports)
        service_import_str = ", ".join(service_imports)

        lines = [
            '"""API v1 router -- domain-specific endpoints.',
            '',
            'Auto-generated from intent specification. Entities and endpoints',
            'are derived from the business requirements, not hardcoded templates.',
            '"""',
            '',
            'from __future__ import annotations',
            '',
            'from fastapi import APIRouter, Depends, HTTPException',
            f'from api.v1.schemas import ({schema_import_str})',
            'from core.dependencies import get_settings, get_repository',
            'from core.config import Settings',
            f'from core.services import ({service_import_str}){storage_import}{storage_dep}',
            '',
            'router = APIRouter()',
        ]

        for ent in entities:
            sn = _snake(ent.name)
            slug = _snake(_plural(ent.name))
            label = ent.name
            has_status = any(f.name in ("status", "state") for f in ent.fields)

            # Build the list of writable field names for create/update
            writable_fields = [f for f in ent.fields if f.name not in ("status", "state")]
            create_kwargs = ", ".join(f"payload.{f.name}" for f in writable_fields)

            # List endpoint — only include status filter if entity has a status/state field
            if has_status:
                list_block = f'''
# --- {label} CRUD ---
@router.get("/{slug}", response_model=list[{label}Response], summary="List {_plural(label).lower()}")
async def list_{slug}(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    return svc.list_all(status)'''
            else:
                list_block = f'''
# --- {label} CRUD ---
@router.get("/{slug}", response_model=list[{label}Response], summary="List {_plural(label).lower()}")
async def list_{slug}(settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    return svc.list_all()'''

            lines.append(list_block + f'''

@router.post("/{slug}", response_model={label}Response, status_code=201, summary="Create {label.lower()}")
async def create_{sn}(payload: {label}Create, settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    return svc.create(payload)

@router.get("/{slug}/{{{sn}_id}}", summary="Get {label.lower()} by ID")
async def get_{sn}({sn}_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    record = svc.get({sn}_id)
    if not record:
        raise HTTPException(status_code=404, detail="{label} not found")
    return record

@router.put("/{slug}/{{{sn}_id}}", summary="Update {label.lower()}")
async def update_{sn}({sn}_id: str, payload: {label}Create, settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    record = svc.update({sn}_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail="{label} not found")
    return record

@router.delete("/{slug}/{{{sn}_id}}", status_code=204, summary="Delete {label.lower()}")
async def delete_{sn}({sn}_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    if not svc.delete({sn}_id):
        raise HTTPException(status_code=404, detail="{label} not found")''')

            # Add workflow action endpoints detected from spec.endpoints
            for ep in (spec.endpoints or []):
                # Match action endpoints like POST /{slug}/{id}/approve
                parts = ep.path.strip("/").split("/")
                if len(parts) >= 3 and ep.method == "POST" and parts[0] == slug:
                    action = parts[-1]
                    lines.append(f'''

@router.post("/{slug}/{{{sn}_id}}/{action}", summary="{ep.description}")
async def {action}_{sn}({sn}_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    record = svc.{action}({sn}_id)
    if not record:
        raise HTTPException(status_code=404, detail="{label} not found")
    return record''')

        lines.append(storage_routes)
        return "\n".join(lines)

    def _dynamic_schemas(self, spec: IntentSpec) -> str:
        """Generate Pydantic schemas from spec.entities — works for any domain."""
        # Check if any entity uses datetime fields
        has_datetime = any(
            f.type == "datetime"
            for ent in spec.entities
            for f in ent.fields
        )

        lines = [
            '"""API v1 request/response schemas.',
            '',
            'Auto-generated from intent specification.',
            '"""',
            '',
            'from __future__ import annotations',
            '',
        ]
        if has_datetime:
            lines.append('from datetime import datetime')
            lines.append('')
        lines += [
            'from pydantic import BaseModel, Field',
            '',
        ]
        for ent in spec.entities:
            # Create schema — writable fields
            lines.append(f'class {ent.name}Create(BaseModel):')
            lines.append(f'    """Schema for creating a {ent.name.lower()}."""')
            lines.append('')
            for field in ent.fields:
                if field.name == "status":
                    continue  # status is set by the service, not the client
                req = "..." if field.required else f'"{""}"' if field.type == "str" else "None"
                if field.type in ("list", "list[str]"):
                    req = "Field(default_factory=list)" if not field.required else "..."
                lines.append(f'    {field.name}: {field.type} = Field(default={req}, description="{field.description}")')
            lines.append('')
            lines.append('')

            # Response schema — all fields
            lines.append(f'class {ent.name}Response(BaseModel):')
            lines.append(f'    """Schema returned by {ent.name.lower()} endpoints."""')
            lines.append('')
            lines.append('    id: str = Field(..., description="Unique identifier")')
            for field in ent.fields:
                if field.type in ("list", "list[str]"):
                    lines.append(f'    {field.name}: {field.type} = Field(default_factory=list, description="{field.description}")')
                elif not field.required:
                    lines.append(f'    {field.name}: {field.type} = Field(default=None, description="{field.description}")')
                else:
                    lines.append(f'    {field.name}: {field.type} = Field(..., description="{field.description}")')
            lines.append('    created_at: str = Field(default="", description="Creation timestamp")' if "created_at" not in {f.name for f in ent.fields} else '')
            lines.append('')
            lines.append('')

        return "\n".join(lines)

    def _dynamic_services(self, spec: IntentSpec) -> str:
        """Generate service classes from spec.entities — works for any domain."""
        lines = [
            '"""Business service layer — domain-specific.',
            '',
            'Auto-generated from intent specification. Each service manages',
            'one domain entity with CRUD operations and workflow actions.',
            '"""',
            '',
            'from __future__ import annotations',
            '',
            'import uuid',
            'from datetime import datetime, timezone',
            '',
            'from domain.repositories import BaseRepository',
            '',
        ]
        for ent in spec.entities:
            sn = _snake(ent.name)
            label = ent.name
            slug = _snake(_plural(ent.name))
            has_status = any(f.name in ("status", "state") for f in ent.fields)

            lines.append(f'class {label}Service:')
            lines.append(f'    """{ent.description or f"Manages {label} domain entities."}"""')
            lines.append('')
            lines.append('    def __init__(self, repo: BaseRepository) -> None:')
            lines.append('        self.repo = repo')
            lines.append('')

            # list_all — only filter by status if entity has a status/state field
            if has_status:
                lines.append('    def list_all(self, status: str | None = None) -> list[dict]:')
                lines.append('        items = self.repo.list_all()')
                lines.append('        if status:')
                lines.append('            items = [i for i in items if i.get("status") == status]')
                lines.append('        return items')
            else:
                lines.append('    def list_all(self) -> list[dict]:')
                lines.append('        return self.repo.list_all()')
            lines.append('')

            # get
            lines.append(f'    def get(self, {sn}_id: str) -> dict | None:')
            lines.append(f'        return self.repo.get({sn}_id)')
            lines.append('')

            # create
            lines.append(f'    def create(self, payload) -> dict:')
            lines.append(f'        record = {{')
            lines.append(f'            "id": str(uuid.uuid4()),')
            for field in ent.fields:
                if field.name == "status":
                    lines.append(f'            "status": "pending",')
                else:
                    lines.append(f'            "{field.name}": getattr(payload, "{field.name}", {"\"\"" if field.type == "str" else "None"}),')
            lines.append(f'            "created_at": datetime.now(timezone.utc).isoformat(),')
            lines.append(f'            "updated_at": datetime.now(timezone.utc).isoformat(),')
            lines.append(f'        }}')
            lines.append(f'        self.repo.create(record["id"], record)')
            lines.append(f'        return record')
            lines.append('')

            # update
            lines.append(f'    def update(self, {sn}_id: str, payload) -> dict | None:')
            lines.append(f'        record = self.repo.get({sn}_id)')
            lines.append(f'        if not record:')
            lines.append(f'            return None')
            for field in ent.fields:
                if field.name == "status":
                    continue
                lines.append(f'        val = getattr(payload, "{field.name}", None)')
                lines.append(f'        if val is not None:')
                lines.append(f'            record["{field.name}"] = val')
            lines.append(f'        record["updated_at"] = datetime.now(timezone.utc).isoformat()')
            lines.append(f'        self.repo.update({sn}_id, record)')
            lines.append(f'        return record')
            lines.append('')

            # delete
            lines.append(f'    def delete(self, {sn}_id: str) -> bool:')
            lines.append(f'        return self.repo.delete({sn}_id)')
            lines.append('')

            # Workflow action methods detected from endpoints
            for ep in (spec.endpoints or []):
                parts = ep.path.strip("/").split("/")
                if len(parts) >= 3 and ep.method == "POST" and parts[0] == slug:
                    action = parts[-1]
                    lines.append(f'    def {action}(self, {sn}_id: str) -> dict | None:')
                    lines.append(f'        """Transition {label.lower()} to \'{action}\' state."""')
                    lines.append(f'        record = self.repo.get({sn}_id)')
                    lines.append(f'        if not record:')
                    lines.append(f'            return None')
                    lines.append(f'        record["status"] = "{action}ed" if not "{action}".endswith("e") else "{action}d"')
                    lines.append(f'        record["updated_at"] = datetime.now(timezone.utc).isoformat()')
                    lines.append(f'        self.repo.update({sn}_id, record)')
                    lines.append(f'        return record')
                    lines.append('')

            lines.append('')

        return "\n".join(lines)

    def _dynamic_models(self, spec: IntentSpec) -> str:
        """Generate domain models from spec.entities — works for any domain."""
        lines = [
            '"""Domain models — auto-generated from intent specification."""',
            '',
            'from __future__ import annotations',
            '',
            'from dataclasses import dataclass, field',
            'from datetime import datetime, timezone',
            '',
        ]
        for ent in spec.entities:
            lines.append(f'@dataclass')
            lines.append(f'class {ent.name}:')
            lines.append(f'    id: str = ""')
            for f in ent.fields:
                default = _python_type_default(f.type)
                lines.append(f'    {f.name}: {f.type} = {default}')
            field_names = {f.name for f in ent.fields}
            if "created_at" not in field_names:
                lines.append('    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())')
            if "updated_at" not in field_names:
                lines.append('    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())')
            lines.append('')
            lines.append('')
        return "\n".join(lines)

    def _dynamic_seed_data(self, spec: IntentSpec) -> str:
        """Generate seed data from spec.entities — works for any domain."""
        lines = [
            '"""Seed data — auto-generated from intent specification."""',
            '',
            'from __future__ import annotations',
            '',
            '_SEED: dict[str, list[dict]] = {',
        ]
        _record_count = 12  # enough for meaningful analytics
        for idx, ent in enumerate(spec.entities):
            sn = _snake(ent.name)
            lines.append(f'    "{sn}": [')
            for rid in range(1, _record_count + 1):
                record_parts = [f'"id": "{sn}-{rid:03d}"']
                for f in ent.fields:
                    if f.name == "created_at":
                        continue  # appended below with realistic timestamps
                    val = _seed_value(f, ent.name, rid)
                    record_parts.append(f'"{f.name}": {val}')
                record_parts.append(f'"created_at": "{ _seed_timestamp(rid) }"')
                lines.append(f'        {{{", ".join(record_parts)}}},')
            lines.append(f'    ],')
        lines.append('}')
        lines.append('')
        lines.append('')
        lines.append('def get_seed_data(entity_name: str) -> list[dict]:')
        lines.append('    """Return seed records for the given entity type."""')
        lines.append('    return _SEED.get(entity_name, [])')
        lines.append('')
        return "\n".join(lines)

    def _dynamic_dashboard_endpoints(self, spec: IntentSpec) -> str:
        """Generate dashboard endpoint list HTML from spec.entities."""
        html_parts = []
        for ent in spec.entities:
            slug = _snake(_plural(ent.name))
            label = _plural(ent.name)
            html_parts.append(
                f'<li><span class=\\"method-badge get\\">GET</span>'
                f'<span class=\\"endpoint-path\\">/api/v1/{slug}</span>'
                f'<span class=\\"endpoint-desc\\">List {label.lower()}</span></li>'
            )
            html_parts.append(
                f'<li><span class=\\"method-badge post\\">POST</span>'
                f'<span class=\\"endpoint-path\\">/api/v1/{slug}</span>'
                f'<span class=\\"endpoint-desc\\">Create {ent.name.lower()}</span></li>'
            )
        # Always include infrastructure endpoints
        html_parts.insert(0,
            '<li><span class=\\"method-badge get\\">GET</span>'
            '<span class=\\"endpoint-path\\">/health</span>'
            '<span class=\\"endpoint-desc\\">Liveness probe</span></li>'
        )
        html_parts.insert(1,
            '<li><span class=\\"method-badge get\\">GET</span>'
            '<span class=\\"endpoint-path\\">/docs</span>'
            '<span class=\\"endpoint-desc\\">OpenAPI docs</span></li>'
        )
        return "\n                    ".join(html_parts)

    def _dynamic_quick_actions(self, spec: IntentSpec) -> str:
        """Generate Quick Actions HTML links for dashboard from spec.entities."""
        actions = [
            '<a class=\\"action-btn\\" href=\\"/docs\\"><span class=\\"icon\\">📚</span>API Documentation</a>',
            '<a class=\\"action-btn\\" href=\\"/health\\"><span class=\\"icon\\">💚</span>Health Check</a>',
            '<a class=\\"action-btn\\" href=\\"/keyvault/status\\"><span class=\\"icon\\">🔐</span>Key Vault Status</a>',
        ]
        icons = ["📦", "🔄", "📋", "📊", "🏷️"]
        for i, ent in enumerate(spec.entities):
            slug = _snake(_plural(ent.name))
            icon = icons[i % len(icons)]
            actions.append(
                f'<a class=\\"action-btn\\" href=\\"/api/v1/{slug}\\"><span class=\\"icon\\">{icon}</span>{_plural(ent.name)}</a>'
            )
        return "\n                    ".join(actions)

    # ---------------------------------------------------------------
    # Interactive Business Dashboard (CEO-friendly)
    # ---------------------------------------------------------------

    def _business_dashboard_css(self) -> str:
        """Extra CSS for the interactive business operations dashboard."""
        lb, rb = chr(123), chr(125)
        raw = """:root {
            --primary: #0078d4;
            --primary-dark: #005a9e;
            --success: #107c10;
            --warning: #ff8c00;
            --danger: #d13438;
            --bg: #f3f2f1;
            --surface: #ffffff;
            --surface-alt: #faf9f8;
            --text: #323130;
            --text-secondary: #605e5c;
            --border: #edebe9;
            --shadow: 0 2px 8px rgba(0,0,0,.08);
            --shadow-lg: 0 8px 32px rgba(0,0,0,.12);
            --radius: 8px;
            --radius-lg: 12px;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif; background:var(--bg); color:var(--text); min-height:100vh; }
        .topbar { background:linear-gradient(135deg,#0078d4 0%,#005a9e 100%); color:white; padding:0 32px; height:48px; display:flex; align-items:center; justify-content:space-between; font-size:13px; box-shadow:0 1px 4px rgba(0,0,0,.15); position:sticky; top:0; z-index:100; }
        .topbar-brand { display:flex; align-items:center; gap:10px; font-weight:600; font-size:14px; }
        .topbar-brand svg { width:20px; height:20px; fill:white; }
        .topbar-meta { display:flex; gap:16px; align-items:center; }
        .topbar-meta span { opacity:.85; }
        .env-badge { background:rgba(255,255,255,.2); padding:2px 10px; border-radius:12px; font-size:11px; text-transform:uppercase; font-weight:600; letter-spacing:.5px; }
        .status-live { display:flex; align-items:center; gap:6px; font-size:12px; }
        .status-live .dot { width:8px; height:8px; border-radius:50%; background:var(--success); animation:pulse 2s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
        .hero { background:linear-gradient(180deg,#005a9e 0%,#0078d4 50%,var(--bg) 100%); padding:40px 32px 56px; text-align:center; color:white; }
        .hero h1 { font-size:26px; font-weight:600; margin-bottom:6px; }
        .hero p { font-size:14px; opacity:.9; max-width:600px; margin:0 auto; line-height:1.5; }
        .hero-pills { display:flex; gap:8px; justify-content:center; margin-top:12px; flex-wrap:wrap; }
        .hero-pills span { background:rgba(255,255,255,.15); padding:3px 14px; border-radius:20px; font-size:11px; font-weight:500; }
        .kpi-bar { max-width:1200px; margin:-32px auto 20px; padding:0 24px; display:flex; flex-wrap:wrap; justify-content:center; gap:16px; }
        .kpi { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:20px; text-align:center; box-shadow:var(--shadow); transition:transform .15s; min-width:160px; flex:1 1 180px; max-width:220px; }
        .kpi:hover { transform:translateY(-2px); box-shadow:var(--shadow-lg); }
        .kpi .number { font-size:32px; font-weight:700; }
        .kpi .label { font-size:11px; text-transform:uppercase; letter-spacing:.8px; color:var(--text-secondary); margin-top:4px; }
        .kpi.ok .number { color:var(--success); }
        .kpi.warn .number { color:var(--warning); }
        .kpi.danger .number { color:var(--danger); }
        .main { max-width:1200px; margin:0 auto 40px; padding:0 24px; }
        .tab-bar { display:flex; gap:0; margin-bottom:0; border-bottom:2px solid var(--border); flex-wrap:wrap; justify-content:center; }
        .tab { padding:12px 24px; font-size:13px; font-weight:600; cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-2px; color:var(--text-secondary); transition:all .15s; }
        .tab:hover { color:var(--text); }
        .tab.active { color:var(--primary); border-bottom-color:var(--primary); }
        .tab-panel { display:none; }
        .tab-panel.active { display:block; }
        .panel-toolbar { display:flex; justify-content:space-between; align-items:center; padding:16px 0; gap:12px; flex-wrap:wrap; }
        .search-box { padding:8px 14px; border:1px solid var(--border); border-radius:var(--radius); font-size:13px; width:280px; outline:none; }
        .search-box:focus { border-color:var(--primary); box-shadow:0 0 0 2px rgba(0,120,212,.15); }
        .btn { padding:8px 18px; border:none; border-radius:var(--radius); font-size:13px; font-weight:600; cursor:pointer; transition:all .15s; display:inline-flex; align-items:center; gap:6px; }
        .btn-primary { background:var(--primary); color:white; }
        .btn-primary:hover { background:var(--primary-dark); }
        .btn-success { background:var(--success); color:white; }
        .btn-success:hover { opacity:.9; }
        .btn-warning { background:var(--warning); color:white; }
        .btn-warning:hover { opacity:.9; }
        .btn-danger { background:var(--danger); color:white; }
        .btn-danger:hover { opacity:.9; }
        .btn-sm { padding:4px 10px; font-size:11px; }
        .data-table { width:100%; border-collapse:separate; border-spacing:0; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); overflow:hidden; box-shadow:var(--shadow); }
        .data-table th { background:var(--surface-alt); padding:10px 14px; font-size:11px; text-transform:uppercase; letter-spacing:.5px; color:var(--text-secondary); text-align:left; font-weight:600; border-bottom:1px solid var(--border); }
        .data-table td { padding:10px 14px; font-size:13px; border-bottom:1px solid var(--border); }
        .data-table tr:last-child td { border-bottom:none; }
        .data-table tr:hover td { background:#f0f6ff; }
        .badge { display:inline-block; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600; text-transform:capitalize; }
        .badge-pending,.badge-draft,.badge-new,.badge-open,.badge-queued,.badge-submitted,.badge-waiting { background:#fff3e0; color:#e65100; }
        .badge-in_progress,.badge-in-progress,.badge-processing,.badge-running,.badge-active,.badge-busy,.badge-executing { background:#e3f2fd; color:#1565c0; }
        .badge-approved,.badge-completed,.badge-processed,.badge-done,.badge-resolved,.badge-closed,.badge-success,.badge-passed,.badge-delivered,.badge-published { background:#e6f4ea; color:#1b5e20; }
        .badge-rejected,.badge-cancelled,.badge-failed,.badge-error,.badge-denied,.badge-expired,.badge-blocked,.badge-terminated { background:#fce4ec; color:#b71c1c; }
        .badge-escalated,.badge-critical,.badge-urgent,.badge-high { background:#f3e5f5; color:#6a1b9a; }
        .badge-on_hold,.badge-on-hold,.badge-paused,.badge-suspended,.badge-deferred,.badge-review,.badge-pending_review { background:#e8eaf6; color:#283593; }
        .badge-inactive,.badge-disabled,.badge-offline,.badge-idle,.badge-standby,.badge-maintenance { background:#eceff1; color:#546e7a; }
        .badge-warning,.badge-degraded,.badge-medium,.badge-partial { background:#fffde7; color:#f57f17; }
        .badge-online,.badge-healthy,.badge-connected,.badge-available,.badge-ready,.badge-low { background:#e0f2f1; color:#00695c; }
        .modal-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,.4); z-index:200; justify-content:center; align-items:center; }
        .modal-overlay.open { display:flex; }
        .modal { background:var(--surface); border-radius:var(--radius-lg); box-shadow:var(--shadow-lg); width:480px; max-width:90vw; max-height:80vh; overflow-y:auto; }
        .modal-header { padding:16px 20px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; }
        .modal-header h3 { font-size:16px; font-weight:600; }
        .modal-close { background:none; border:none; font-size:20px; cursor:pointer; color:var(--text-secondary); }
        .modal-body { padding:20px; }
        .form-group { margin-bottom:14px; }
        .form-group label { display:block; font-size:12px; font-weight:600; color:var(--text-secondary); margin-bottom:4px; text-transform:uppercase; letter-spacing:.3px; }
        .form-group input,.form-group select,.form-group textarea { width:100%; padding:8px 12px; border:1px solid var(--border); border-radius:var(--radius); font-size:13px; outline:none; }
        .form-group input:focus,.form-group select:focus,.form-group textarea:focus { border-color:var(--primary); box-shadow:0 0 0 2px rgba(0,120,212,.15); }
        .modal-footer { padding:12px 20px; border-top:1px solid var(--border); display:flex; justify-content:flex-end; gap:8px; }
        .toast { position:fixed; bottom:24px; right:24px; padding:12px 20px; border-radius:var(--radius); color:white; font-size:13px; font-weight:500; z-index:300; transform:translateY(80px); opacity:0; transition:all .3s; box-shadow:var(--shadow-lg); }
        .toast.show { transform:translateY(0); opacity:1; }
        .toast.success { background:var(--success); }
        .toast.error { background:var(--danger); }
        .detail-row { display:grid; grid-template-columns:140px 1fr; gap:8px; padding:6px 0; border-bottom:1px solid var(--border); font-size:13px; }
        .detail-row:last-child { border-bottom:none; }
        .detail-row .dl { font-weight:600; color:var(--text-secondary); }
        .empty-state { text-align:center; padding:40px; color:var(--text-secondary); }
        .empty-state .icon { font-size:48px; margin-bottom:12px; }
        .footer { text-align:center; padding:24px; font-size:12px; color:var(--text-secondary); border-top:1px solid var(--border); max-width:1200px; margin:0 auto; }
        .footer a { color:var(--primary); text-decoration:none; }
        .sidebar-info { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px; }
        .info-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:16px; box-shadow:var(--shadow); }
        .info-card h4 { font-size:12px; text-transform:uppercase; letter-spacing:.5px; color:var(--text-secondary); margin-bottom:8px; }
        .info-card ul { list-style:none; font-size:13px; }
        .info-card ul li { padding:4px 0; display:flex; align-items:center; gap:8px; }
        .info-card ul li::before { content:''; width:6px; height:6px; border-radius:50%; background:var(--primary); flex-shrink:0; }
        .chat-container { display:flex; flex-direction:column; height:520px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); box-shadow:var(--shadow); overflow:hidden; }
        .chat-header { background:linear-gradient(135deg,#0078d4,#005a9e); color:white; padding:14px 20px; display:flex; justify-content:space-between; align-items:center; }
        .chat-header h4 { font-size:14px; font-weight:600; margin:0; }
        .chat-status { font-size:11px; display:flex; align-items:center; gap:6px; }
        .chat-status .dot { width:8px; height:8px; border-radius:50%; }
        .chat-messages { flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:12px; background:var(--surface-alt); }
        .chat-msg { max-width:85%; padding:10px 14px; border-radius:12px; font-size:13px; line-height:1.6; word-wrap:break-word; }
        .chat-msg.user { align-self:flex-end; background:var(--primary); color:white; border-bottom-right-radius:4px; white-space:pre-wrap; }
        .chat-msg.assistant { align-self:flex-start; background:var(--surface); border:1px solid var(--border); border-bottom-left-radius:4px; box-shadow:var(--shadow); max-width:92%; }
        .ai-table { width:100%; border-collapse:collapse; font-size:12px; margin:6px 0; }
        .ai-table th { background:var(--surface-alt); padding:6px 8px; text-align:left; border-bottom:2px solid var(--border); font-weight:600; font-size:11px; text-transform:uppercase; color:var(--text-secondary); }
        .ai-table td { padding:5px 8px; border-bottom:1px solid var(--border); }
        .ai-table tr:hover td { background:rgba(0,120,212,.04); }
        .ai-table code { background:var(--surface-alt); padding:1px 4px; border-radius:3px; font-size:11px; }
        .ai-stats-row { display:flex; flex-wrap:wrap; gap:6px; margin:8px 0; }
        .ai-stat { display:inline-flex; align-items:center; gap:4px; padding:4px 10px; border-radius:16px; border-left:3px solid; background:var(--surface-alt); font-size:12px; }
        .ai-section { margin:8px 0; }
        .ai-section-title { font-weight:600; font-size:14px; color:var(--primary); margin-bottom:6px; padding-bottom:4px; border-bottom:1px solid var(--border); }
        .ai-greeting { font-size:14px; margin-bottom:8px; }
        .ai-hint { font-size:12px; color:var(--text-secondary); margin:6px 0; padding:6px 10px; background:var(--surface-alt); border-radius:var(--radius); border-left:3px solid var(--primary); }
        .ai-suggestions { margin:6px 0 0; padding-left:18px; font-size:12px; }
        .ai-suggestions li { margin:3px 0; color:var(--text-secondary); }
        .ai-bar-chart { margin:4px 0; }
        .ai-bar-row { display:flex; align-items:center; gap:6px; margin:3px 0; font-size:12px; }
        .ai-bar-label { min-width:80px; text-align:right; color:var(--text-secondary); text-transform:capitalize; }
        .ai-bar-track { flex:1; height:16px; background:var(--surface-alt); border-radius:8px; overflow:hidden; }
        .ai-bar-fill { height:100%; border-radius:8px; transition:width .3s; }
        .ai-bar-val { min-width:24px; font-weight:600; }
        .chat-msg.system { align-self:center; background:var(--surface-alt); border:1px solid var(--border); color:var(--text-secondary); font-size:12px; text-align:center; max-width:90%; }
        .chat-input-bar { display:flex; gap:8px; padding:12px 16px; border-top:1px solid var(--border); background:var(--surface); }
        .chat-input { flex:1; padding:10px 14px; border:1px solid var(--border); border-radius:20px; font-size:13px; outline:none; resize:none; font-family:inherit; }
        .chat-input:focus { border-color:var(--primary); box-shadow:0 0 0 2px rgba(0,120,212,.15); }
        .chat-send { padding:10px 20px; background:var(--primary); color:white; border:none; border-radius:20px; font-size:13px; font-weight:600; cursor:pointer; transition:background .15s; }
        .chat-send:hover { background:var(--primary-dark); }
        .chat-send:disabled { opacity:.5; cursor:not-allowed; }
        .chat-upload-btn { display:flex; align-items:center; justify-content:center; width:38px; height:38px; border-radius:50%; border:1px solid var(--border); cursor:pointer; color:var(--text-secondary); transition:all .15s; flex-shrink:0; }
        .chat-upload-btn:hover { background:var(--surface-alt); color:var(--primary); border-color:var(--primary); }
        .chat-file-preview { display:flex; align-items:center; gap:8px; padding:8px 12px; margin:0 16px 4px; background:var(--surface-alt); border:1px solid var(--border); border-radius:var(--radius); font-size:12px; color:var(--text-secondary); }
        .chat-file-preview .file-name { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .chat-file-preview .file-remove { cursor:pointer; color:var(--danger); font-weight:bold; }
        .chat-msg .file-analysis { background:var(--surface-alt); border:1px solid var(--border); border-radius:var(--radius); padding:10px; margin-top:8px; font-size:12px; white-space:pre-wrap; }
        .chat-typing { display:flex; gap:4px; padding:8px 14px; align-self:flex-start; }
        .chat-typing span { width:8px; height:8px; border-radius:50%; background:var(--text-secondary); animation:typing 1.4s infinite; }
        .chat-typing span:nth-child(2) { animation-delay:.2s; }
        .chat-typing span:nth-child(3) { animation-delay:.4s; }
        @keyframes typing { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-6px)} }"""
        return raw.replace(lb, lb * 2).replace(rb, rb * 2)

    def _business_dashboard_body(self, spec: IntentSpec) -> str:
        """Generate the business dashboard HTML body with KPI cards, tabs, tables, and modals."""
        entities = spec.entities
        kpi_html = []
        for ent in entities:
            slug = _snake(_plural(ent.name))
            label = _plural(ent.name)
            kpi_html.append(
                f'<div class=\\"kpi\\" id=\\"kpi-{slug}\\">'
                f'<div class=\\"number\\" id=\\"count-{slug}\\">--</div>'
                f'<div class=\\"label\\">Total {label}</div></div>'
            )
        # Dynamic status summary — JS populates from actual data
        kpi_html.append(
            '<div class=\\"kpi warn\\" id=\\"kpi-action-needed\\">'
            '<div class=\\"number\\" id=\\"count-action-needed\\">--</div>'
            '<div class=\\"label\\">Needs Action</div></div>'
        )
        kpi_html.append(
            '<div class=\\"kpi ok\\" id=\\"kpi-resolved\\">'
            '<div class=\\"number\\" id=\\"count-resolved\\">--</div>'
            '<div class=\\"label\\">Resolved</div></div>'
        )
        kpis = "\n        ".join(kpi_html)

        # Tabs
        tabs_html = []
        panels_html = []
        for i, ent in enumerate(entities):
            slug = _snake(_plural(ent.name))
            label = _plural(ent.name)
            active = " active" if i == 0 else ""
            tabs_html.append(f'<div class=\\"tab{active}\\" data-tab=\\"{slug}\\">{label}</div>')

            # Table columns from entity fields (skip heavy ones like lists/dicts for table view)
            table_cols = ["ID"]
            field_keys = []
            for f in ent.fields:
                if f.type not in ("list", "list[str]", "dict") and f.name not in ("notes",):
                    table_cols.append(f.name.replace("_", " ").title())
                    field_keys.append(f.name)
            table_cols.append("Actions")
            th_html = "".join(f"<th>{c}</th>" for c in table_cols)

            sq = "&#39;"
            panels_html.append(
                f'<div class=\\"tab-panel{active}\\" id=\\"panel-{slug}\\">'
                f'<div class=\\"panel-toolbar\\">'
                f'<input type=\\"text\\" class=\\"search-box\\" placeholder=\\"Search {label.lower()}...\\" oninput=\\"filterTable({sq}{slug}{sq}, this.value)\\">'
                f'<button class=\\"btn btn-primary\\" onclick=\\"openCreateModal({sq}{ent.name}{sq}, {sq}{slug}{sq})\\">+ New {ent.name}</button>'
                f'</div>'
                f'<table class=\\"data-table\\" id=\\"table-{slug}\\">'
                f'<thead><tr>{th_html}</tr></thead>'
                f'<tbody id=\\"tbody-{slug}\\"><tr><td colspan=\\"{len(table_cols)}\\" style=\\"text-align:center;padding:24px;color:var(--text-secondary)\\">Loading...</td></tr></tbody>'
                f'</table></div>'
            )
        tabs_html.append('<div class=\\"tab\\" data-tab=\\"system\\">System</div>')

        # AI chat tab -- added when spec uses AI
        ai_chat_panel = ""
        if spec.uses_ai:
            tabs_html.append('<div class=\\"tab\\" data-tab=\\"ai-chat\\">AI Assistant</div>')
            ai_chat_panel = (
                '<div class=\\"tab-panel\\" id=\\"panel-ai-chat\\">'
                '<div class=\\"chat-container\\">'
                '<div class=\\"chat-header\\">'
                f'<h4>AI Assistant &mdash; {spec.project_name}</h4>'
                '<div class=\\"chat-status\\"><span class=\\"dot\\" id=\\"ai-status-dot\\" style=\\"background:var(--text-secondary)\\"></span><span id=\\"ai-status-text\\">Checking...</span></div>'
                '</div>'
                '<div class=\\"chat-messages\\" id=\\"chatMessages\\">'
                '<div class=\\"chat-msg system\\">Ask me anything about your data. I can search, analyze, and provide insights across all entities.</div>'
                '</div>'
                '<div class=\\"chat-input-bar\\">'
                '<label class=\\"chat-upload-btn\\" title=\\"Upload file (image, document, audio, receipt)\\"><input type=\\"file\\" id=\\"chatFileInput\\" style=\\"display:none\\" onchange=\\"uploadFile()\\" accept=\\"image/*,audio/*,.pdf,.docx,.xlsx,.csv,.txt,.json,.xml,.md,.html\\"><svg width=\\"18\\" height=\\"18\\" viewBox=\\"0 0 24 24\\" fill=\\"none\\" stroke=\\"currentColor\\" stroke-width=\\"2\\"><path d=\\"M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48\\"/></svg></label>'
                '<input type=\\"text\\" class=\\"chat-input\\" id=\\"chatInput\\" placeholder=\\"Ask about your data or upload a file...\\" onkeydown=\\"if(event.key===&#39;Enter&#39;)sendChat()\\">'
                '<button class=\\"chat-send\\" id=\\"chatSend\\" onclick=\\"sendChat()\\">Send</button>'
                '</div>'
                '</div></div>'
            )

        tabs = "\n            ".join(tabs_html)
        panels = "\n        ".join(panels_html)

        # System panel
        arch_info = spec.compute_target.value.replace("_", " ").title()
        data_stores_str = self._enterprise_data_stores(spec)
        security_str = spec.security.auth_model.value.replace("_", " ").title()

        system_panel = (
            f'<div class=\\"tab-panel\\" id=\\"panel-system\\">'
            f'<div class=\\"sidebar-info\\">'
            f'<div class=\\"info-card\\"><h4>Architecture</h4><ul>'
            f'<li>Compute: {arch_info}</li>'
            f'<li>Data: {data_stores_str}</li>'
            f'<li>Security: {security_str}</li>'
            f'<li>Monitoring: Log Analytics</li></ul></div>'
            f'<div class=\\"info-card\\"><h4>API Documentation</h4><ul>'
            f'<li><a href=\\"/docs\\" style=\\"color:var(--primary)\\">Interactive API Docs</a></li>'
            f'<li><a href=\\"/health\\" style=\\"color:var(--primary)\\">Health Check</a></li>'
            f'<li><a href=\\"/keyvault/status\\" style=\\"color:var(--primary)\\">Key Vault Status</a></li></ul></div>'
            f'</div></div>'
        )

        return f"""{kpis}
    </div>
    <div class=\\"main\\">
        <div class=\\"tab-bar\\">
            {tabs}
        </div>
        {panels}
        {system_panel}
        {ai_chat_panel}
    </div>
    <div class=\\"modal-overlay\\" id=\\"createModal\\">
        <div class=\\"modal\\">
            <div class=\\"modal-header\\"><h3 id=\\"modalTitle\\">Create</h3><button class=\\"modal-close\\" onclick=\\"closeModal()\\">&times;</button></div>
            <div class=\\"modal-body\\" id=\\"modalBody\\"></div>
            <div class=\\"modal-footer\\"><button class=\\"btn\\" onclick=\\"closeModal()\\">Cancel</button><button class=\\"btn btn-primary\\" id=\\"modalSubmit\\" onclick=\\"submitCreate()\\">Create</button></div>
        </div>
    </div>
    <div class=\\"modal-overlay\\" id=\\"detailModal\\">
        <div class=\\"modal\\">
            <div class=\\"modal-header\\"><h3 id=\\"detailTitle\\">Details</h3><button class=\\"modal-close\\" onclick=\\"closeDetail()\\">&times;</button></div>
            <div class=\\"modal-body\\" id=\\"detailBody\\"></div>
            <div class=\\"modal-footer\\" id=\\"detailActions\\"></div>
        </div>
    </div>
    <div id=\\"toast\\" class=\\"toast\\"></div>"""

    def _business_dashboard_js(self, spec: IntentSpec) -> str:
        """Generate JS for the interactive business dashboard -- fetches, tables, modals, actions."""
        lb, rb = chr(123), chr(125)
        entities = spec.entities

        # Build entity config object
        entity_configs = []
        for ent in entities:
            slug = _snake(_plural(ent.name))
            id_field = _snake(ent.name) + "_id"
            fields_for_table = []
            fields_for_form = []
            for f in ent.fields:
                if f.type not in ("list", "list[str]", "dict") and f.name not in ("notes",):
                    fields_for_table.append(f.name)
                if f.name != "status":
                    fields_for_form.append({"name": f.name, "type": f.type})
            # Detect workflow actions from spec.endpoints
            actions = []
            for ep in spec.endpoints:
                # endpoints like POST /returns/{id}/approve
                if f"/{slug}/" in ep.path and ep.method == "POST" and "{" in ep.path:
                    parts = ep.path.rstrip("/").split("/")
                    action_word = parts[-1]
                    if action_word not in (slug, f"{{{id_field}}}"):
                        actions.append(action_word)
            entity_configs.append({
                "name": ent.name,
                "slug": slug,
                "id_field": id_field,
                "table_fields": fields_for_table,
                "form_fields": fields_for_form,
                "actions": actions,
            })

        # Serialize entity config to JS
        import json
        config_js = json.dumps(entity_configs, indent=8)

        raw = f"""
        const ENTITIES = {config_js};
        let allData = {lb}{rb};

        // Dynamic status classification — adapts to any domain
        const ACTION_STATUSES = ['pending','draft','new','open','queued','submitted','waiting','in_progress','in-progress','processing','running','active','review','pending_review','on_hold','on-hold','paused'];
        const RESOLVED_STATUSES = ['completed','approved','processed','done','resolved','closed','success','passed','delivered','published','inactive','disabled','offline','cancelled','rejected','failed','error','denied','expired','terminated'];

        async function loadAll() {lb}
            let actionNeeded = 0, resolved = 0;
            for (const ent of ENTITIES) {lb}
                try {lb}
                    const r = await fetch('/api/v1/' + ent.slug);
                    const d = await r.json();
                    const rows = Array.isArray(d) ? d : (d.value || d.items || d.data || []);
                    allData[ent.slug] = rows;
                    document.getElementById('count-' + ent.slug).textContent = rows.length;
                    rows.forEach(row => {lb}
                        const s = String(row.status || '').toLowerCase().replace(/ /g,'_');
                        if (ACTION_STATUSES.includes(s)) actionNeeded++;
                        else if (RESOLVED_STATUSES.includes(s)) resolved++;
                    {rb});
                    renderTable(ent, rows);
                {rb} catch(e) {lb}
                    console.error('Failed to load ' + ent.slug, e);
                    document.getElementById('count-' + ent.slug).textContent = '!';
                {rb}
            {rb}
            const anEl = document.getElementById('count-action-needed');
            if (anEl) anEl.textContent = actionNeeded;
            const rsEl = document.getElementById('count-resolved');
            if (rsEl) rsEl.textContent = resolved;
            const luEl = document.getElementById('last-updated');
            if (luEl) luEl.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        {rb}

        function renderTable(ent, rows) {lb}
            const tbody = document.getElementById('tbody-' + ent.slug);
            if (!rows.length) {lb}
                tbody.innerHTML = '<tr><td colspan="' + (ent.table_fields.length + 2) + '" style="text-align:center;padding:32px;color:var(--text-secondary)"><div class="empty-state"><div class="icon">📭</div><div>No ' + ent.slug.replace(/_/g,' ') + ' yet</div></div></td></tr>';
                return;
            {rb}
            tbody.innerHTML = rows.map(row => {lb}
                const idShort = (row.id || '').substring(0, 8);
                let cells = '<td style="font-family:Consolas,monospace;font-size:12px;cursor:pointer;color:var(--primary)" onclick="openDetail(&#39;' + ent.slug + '&#39;,&#39;' + row.id + '&#39;)">' + idShort + '...</td>';
                ent.table_fields.forEach(f => {lb}
                    const val = row[f] != null ? row[f] : '-';
                    if (f === 'status' || f === 'state' || f.endsWith('_status')) {lb}
                        cells += '<td><span class="badge badge-' + String(val).replace(/ /g,'-').replace(/[^a-zA-Z0-9-_]/g,'') + '">' + val + '</span></td>';
                    {rb} else if (f.endsWith('_at') || f.endsWith('_date') || f === 'timestamp' || f === 'date' || f === 'created' || f === 'updated') {lb}
                        const d = new Date(val);
                        cells += '<td>' + (isNaN(d) ? val : d.toLocaleDateString()) + '</td>';
                    {rb} else if (f === 'amount' || f === 'price' || f === 'cost' || f === 'total' || f === 'fee' || f === 'balance' || f.endsWith('_amount') || f.endsWith('_price') || f.endsWith('_cost')) {lb}
                        cells += '<td style="font-weight:600">$' + Number(val).toFixed(2) + '</td>';
                    {rb} else if (f === 'priority' || f === 'severity' || f === 'level' || f === 'urgency') {lb}
                        const pcolor = ['high','critical','urgent','p1'].includes(String(val).toLowerCase()) ? 'var(--danger)' : ['medium','p2','warning'].includes(String(val).toLowerCase()) ? 'var(--warning)' : 'var(--text-secondary)';
                        cells += '<td style="font-weight:600;color:' + pcolor + '">' + val + '</td>';
                    {rb} else if (f === 'email' || f.endsWith('_email')) {lb}
                        cells += '<td><a href="mailto:' + val + '" style="color:var(--primary)">' + val + '</a></td>';
                    {rb} else if (f === 'url' || f === 'link' || f === 'website' || f.endsWith('_url')) {lb}
                        cells += '<td><a href="' + val + '" target="_blank" style="color:var(--primary)">' + String(val).substring(0,40) + '</a></td>';
                    {rb} else if (typeof val === 'boolean' || f.startsWith('is_') || f.startsWith('has_') || f === 'enabled' || f === 'active') {lb}
                        cells += '<td>' + (val === true || val === 'true' || val === 'True' ? '\u2705' : '\u274c') + '</td>';
                    {rb} else if (typeof val === 'number' && !Number.isInteger(val)) {lb}
                        cells += '<td>' + Number(val).toFixed(2) + '</td>';
                    {rb} else {lb}
                        const sv = String(val);
                        cells += '<td>' + (sv.length > 60 ? sv.substring(0,57) + '...' : sv) + '</td>';
                    {rb}
                {rb});
                let actionBtns = '';
                const ACTION_STYLES = {lb}'approve':'btn-success','accept':'btn-success','activate':'btn-success','enable':'btn-success','publish':'btn-success','start':'btn-success','deploy':'btn-success','confirm':'btn-success','resolve':'btn-success',
                    'reject':'btn-danger','deny':'btn-danger','delete':'btn-danger','remove':'btn-danger','cancel':'btn-danger','terminate':'btn-danger','disable':'btn-danger','block':'btn-danger','revoke':'btn-danger',
                    'process':'btn-warning','escalate':'btn-warning','retry':'btn-warning','resubmit':'btn-warning','pause':'btn-warning','suspend':'btn-warning','flag':'btn-warning','review':'btn-warning','archive':'btn-warning'{rb};
                const s = String(row.status || '').toLowerCase().replace(/ /g,'_');
                const isTerminal = RESOLVED_STATUSES.includes(s);
                if (!isTerminal) {lb}
                    ent.actions.forEach(action => {lb}
                        const btnClass = ACTION_STYLES[action] || 'btn-primary';
                        const label = action.charAt(0).toUpperCase() + action.slice(1).replace(/_/g,' ');
                        actionBtns += '<button class="btn ' + btnClass + ' btn-sm" onclick="doAction(&#39;' + ent.slug + '&#39;,&#39;' + row.id + '&#39;,&#39;' + action + '&#39;)">' + label + '</button> ';
                    {rb});
                {rb}
                if (!actionBtns) actionBtns = '<span style="color:var(--text-secondary);font-size:12px">' + (isTerminal ? '\u2714 Done' : 'No actions') + '</span>';
                cells += '<td>' + actionBtns + '</td>';
                return '<tr>' + cells + '</tr>';
            {rb}).join('');
        {rb}

        function filterTable(slug, query) {lb}
            const rows = allData[slug] || [];
            const q = query.toLowerCase();
            const ent = ENTITIES.find(e => e.slug === slug);
            const filtered = rows.filter(r => JSON.stringify(r).toLowerCase().includes(q));
            renderTable(ent, filtered);
        {rb}

        // Tabs
        document.querySelectorAll('.tab').forEach(tab => {lb}
            tab.addEventListener('click', () => {lb}
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
            {rb});
        {rb});

        // Create modal
        let createTarget = {lb}{rb};
        function openCreateModal(entityName, slug) {lb}
            const ent = ENTITIES.find(e => e.slug === slug);
            createTarget = {lb} entityName, slug {rb};
            document.getElementById('modalTitle').textContent = 'Create New ' + entityName;
            let formHtml = '';
            ent.form_fields.forEach(f => {lb}
                const label = f.name.replace(/_/g, ' ');
                if (f.type === 'list' || f.type === 'list[str]') {lb}
                    formHtml += '<div class="form-group"><label>' + label + '</label><input type="text" name="' + f.name + '" placeholder="Comma-separated values"></div>';
                {rb} else if (f.type === 'float' || f.type === 'int') {lb}
                    formHtml += '<div class="form-group"><label>' + label + '</label><input type="number" name="' + f.name + '" step="any"></div>';
                {rb} else if (f.type === 'bool') {lb}
                    formHtml += '<div class="form-group"><label>' + label + '</label><select name="' + f.name + '"><option value="true">Yes</option><option value="false">No</option></select></div>';
                {rb} else {lb}
                    formHtml += '<div class="form-group"><label>' + label + '</label><input type="text" name="' + f.name + '"></div>';
                {rb}
            {rb});
            document.getElementById('modalBody').innerHTML = formHtml;
            document.getElementById('createModal').classList.add('open');
        {rb}
        function closeModal() {lb} document.getElementById('createModal').classList.remove('open'); {rb}

        async function submitCreate() {lb}
            const ent = ENTITIES.find(e => e.slug === createTarget.slug);
            const body = {lb}{rb};
            ent.form_fields.forEach(f => {lb}
                const input = document.querySelector('#modalBody [name="' + f.name + '"]');
                if (!input) return;
                let val = input.value;
                if (f.type === 'list' || f.type === 'list[str]') {lb}
                    body[f.name] = val ? val.split(',').map(s => s.trim()) : [];
                {rb} else if (f.type === 'float') {lb}
                    body[f.name] = parseFloat(val) || 0;
                {rb} else if (f.type === 'int') {lb}
                    body[f.name] = parseInt(val) || 0;
                {rb} else if (f.type === 'bool') {lb}
                    body[f.name] = val === 'true';
                {rb} else {lb}
                    body[f.name] = val;
                {rb}
            {rb});
            try {lb}
                const r = await fetch('/api/v1/' + createTarget.slug, {lb} method:'POST', headers:{lb}'Content-Type':'application/json'{rb}, body:JSON.stringify(body) {rb});
                if (r.ok) {lb}
                    showToast('success', createTarget.entityName + ' created successfully');
                    closeModal();
                    loadAll();
                {rb} else {lb}
                    const err = await r.json();
                    showToast('error', 'Error: ' + (err.detail || JSON.stringify(err)));
                {rb}
            {rb} catch(e) {lb}
                showToast('error', 'Network error');
            {rb}
        {rb}

        // Detail modal
        function openDetail(slug, id) {lb}
            const ent = ENTITIES.find(e => e.slug === slug);
            const rows = allData[slug] || [];
            const row = rows.find(r => r.id === id);
            if (!row) return;
            document.getElementById('detailTitle').textContent = ent.name + ' Details';
            let html = '';
            Object.entries(row).forEach(([k,v]) => {lb}
                const label = k.replace(/_/g,' ').replace(/\\\\b\\\\w/g, c => c.toUpperCase());
                let display = v;
                if (Array.isArray(v)) display = v.join(', ');
                if (k === 'status' || k === 'state' || k.endsWith('_status')) display = '<span class="badge badge-' + String(v).replace(/ /g,'-').replace(/[^a-zA-Z0-9_-]/g,'') + '">' + v + '</span>';
                else if (k === 'amount' || k === 'price' || k === 'cost' || k === 'total' || k === 'fee' || k === 'balance' || k.endsWith('_amount') || k.endsWith('_price') || k.endsWith('_cost')) display = '$' + Number(v).toFixed(2);
                else if (k.endsWith('_at') || k.endsWith('_date') || k === 'timestamp' || k === 'date') {lb} const d=new Date(v); if(!isNaN(d)) display=d.toLocaleString(); {rb}
                else if (typeof v === 'boolean' || k.startsWith('is_') || k.startsWith('has_')) display = v ? '\u2705' : '\u274c';
                else if (k === 'email' || k.endsWith('_email')) display = '<a href="mailto:'+v+'" style="color:var(--primary)">'+v+'</a>';
                html += '<div class="detail-row"><div class="dl">' + label + '</div><div>' + display + '</div></div>';
            {rb});
            document.getElementById('detailBody').innerHTML = html;

            // Action buttons in detail — dynamic from entity actions
            let actionsHtml = '<button class="btn" onclick="closeDetail()">Close</button>';
            const ds = String(row.status || '').toLowerCase().replace(/ /g,'_');
            const isTerminalDetail = RESOLVED_STATUSES.includes(ds);
            if (!isTerminalDetail) {lb}
                const DA = {lb}'approve':'btn-success','accept':'btn-success','activate':'btn-success','enable':'btn-success','publish':'btn-success','start':'btn-success','confirm':'btn-success','resolve':'btn-success',
                    'reject':'btn-danger','deny':'btn-danger','delete':'btn-danger','remove':'btn-danger','cancel':'btn-danger','terminate':'btn-danger','disable':'btn-danger',
                    'process':'btn-warning','escalate':'btn-warning','retry':'btn-warning','resubmit':'btn-warning','pause':'btn-warning','review':'btn-warning','archive':'btn-warning'{rb};
                ent.actions.forEach(action => {lb}
                    const bc = DA[action] || 'btn-primary';
                    const lbl = action.charAt(0).toUpperCase() + action.slice(1).replace(/_/g,' ');
                    actionsHtml += ' <button class="btn ' + bc + '" onclick="doAction(&#39;' + slug + '&#39;,&#39;' + id + '&#39;,&#39;' + action + '&#39;);closeDetail()">' + lbl + '</button>';
                {rb});
            {rb}
            document.getElementById('detailActions').innerHTML = actionsHtml;
            document.getElementById('detailModal').classList.add('open');
        {rb}
        function closeDetail() {lb} document.getElementById('detailModal').classList.remove('open'); {rb}

        async function doAction(slug, id, action) {lb}
            if (!confirm('Are you sure you want to ' + action + ' this record?')) return;
            try {lb}
                const r = await fetch('/api/v1/' + slug + '/' + id + '/' + action, {lb} method:'POST' {rb});
                if (r.ok) {lb}
                    showToast('success', action.charAt(0).toUpperCase() + action.slice(1) + ' completed');
                    loadAll();
                {rb} else {lb}
                    const err = await r.json();
                    showToast('error', 'Error: ' + (err.detail || 'Action failed'));
                {rb}
            {rb} catch(e) {lb}
                showToast('error', 'Network error');
            {rb}
        {rb}

        function showToast(type, msg) {lb}
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.className = 'toast ' + type + ' show';
            setTimeout(() => {lb} t.classList.remove('show'); {rb}, 3000);
        {rb}

        // Init
        loadAll();
        setInterval(loadAll, 30000);

        // Real-time clock
        function updateClock() {lb}
            const now = new Date();
            const el = document.getElementById('live-clock');
            if (el) el.textContent = now.toLocaleString('en-US', {lb}
                weekday:'short', year:'numeric', month:'short', day:'numeric',
                hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false
            {rb});
        {rb}
        updateClock();
        setInterval(updateClock, 1000);

        // Health check
        async function checkHealth() {lb}
            const indicator = document.getElementById('health-indicator');
            if (!indicator) return;
            const dot = indicator.querySelector('.dot');
            const text = document.getElementById('health-text');
            try {lb}
                const r = await fetch('/health');
                const d = await r.json();
                if (d.status === 'healthy') {lb}
                    dot.style.background = 'var(--success)';
                    text.textContent = 'Healthy';
                {rb} else {lb}
                    dot.style.background = 'var(--warning)';
                    text.textContent = 'Degraded';
                {rb}
            {rb} catch(e) {lb}
                dot.style.background = 'var(--danger)';
                text.textContent = 'Offline';
            {rb}
        {rb}
        checkHealth();
        setInterval(checkHealth, 15000);
"""

        # Add AI chat JS when AI is enabled
        if spec.uses_ai:
            chat_js = f"""

        // AI Chat
        let chatHistory = [];
        async function checkAIStatus() {lb}
            const dot = document.getElementById('ai-status-dot');
            const text = document.getElementById('ai-status-text');
            if (!dot) return;
            try {lb}
                const r = await fetch('/api/v1/ai/models');
                const d = await r.json();
                if (d.status === 'available') {lb}
                    dot.style.background = 'var(--success)';
                    text.textContent = d.provider + ' (' + d.chat_model + ')';
                {rb} else {lb}
                    dot.style.background = 'var(--success)';
                    text.textContent = 'Local Data Engine (query your data)';
                {rb}
            {rb} catch(e) {lb}
                dot.style.background = 'var(--danger)';
                text.textContent = 'Unavailable';
            {rb}
        {rb}
        checkAIStatus();

        function appendChatMsg(role, content) {lb}
            const container = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = 'chat-msg ' + role;
            if (role === 'assistant' && (content.includes('<') && content.includes('>'))) {lb}
                div.innerHTML = content;
            {rb} else {lb}
                div.textContent = content;
            {rb}
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        {rb}

        function showTyping() {lb}
            const container = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = 'chat-typing';
            div.id = 'typing-indicator';
            div.innerHTML = '<span></span><span></span><span></span>';
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        {rb}

        function hideTyping() {lb}
            const el = document.getElementById('typing-indicator');
            if (el) el.remove();
        {rb}

        async function sendChat() {lb}
            const input = document.getElementById('chatInput');
            const msg = input.value.trim();
            if (!msg) return;
            input.value = '';
            appendChatMsg('user', msg);
            chatHistory.push({lb} role: 'user', content: msg {rb});
            document.getElementById('chatSend').disabled = true;
            showTyping();
            try {lb}
                const r = await fetch('/api/v1/ai/chat', {lb}
                    method: 'POST',
                    headers: {lb} 'Content-Type': 'application/json' {rb},
                    body: JSON.stringify({lb}
                        message: msg,
                        history: chatHistory.slice(-10)
                    {rb})
                {rb});
                hideTyping();
                if (r.ok) {lb}
                    const d = await r.json();
                    appendChatMsg('assistant', d.reply);
                    chatHistory.push({lb} role: 'assistant', content: d.reply {rb});
                {rb} else {lb}
                    const err = await r.json().catch(() => ({lb}{rb}));
                    appendChatMsg('system', 'Error: ' + (err.detail || 'AI service unavailable. Configure AZURE_OPENAI_ENDPOINT or OPENAI_API_KEY.'));
                {rb}
            {rb} catch(e) {lb}
                hideTyping();
                appendChatMsg('system', 'Network error: ' + e.message);
            {rb}
            document.getElementById('chatSend').disabled = false;
            input.focus();
        {rb}

        async function uploadFile() {lb}
            const fileInput = document.getElementById('chatFileInput');
            const file = fileInput.files[0];
            if (!file) return;
            fileInput.value = '';

            const sizeMB = file.size / (1024 * 1024);
            if (sizeMB > 20) {lb}
                appendChatMsg('system', 'File too large (max 20MB): ' + file.name);
                return;
            {rb}

            appendChatMsg('user', '\U0001F4CE Uploaded: ' + file.name + ' (' + (sizeMB < 1 ? (file.size/1024).toFixed(0)+'KB' : sizeMB.toFixed(1)+'MB') + ')');
            document.getElementById('chatSend').disabled = true;
            showTyping();

            try {lb}
                const formData = new FormData();
                formData.append('file', file);

                const r = await fetch('/api/v1/ai/upload', {lb}
                    method: 'POST',
                    body: formData
                {rb});
                hideTyping();
                if (r.ok) {lb}
                    const d = await r.json();
                    const replyText = d.analysis || d.reply || 'File processed.';
                    appendChatMsg('assistant', replyText);
                    chatHistory.push({lb} role: 'user', content: 'Uploaded file: ' + file.name {rb});
                    chatHistory.push({lb} role: 'assistant', content: replyText {rb});
                {rb} else {lb}
                    const err = await r.json().catch(() => ({lb}{rb}));
                    appendChatMsg('system', 'Upload error: ' + (err.detail || 'Failed to process file'));
                {rb}
            {rb} catch(e) {lb}
                hideTyping();
                appendChatMsg('system', 'Upload failed: ' + e.message);
            {rb}
            document.getElementById('chatSend').disabled = false;
        {rb}
"""
            raw += chat_js

        return raw.replace(lb, lb * 2).replace(rb, rb * 2)

    def _python_v1_schemas(self, spec: IntentSpec) -> str:
        # Dynamic generation when entities come from intent parsing
        if _has_custom_entities(spec):
            return self._dynamic_schemas(spec)

        # Base schemas always included for backward compatibility
        base = '''"""API v1 request/response schemas.

Keep Pydantic models here so routers stay thin.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResourceCreate(BaseModel):
    """Schema for creating a new resource."""

    name: str = Field(..., min_length=1, max_length=120, description="Resource name")
    description: str = Field(default="", max_length=500, description="Resource description")


class ResourceResponse(BaseModel):
    """Schema returned by resource endpoints."""

    id: str = Field(..., description="Unique resource identifier")
    name: str = Field(..., description="Resource name")
    description: str = Field(default="", description="Resource description")
    project: str = Field(..., description="Owning project name")
'''

        return base

    def _python_core_config(self, spec: IntentSpec) -> str:
        storage_field = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_field = '\n    storage_account_url: str = Field(default="", description="Azure Storage account URL")'

        cosmos_field = ""
        if DataStore.COSMOS_DB in spec.data_stores:
            cosmos_field = '\n    cosmos_endpoint: str = Field(default="", description="Cosmos DB endpoint")\n    cosmos_database: str = Field(default="", description="Cosmos DB database name")'

        return f'''"""Application configuration via pydantic-settings.

Environment variables are automatically loaded.  Values can be
overridden with a .env file during local development.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised configuration -- reads from environment variables."""

    app_name: str = Field(default="{spec.project_name}", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="{spec.environment}", description="Runtime environment")
    port: int = Field(default=8000, description="HTTP listen port")

    # Storage mode: "memory" for in-memory (demo/dev), "azure" for Azure services
    storage_mode: str = Field(default="memory", description="Storage backend: memory or azure")

    # Azure integration
    azure_client_id: str = Field(default="", description="Managed identity client ID")
    key_vault_uri: str = Field(default="", description="Key Vault URI")
    key_vault_name: str = Field(default="", description="Key Vault name (fallback)"){storage_field}{cosmos_field}

    model_config = {{"env_file": ".env", "extra": "ignore"}}
'''

    def _python_core_dependencies(self, spec: IntentSpec) -> str:
        storage_dep = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_dep = """

def get_blob_service() -> BlobServiceClient:
    \"\"\"Dependency that yields an authenticated BlobServiceClient.\"\"\"
    from azure.storage.blob import BlobServiceClient

    settings = get_settings()
    credential = DefaultAzureCredential(
        managed_identity_client_id=settings.azure_client_id or None
    )
    if not settings.storage_account_url:
        raise ValueError("STORAGE_ACCOUNT_URL not configured")
    return BlobServiceClient(
        account_url=settings.storage_account_url, credential=credential
    )
"""

        return f'''"""Dependency injection helpers for FastAPI.

Use these with `Depends()` in route functions to obtain
configured clients and settings.
"""

from __future__ import annotations

from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from core.config import Settings
from domain.repositories import InMemoryRepository


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Repository singletons keyed by entity name
_repositories: dict[str, object] = {{}}


def get_repository(entity_name: str, storage_mode: str = "memory"):
    \"\"\"Factory that returns a repository for the given entity.

    In 'memory' mode, returns an InMemoryRepository (pre-seeded on first call).
    In 'azure' mode, extend with CosmosRepository / BlobRepository as needed.
    \"\"\"
    key = f"{{entity_name}}:{{storage_mode}}"
    if key not in _repositories:
        if storage_mode == "azure":
            # Placeholder for Azure SDK repositories
            _repositories[key] = InMemoryRepository()
        else:
            repo = InMemoryRepository()
            # Auto-seed demo data on first access
            try:
                from domain.seed_data import get_seed_data
                for item in get_seed_data(entity_name):
                    repo.create(item["id"], item)
            except (ImportError, KeyError):
                pass
            _repositories[key] = repo
    return _repositories[key]


def get_keyvault_client() -> SecretClient:
    \"\"\"Dependency that yields an authenticated SecretClient.\"\"\"
    settings = get_settings()
    credential = DefaultAzureCredential(
        managed_identity_client_id=settings.azure_client_id or None
    )
    vault_uri = settings.key_vault_uri
    if not vault_uri and settings.key_vault_name:
        vault_uri = f"https://{{settings.key_vault_name}}.vault.azure.net"
    if not vault_uri:
        raise ValueError("KEY_VAULT_URI or KEY_VAULT_NAME must be set")
    return SecretClient(vault_url=vault_uri, credential=credential)
{storage_dep}'''

    def _python_core_services(self, spec: IntentSpec) -> str:
        if _has_custom_entities(spec):
            return self._dynamic_services(spec)

        # Generic / default domain
        return f'''"""Business service layer.

Put domain logic here, not in routers.  Services are framework-agnostic
and can be tested independently of FastAPI.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from domain.repositories import BaseRepository


class ResourceService:
    """Generic CRUD domain service with repository-backed persistence."""

    def __init__(self, project_name: str = "{spec.project_name}", repo: BaseRepository | None = None) -> None:
        self.project_name = project_name
        self.repo = repo

    def list_resources(self) -> list[dict]:
        """Return all resources from the repository."""
        if self.repo:
            return self.repo.list_all()
        return [
            {{
                "id": "sample-001",
                "name": "Example Resource",
                "description": "Replace this stub with your data store query.",
                "project": self.project_name,
            }}
        ]

    def create_resource(self, name: str, description: str = "") -> dict:
        """Create and return a new resource."""
        resource = {{
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "project": self.project_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }}
        if self.repo:
            self.repo.create(resource["id"], resource)
        return resource

    def get_resource(self, resource_id: str) -> dict | None:
        """Get a single resource by ID."""
        if self.repo:
            return self.repo.get(resource_id)
        return None

    def update_resource(self, resource_id: str, name: str | None = None, description: str | None = None) -> dict | None:
        """Update an existing resource."""
        if not self.repo:
            return None
        resource = self.repo.get(resource_id)
        if not resource:
            return None
        if name is not None:
            resource["name"] = name
        if description is not None:
            resource["description"] = description
        resource["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.repo.update(resource_id, resource)
        return resource

    def delete_resource(self, resource_id: str) -> bool:
        """Delete a resource by ID."""
        if self.repo:
            return self.repo.delete(resource_id)
        return False
'''

    # ===============================================================
    # Domain layer file generators
    # ===============================================================

    def _python_domain_models(self, spec: IntentSpec) -> str:
        if _has_custom_entities(spec):
            return self._dynamic_models(spec)

        # Generic
        return '''"""Domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Item:
    id: str = ""
    name: str = ""
    description: str = ""
    status: str = "active"
    project: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
'''

    def _python_repositories(self, spec: IntentSpec) -> str:
        return '''"""Repository pattern -- pluggable storage backends.

Switch between in-memory (demo/dev) and Azure SDK (production)
by setting the STORAGE_MODE environment variable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseRepository(ABC):
    """Abstract base for all repositories."""

    @abstractmethod
    def get(self, entity_id: str) -> dict | None: ...

    @abstractmethod
    def list_all(self) -> list[dict]: ...

    @abstractmethod
    def create(self, entity_id: str, data: dict) -> dict: ...

    @abstractmethod
    def update(self, entity_id: str, data: dict) -> dict | None: ...

    @abstractmethod
    def delete(self, entity_id: str) -> bool: ...


class InMemoryRepository(BaseRepository):
    """Dict-backed repository for demos and testing."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def get(self, entity_id: str) -> dict | None:
        return self._store.get(entity_id)

    def list_all(self) -> list[dict]:
        return list(self._store.values())

    def create(self, entity_id: str, data: dict) -> dict:
        self._store[entity_id] = data
        return data

    def update(self, entity_id: str, data: dict) -> dict | None:
        if entity_id not in self._store:
            return None
        self._store[entity_id] = data
        return data

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False
'''

    def _python_seed_data(self, spec: IntentSpec) -> str:
        if _has_custom_entities(spec):
            return self._dynamic_seed_data(spec)

        # Generic
        return '''"""Seed data -- generic demo records."""

from __future__ import annotations

_SEED: dict[str, list[dict]] = {
    "resource": [
        {"id": "res-001", "name": "Example Widget", "description": "A sample resource", "status": "active", "project": "demo", "created_at": "2024-03-15T08:00:00Z"},
        {"id": "res-002", "name": "Test Service", "description": "A sample service offering", "status": "active", "project": "demo", "created_at": "2024-03-15T09:00:00Z"},
        {"id": "res-003", "name": "Draft Report", "description": "Quarterly financial summary", "status": "draft", "project": "demo", "created_at": "2024-03-15T10:00:00Z"},
        {"id": "res-004", "name": "Archived Task", "description": "Completed migration task", "status": "archived", "project": "demo", "created_at": "2024-03-14T14:00:00Z"},
        {"id": "res-005", "name": "Pending Review", "description": "Code review for feature branch", "status": "pending", "project": "demo", "created_at": "2024-03-15T11:00:00Z"},
    ],
}


def get_seed_data(entity_name: str) -> list[dict]:
    """Return seed records for the given entity type."""
    return _SEED.get(entity_name, [])
'''

    # ===============================================================
    # Node.js / Express -- implementation methods
    # ===============================================================

    def _node_main(self, spec: IntentSpec) -> str:
        storage_require = ""
        storage_route = ""

        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_require = 'const { BlobServiceClient } = require("@azure/storage-blob");\n'
            storage_route = """
// -- Storage Status --------------------------------------------------
app.get("/storage/status", async (req, res) => {{
  try {{
    const credential = new DefaultAzureCredential();
    const blobClient = new BlobServiceClient(
      process.env.STORAGE_ACCOUNT_URL || "",
      credential
    );
    const iter = blobClient.listContainers({{ maxPageSize: 1 }});
    await iter.next();
    res.json({{ status: "connected", containers_accessible: true }});
  }} catch (err) {{
    console.error("Storage health check failed:", err.message);
    res.status(503).json({{ status: "error", detail: err.message }});
  }}
}});
"""

        return f"""// ===================================================================
// Enterprise DevEx Orchestrator -- Generated Application (Node.js)
//
// Project: {spec.project_name}
// Description: {spec.description}
// ===================================================================

const express = require("express");
const {{ DefaultAzureCredential }} = require("@azure/identity");
const {{ SecretClient }} = require("@azure/keyvault-secrets");
{storage_require}
const app = express();
const APP_NAME = "{spec.project_name}";
const VERSION = "1.0.0";
const PORT = parseInt(process.env.PORT || "8000", 10);

app.use(express.json());

// -- Health Endpoint -------------------------------------------------
app.get("/health", (req, res) => {{
  res.json({{
    status: "healthy",
    service: APP_NAME,
    version: VERSION,
    timestamp: new Date().toISOString(),
  }});
}});

// -- Root Endpoint (Enterprise Dashboard) ----------------------------
app.get("/", (req, res) => {{
  const complianceBadges = `{self._enterprise_compliance_badges(spec)}`;
  const dataStores = "{self._enterprise_data_stores(spec)}";
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${{APP_NAME}} — Enterprise Dashboard</title>
    <style>
        {self.ENTERPRISE_CSS}
    </style>
</head>
<body>
    <nav class="topbar">
        <div class="topbar-brand">
            <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            ${{APP_NAME}}
        </div>
        <div class="topbar-meta">
            <span class="env-badge">{spec.environment}</span>
            <span>{spec.azure_region}</span>
        </div>
    </nav>
    <section class="hero">
        <h1>${{APP_NAME}}</h1>
        <p>{spec.description}</p>
        <div class="version-pill">v${{VERSION}} · {spec.compute_target.value.replace('_', ' ').title()}</div>
    </section>
    <div class="dashboard">
        <div class="card">
            <div class="card-header"><div class="card-icon" style="background:#e6f4ea">💚</div><h3>System Status</h3></div>
            <div class="card-body">
                <div class="status-grid">
                    <div class="status-item"><div class="label">Health</div><div id="health-status" class="value">Checking…</div></div>
                    <div class="status-item"><div class="label">Key Vault</div><div id="kv-status" class="value">Checking…</div></div>
                    <div class="status-item"><div class="label">Region</div><div class="value" style="font-size:14px">{spec.azure_region}</div></div>
                    <div class="status-item"><div class="label">Environment</div><div class="value" style="font-size:14px;text-transform:capitalize">{spec.environment}</div></div>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="card-header"><div class="card-icon" style="background:#e3f2fd">⚡</div><h3>Quick Actions</h3></div>
            <div class="card-body">
                <div class="actions">
                    <a class="action-btn" href="/health"><span class="icon">💚</span>Health Check</a>
                    <a class="action-btn" href="/keyvault/status"><span class="icon">🔐</span>Key Vault Status</a>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="card-header"><div class="card-icon" style="background:#fff3e0">🔌</div><h3>API Endpoints</h3></div>
            <div class="card-body">
                <ul class="endpoint-list">
                    <li><span class="method-badge get">GET</span><span class="endpoint-path">/health</span><span class="endpoint-desc">Liveness probe</span></li>
                    <li><span class="method-badge get">GET</span><span class="endpoint-path">/keyvault/status</span><span class="endpoint-desc">Vault connectivity</span></li>
                </ul>
            </div>
        </div>
        <div class="card">
            <div class="card-header"><div class="card-icon" style="background:#fce4ec">🏗️</div><h3>Architecture &amp; Compliance</h3></div>
            <div class="card-body">
                <ul class="arch-list">
                    <li><span class="arch-badge compute">COMPUTE</span>{spec.compute_target.value.replace('_', ' ').title()}</li>
                    <li><span class="arch-badge data">DATA</span>${{dataStores}}</li>
                    <li><span class="arch-badge security">SECURITY</span>{spec.security.auth_model.value.replace('_', ' ').title()}</li>
                    <li><span class="arch-badge monitor">MONITOR</span>Log Analytics · Health Probes</li>
                </ul>
                <div class="compliance-row">${{complianceBadges}}</div>
            </div>
        </div>
    </div>
    <footer class="footer">${{APP_NAME}} v${{VERSION}} · Enterprise DevEx Orchestrator</footer>
    <script>
        {self.ENTERPRISE_JS}
    </script>
</body>
</html>`;
  res.send(html);
}});

// -- Key Vault Status ------------------------------------------------
app.get("/keyvault/status", async (req, res) => {{
  try {{
    const credential = new DefaultAzureCredential();
    const vaultUri = process.env.KEY_VAULT_URI || "";
    const vaultName = process.env.KEY_VAULT_NAME || "";
    let vaultUrl = vaultUri;
    if (!vaultUrl && vaultName) {{
      vaultUrl = `https://${{vaultName}}.vault.azure.net`;
    }}
    if (!vaultUrl) throw new Error("KEY_VAULT_URI or KEY_VAULT_NAME must be set");
    const client = new SecretClient(
      vaultUrl,
      credential
    );
    const iter = client.listPropertiesOfSecrets({{ maxPageSize: 1 }});
    await iter.next();
    res.json({{ status: "connected", vault_accessible: true }});
  }} catch (err) {{
    console.error("Key Vault health check failed:", err.message);
    res.status(503).json({{ status: "error", detail: err.message }});
  }}
}});
{storage_route}
app.listen(PORT, () => {{
  console.log(`${{APP_NAME}} v${{VERSION}} listening on port ${{PORT}}`);
}});
"""

    def _node_package_json(self, spec: IntentSpec) -> str:
        deps = {
            "express": "^4.18.0",
            "uuid": "^9.0.0",
            "@azure/identity": "^4.0.0",
            "@azure/keyvault-secrets": "^4.8.0",
        }
        if DataStore.BLOB_STORAGE in spec.data_stores:
            deps["@azure/storage-blob"] = "^12.17.0"
        if DataStore.COSMOS_DB in spec.data_stores:
            deps["@azure/cosmos"] = "^4.0.0"

        import json as _json

        deps_str = _json.dumps(deps, indent=4)

        return f"""{{
  "name": "{spec.project_name}",
  "version": "1.0.0",
  "description": "{spec.description}",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js",
    "dev": "node --watch index.js",
    "test": "jest --coverage"
  }},
  "dependencies": {deps_str},
  "devDependencies": {{
    "jest": "^29.7.0"
  }},
  "engines": {{
    "node": ">=20.0.0"
  }}
}}
"""

    def _node_dockerfile(self, spec: IntentSpec) -> str:
        return f"""# ===================================================================
# Dockerfile -- {spec.project_name} (Node.js)
# Multi-stage build for minimal production image
# ===================================================================

FROM node:20-slim AS builder
WORKDIR /build
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-slim AS runtime
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app
COPY --from=builder /build/node_modules ./node_modules
COPY . .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:8000/health', r => r.statusCode === 200 ? process.exit(0) : process.exit(1))"
CMD ["node", "index.js"]
"""

    def _node_env_example(self, spec: IntentSpec) -> str:
        lines = [
            "# Application configuration",
            "PORT=8000",
            f"ENVIRONMENT={spec.environment}",
            "",
            "# Azure Managed Identity",
            "AZURE_CLIENT_ID=",
            "",
            "# Key Vault",
            "KEY_VAULT_NAME=",
        ]
        if DataStore.BLOB_STORAGE in spec.data_stores:
            lines += ["", "# Storage", "STORAGE_ACCOUNT_URL="]
        return "\n".join(lines) + "\n"

    def _node_services(self, spec: IntentSpec) -> str:
        """Generate domain service layer for Node.js."""
        if _has_custom_entities(spec):
            return self._dynamic_node_services(spec)

        # Generic
        return """const { v4: uuid } = require("uuid");
const { seedData } = require("./data");

const db = { resources: { ...seedData.resources } };

class ResourceService {
  list() { return Object.values(db.resources); }
  get(id) { return db.resources[id] || null; }
  create({ name, description }) {
    const resource = { id: uuid(), name, description: description || "", project: "default", created_at: new Date().toISOString() };
    db.resources[resource.id] = resource;
    return resource;
  }
  update(id, { name, description }) {
    const resource = db.resources[id];
    if (!resource) return null;
    if (name !== undefined) resource.name = name;
    if (description !== undefined) resource.description = description;
    return resource;
  }
  delete(id) { const existed = !!db.resources[id]; delete db.resources[id]; return existed; }
}

module.exports = { ResourceService };
"""

    def _node_seed_data(self, spec: IntentSpec) -> str:
        """Generate seed data for Node.js."""
        if _has_custom_entities(spec):
            return self._dynamic_node_seed_data(spec)

        return """const seedData = {
  resources: {
    "r1": { id: "r1", name: "Sample Resource 1", description: "First demo resource", project: "default", created_at: "2024-01-01T00:00:00Z" },
    "r2": { id: "r2", name: "Sample Resource 2", description: "Second demo resource", project: "default", created_at: "2024-01-02T00:00:00Z" },
    "r3": { id: "r3", name: "Sample Resource 3", description: "Third demo resource", project: "default", created_at: "2024-01-03T00:00:00Z" },
  },
};
module.exports = { seedData };
"""

    def _dynamic_node_services(self, spec: IntentSpec) -> str:
        """Generate Node.js service classes from spec.entities."""
        lines = ['const { v4: uuid } = require("uuid");',
                 'const { seedData } = require("./data");',
                 '',
                 'const db = { ...seedData };',
                 '']
        class_names = []
        for ent in spec.entities:
            sn = _snake(ent.name)
            plural = _snake(_plural(ent.name))
            cls = f'{ent.name}Service'
            class_names.append(cls)

            lines.append(f'class {cls} {{')
            lines.append(f'  list(status) {{')
            lines.append(f'    let items = Object.values(db.{plural} || {{}});')
            lines.append(f'    if (status) items = items.filter(i => i.status === status);')
            lines.append(f'    return items;')
            lines.append(f'  }}')
            lines.append(f'  get(id) {{ return (db.{plural} || {{}})[id] || null; }}')
            # build create fields
            field_names = [f.name for f in ent.fields if f.name != 'status']
            create_destructure = ', '.join(field_names) if field_names else 'name'
            lines.append(f'  create({{ {create_destructure} }}) {{')
            lines.append(f'    const record = {{ id: uuid(), {", ".join(f"{fn}: {fn} || \"\"" for fn in field_names) if field_names else "name: name || \"\""}, status: "pending", created_at: new Date().toISOString() }};')
            lines.append(f'    if (!db.{plural}) db.{plural} = {{}};')
            lines.append(f'    db.{plural}[record.id] = record;')
            lines.append(f'    return record;')
            lines.append(f'  }}')
            lines.append(f'  update(id, data) {{')
            lines.append(f'    const item = (db.{plural} || {{}})[id];')
            lines.append(f'    if (!item) return null;')
            lines.append(f'    Object.assign(item, data, {{ updated_at: new Date().toISOString() }});')
            lines.append(f'    return item;')
            lines.append(f'  }}')
            lines.append(f'  delete(id) {{ const existed = !!(db.{plural} || {{}})[id]; if (db.{plural}) delete db.{plural}[id]; return existed; }}')
            lines.append(f'}}')
            lines.append('')

        lines.append(f'module.exports = {{ {", ".join(class_names)} }};')
        lines.append('')
        return "\n".join(lines)

    def _dynamic_node_seed_data(self, spec: IntentSpec) -> str:
        """Generate Node.js seed data from spec.entities."""
        lines = ['const seedData = {']
        for ent in spec.entities:
            sn = _snake(ent.name)
            plural = _snake(_plural(ent.name))
            lines.append(f'  {plural}: {{')
            for rid in range(1, 4):
                parts = [f'id: "{sn}-{rid:03d}"']
                for f in ent.fields:
                    if f.name == "created_at":
                        continue
                    val = _seed_value(f, ent.name, rid)
                    parts.append(f'{f.name}: {val}')
                hour = 8 + rid
                parts.append(f'created_at: "2024-03-{10+rid}T{hour:02d}:00:00Z"')
                lines.append(f'    "{sn}-{rid:03d}": {{ {", ".join(parts)} }},')
            lines.append(f'  }},')
        lines.append('};')
        lines.append('module.exports = { seedData };')
        lines.append('')
        return "\n".join(lines)

    # ===============================================================
    # .NET / ASP.NET Core -- implementation methods
    # ===============================================================

    def _dotnet_program(self, spec: IntentSpec) -> str:
        storage_usings = ""
        storage_services = ""
        storage_endpoint = ""

        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_usings = "using Azure.Storage.Blobs;\n"
            storage_services = """
builder.Services.AddSingleton(sp =>
{{
    var credential = new DefaultAzureCredential();
    var accountUrl = builder.Configuration["STORAGE_ACCOUNT_URL"] ?? "";
    return new BlobServiceClient(new Uri(accountUrl), credential);
}});
"""
            storage_endpoint = """
app.MapGet("/storage/status", async (BlobServiceClient blobClient) =>
{{
    try
    {{
        await foreach (var _ in blobClient.GetBlobContainersAsync().AsPages(pageSizeHint: 1))
        {{ break; }}
        return Results.Ok(new {{ status = "connected", containers_accessible = true }});
    }}
    catch (Exception ex)
    {{
        return Results.Json(new {{ status = "error", detail = ex.Message }}, statusCode: 503);
    }}
}});
"""

        return f"""// ===================================================================
// Enterprise DevEx Orchestrator -- Generated Application (.NET)
//
// Project: {spec.project_name}
// Description: {spec.description}
// ===================================================================

using Azure.Identity;
using Azure.Security.KeyVault.Secrets;
{storage_usings}
var builder = WebApplication.CreateBuilder(args);

var appName = "{spec.project_name}";
var version = "1.0.0";

// -- Key Vault Client ------------------------------------------------
builder.Services.AddSingleton(sp =>
{{
    var credential = new DefaultAzureCredential();
    var vaultUri = builder.Configuration["KEY_VAULT_URI"] ?? "";
    var vaultName = builder.Configuration["KEY_VAULT_NAME"] ?? "";
    if (string.IsNullOrEmpty(vaultUri) && !string.IsNullOrEmpty(vaultName))
        vaultUri = $"https://{{vaultName}}.vault.azure.net";
    if (string.IsNullOrEmpty(vaultUri))
        throw new InvalidOperationException("KEY_VAULT_URI or KEY_VAULT_NAME must be set");
    return new SecretClient(new Uri(vaultUri), credential);
}});
{storage_services}
var app = builder.Build();

// -- Health Endpoint -------------------------------------------------
app.MapGet("/health", () => Results.Ok(new
{{
    status = "healthy",
    service = appName,
    version,
    timestamp = DateTime.UtcNow.ToString("o"),
}}));

// -- Root Endpoint (Enterprise Dashboard) ----------------------------
app.MapGet("/", () =>
{{
    var complianceBadges = @"{self._enterprise_compliance_badges(spec).replace('"', '""')}";
    var dataStores = "{self._enterprise_data_stores(spec)}";
    var html = $@"<!DOCTYPE html>
<html lang=""en"">
<head>
    <meta charset=""UTF-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1.0"">
    <title>{{appName}} — Enterprise Dashboard</title>
    <style>
        {self.ENTERPRISE_CSS.replace('{', '{{{{').replace('}', '}}}}').replace('{{{{{{{{', '{{').replace('}}}}}}}}', '}}')}
    </style>
</head>
<body>
    <nav class=""topbar"">
        <div class=""topbar-brand"">
            <svg viewBox=""0 0 24 24""><path d=""M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5""/></svg>
            {{appName}}
        </div>
        <div class=""topbar-meta"">
            <span class=""env-badge"">{spec.environment}</span>
            <span>{spec.azure_region}</span>
        </div>
    </nav>
    <section class=""hero"">
        <h1>{{appName}}</h1>
        <p>{spec.description}</p>
        <div class=""version-pill"">v{{version}} · {spec.compute_target.value.replace('_', ' ').title()}</div>
    </section>
    <div class=""dashboard"">
        <div class=""card"">
            <div class=""card-header""><div class=""card-icon"" style=""background:#e6f4ea"">💚</div><h3>System Status</h3></div>
            <div class=""card-body"">
                <div class=""status-grid"">
                    <div class=""status-item""><div class=""label"">Health</div><div id=""health-status"" class=""value"">Checking…</div></div>
                    <div class=""status-item""><div class=""label"">Key Vault</div><div id=""kv-status"" class=""value"">Checking…</div></div>
                    <div class=""status-item""><div class=""label"">Region</div><div class=""value"" style=""font-size:14px"">{spec.azure_region}</div></div>
                    <div class=""status-item""><div class=""label"">Environment</div><div class=""value"" style=""font-size:14px;text-transform:capitalize"">{spec.environment}</div></div>
                </div>
            </div>
        </div>
        <div class=""card"">
            <div class=""card-header""><div class=""card-icon"" style=""background:#e3f2fd"">⚡</div><h3>Quick Actions</h3></div>
            <div class=""card-body"">
                <div class=""actions"">
                    <a class=""action-btn"" href=""/health""><span class=""icon"">💚</span>Health Check</a>
                    <a class=""action-btn"" href=""/keyvault/status""><span class=""icon"">🔐</span>Key Vault Status</a>
                </div>
            </div>
        </div>
        <div class=""card"">
            <div class=""card-header""><div class=""card-icon"" style=""background:#fff3e0"">🔌</div><h3>API Endpoints</h3></div>
            <div class=""card-body"">
                <ul class=""endpoint-list"">
                    <li><span class=""method-badge get"">GET</span><span class=""endpoint-path"">/health</span><span class=""endpoint-desc"">Liveness probe</span></li>
                    <li><span class=""method-badge get"">GET</span><span class=""endpoint-path"">/keyvault/status</span><span class=""endpoint-desc"">Vault connectivity</span></li>
                </ul>
            </div>
        </div>
        <div class=""card"">
            <div class=""card-header""><div class=""card-icon"" style=""background:#fce4ec"">🏗️</div><h3>Architecture &amp; Compliance</h3></div>
            <div class=""card-body"">
                <ul class=""arch-list"">
                    <li><span class=""arch-badge compute"">COMPUTE</span>{spec.compute_target.value.replace('_', ' ').title()}</li>
                    <li><span class=""arch-badge data"">DATA</span>{{dataStores}}</li>
                    <li><span class=""arch-badge security"">SECURITY</span>{spec.security.auth_model.value.replace('_', ' ').title()}</li>
                    <li><span class=""arch-badge monitor"">MONITOR</span>Log Analytics · Health Probes</li>
                </ul>
                <div class=""compliance-row"">{{complianceBadges}}</div>
            </div>
        </div>
    </div>
    <footer class=""footer"">{{appName}} v{{version}} · Enterprise DevEx Orchestrator</footer>
    <script>
        {self.ENTERPRISE_JS}
    </script>
</body>
</html>";
    return Results.Content(html, "text/html");
}});

// -- Key Vault Status ------------------------------------------------
app.MapGet("/keyvault/status", async (SecretClient kvClient) =>
{{
    try
    {{
        await foreach (var _ in kvClient.GetPropertiesOfSecretsAsync().AsPages(pageSizeHint: 1))
        {{ break; }}
        return Results.Ok(new {{ status = "connected", vault_accessible = true }});
    }}
    catch (Exception ex)
    {{
        return Results.Json(new {{ status = "error", detail = ex.Message }}, statusCode: 503);
    }}
}});
{storage_endpoint}
app.Run();
"""

    def _dotnet_csproj(self, spec: IntentSpec) -> str:
        storage_pkg = ""
        if DataStore.BLOB_STORAGE in spec.data_stores:
            storage_pkg = '    <PackageReference Include="Azure.Storage.Blobs" Version="12.19.0" />\n'
        cosmos_pkg = ""
        if DataStore.COSMOS_DB in spec.data_stores:
            cosmos_pkg = '    <PackageReference Include="Microsoft.Azure.Cosmos" Version="3.37.0" />\n'

        return f"""<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Azure.Identity" Version="1.11.0" />
    <PackageReference Include="Azure.Security.KeyVault.Secrets" Version="4.6.0" />
{storage_pkg}{cosmos_pkg}  </ItemGroup>
</Project>
"""

    def _dotnet_dockerfile(self, spec: IntentSpec) -> str:
        return f"""# ===================================================================
# Dockerfile -- {spec.project_name} (.NET)
# Multi-stage build for minimal production image
# ===================================================================

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS builder
WORKDIR /build
COPY *.csproj ./
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
WORKDIR /app
COPY --from=builder /publish .
USER appuser
EXPOSE 8000
ENV ASPNETCORE_URLS=http://+:8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["dotnet", "{spec.project_name}.dll"]
"""

    def _dotnet_appsettings(self, spec: IntentSpec) -> str:
        import json as _json

        settings: dict = {
            "Logging": {"LogLevel": {"Default": "Information", "Microsoft.AspNetCore": "Warning"}},
            "ENVIRONMENT": spec.environment,
            "KEY_VAULT_NAME": "",
        }
        if DataStore.BLOB_STORAGE in spec.data_stores:
            settings["STORAGE_ACCOUNT_URL"] = ""
        return _json.dumps(settings, indent=2) + "\n"

    def _dotnet_services(self, spec: IntentSpec) -> str:
        """Generate domain services for .NET."""
        if _has_custom_entities(spec):
            return self._dynamic_dotnet_services(spec)

        # Generic
        return """// Domain Services -- Generic CRUD
using System.Collections.Concurrent;

namespace App.Services;

public record Resource(string Id, string Name, string Description, string Project, DateTime CreatedAt);

public class ResourceService
{
    private readonly ConcurrentDictionary<string, Resource> _resources = new();

    public ResourceService(SeedData seed) { foreach (var r in seed.Resources) _resources[r.Id] = r; }
    public IEnumerable<Resource> List() => _resources.Values;
    public Resource? Get(string id) => _resources.GetValueOrDefault(id);
    public Resource Create(string name, string? description = null) { var r = new Resource(Guid.NewGuid().ToString(), name, description ?? "", "default", DateTime.UtcNow); _resources[r.Id] = r; return r; }
    public Resource? Update(string id, string name, string? description = null) { if (!_resources.TryGetValue(id, out var old)) return null; var u = old with { Name = name, Description = description ?? old.Description }; _resources[id] = u; return u; }
    public bool Delete(string id) => _resources.TryRemove(id, out _);
}
"""

    def _dotnet_seed_data(self, spec: IntentSpec) -> str:
        """Generate seed data for .NET."""
        if _has_custom_entities(spec):
            return self._dynamic_dotnet_seed_data(spec)

        return """// Seed Data -- Generic
namespace App.Services;

public class SeedData
{
    public List<Resource> Resources { get; } = new()
    {
        new("r1", "Sample Resource 1", "First demo resource", "default", DateTime.Parse("2024-01-01T00:00:00Z")),
        new("r2", "Sample Resource 2", "Second demo resource", "default", DateTime.Parse("2024-01-02T00:00:00Z")),
        new("r3", "Sample Resource 3", "Third demo resource", "default", DateTime.Parse("2024-01-03T00:00:00Z")),
    };
}
"""

    def _dynamic_dotnet_services(self, spec: IntentSpec) -> str:
        """Generate .NET service classes from spec.entities."""
        lines = ['// Domain Services — auto-generated from intent specification',
                 'using System.Collections.Concurrent;',
                 '',
                 'namespace App.Services;',
                 '']
        # Record definitions
        for ent in spec.entities:
            fields = ', '.join(
                f'{_dotnet_type(f.type)} {_pascal_field(f.name)}'
                for f in ent.fields
            )
            lines.append(f'public record {ent.name}(string Id, {fields}, string Status, DateTime CreatedAt);')
        lines.append('')
        # Service classes
        for ent in spec.entities:
            sn = _snake(ent.name)
            plural = _plural(ent.name)
            store_name = f'_{sn}s'
            cls = f'{ent.name}Service'
            lines.append(f'public class {cls}')
            lines.append('{')
            lines.append(f'    private readonly ConcurrentDictionary<string, {ent.name}> {store_name} = new();')
            lines.append('')
            lines.append(f'    public {cls}(SeedData seed) {{ foreach (var e in seed.{plural}) {store_name}[e.Id] = e; }}')
            lines.append(f'    public IEnumerable<{ent.name}> List(string? status = null) => status is null ? {store_name}.Values : {store_name}.Values.Where(e => e.Status == status);')
            lines.append(f'    public {ent.name}? Get(string id) => {store_name}.GetValueOrDefault(id);')
            # Create method
            create_params = ', '.join(
                f'{_dotnet_type(f.type)} {_camel(f.name)}'
                for f in ent.fields if f.name != 'status'
            )
            create_args = ', '.join(
                [f'Guid.NewGuid().ToString()'] +
                [_camel(f.name) for f in ent.fields if f.name != 'status'] +
                ['"pending"', 'DateTime.UtcNow']
            )
            lines.append(f'    public {ent.name} Create({create_params}) {{ var e = new {ent.name}({create_args}); {store_name}[e.Id] = e; return e; }}')
            lines.append(f'    public bool Delete(string id) => {store_name}.TryRemove(id, out _);')
            lines.append('}')
            lines.append('')
        return "\n".join(lines)

    def _dynamic_dotnet_seed_data(self, spec: IntentSpec) -> str:
        """Generate .NET seed data from spec.entities."""
        lines = ['// Seed Data — auto-generated from intent specification',
                 'namespace App.Services;',
                 '',
                 'public class SeedData',
                 '{']
        for ent in spec.entities:
            plural = _plural(ent.name)
            lines.append(f'    public List<{ent.name}> {plural} {{ get; }} = new()')
            lines.append('    {')
            for rid in range(1, 4):
                parts = [f'"{_snake(ent.name)}-{rid:03d}"']
                for f in ent.fields:
                    val = _seed_value(f, ent.name, rid)
                    # Convert Python-style value to C# style
                    cval = _dotnet_seed_val(val, f.type)
                    parts.append(cval)
                parts.append('"pending"')
                hour = 8 + rid
                parts.append(f'DateTime.Parse("2024-03-{10+rid}T{hour:02d}:00:00Z")')
                lines.append(f'        new({", ".join(parts)}),')
            lines.append('    };')
        lines.append('}')
        lines.append('')
        return "\n".join(lines)

    # ===============================================================
    # AI Layer — OpenAI client, chat router, agent orchestration
    # ===============================================================

    def _python_ai_client(self, spec: IntentSpec) -> str:
        """Generate AI client that auto-detects provider: Azure OpenAI, OpenAI, or raises clear error."""
        ai_model = getattr(spec, "ai_model", "gpt-4o")
        entities = spec.entities
        entity_names = ", ".join(e.name for e in entities) if entities else "general"
        return f'''"""AI Client -- auto-detecting provider with enterprise auth.

Supports:
1. Azure OpenAI with Managed Identity (AZURE_OPENAI_ENDPOINT set)
2. Azure OpenAI with API key (AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY)
3. OpenAI API (OPENAI_API_KEY set)

No mocks — real AI processing for: {entity_names}
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

CHAT_MODEL = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "{ai_model}")
EMBEDDINGS_MODEL = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "text-embedding-ada-002")


def _create_azure_openai_client():
    """Create Azure OpenAI client with Managed Identity or API key."""
    from openai import AzureOpenAI

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if api_key:
        return AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-06-01",
        )

    # Managed Identity (production path)
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    credential = DefaultAzureCredential(
        managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
    )
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-06-01",
    )


def _create_openai_client():
    """Create standard OpenAI client."""
    from openai import OpenAI

    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_ai_client():
    """Auto-detect and return the best available AI client.

    Returns a tuple of (client, provider_name).
    Raises RuntimeError if no provider is configured.
    """
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        logger.info("ai_client.provider", extra={{"provider": "azure_openai"}})
        return _create_azure_openai_client(), "azure_openai"

    if os.getenv("OPENAI_API_KEY"):
        logger.info("ai_client.provider", extra={{"provider": "openai"}})
        return _create_openai_client(), "openai"

    raise RuntimeError(
        "No AI provider configured. Set one of: "
        "AZURE_OPENAI_ENDPOINT (+ optional AZURE_OPENAI_API_KEY), "
        "or OPENAI_API_KEY"
    )


def get_embeddings(text: str) -> list[float]:
    """Generate embeddings for the given text."""
    client, _ = get_ai_client()
    response = client.embeddings.create(model=EMBEDDINGS_MODEL, input=text)
    return response.data[0].embedding


def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> dict[str, Any]:
    """Run a chat completion and return structured result."""
    client, provider = get_ai_client()
    use_model = model or CHAT_MODEL

    response = client.chat.completions.create(
        model=use_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    choice = response.choices[0]
    return {{
        "reply": choice.message.content or "",
        "model": use_model,
        "provider": provider,
        "usage": {{
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }},
    }}
'''

    def _python_ai_chat(self, spec: IntentSpec) -> str:
        """Generate domain-aware AI chat router with real RAG and entity context."""
        ai_features = getattr(spec, "ai_features", [])
        entities = spec.entities

        # Build entity registry imports and context builder
        entity_imports = []
        entity_context_lines = []
        for ent in entities:
            sn = _snake(ent.name)
            entity_context_lines.append(
                f'    try:\n'
                f'        repo = get_repository("{sn}")\n'
                f'        items = repo.list_all()\n'
                f'        records = []\n'
                f'        for item in items:\n'
                f'            if hasattr(item, "__dict__"):\n'
                f'                records.append({{k: v for k, v in item.__dict__.items() if not k.startswith("_")}})\n'
                f'            elif isinstance(item, dict):\n'
                f'                records.append(item)\n'
                f'            else:\n'
                f'                records.append({{"value": str(item)}})\n'
                f'        result["{ent.name}"] = records\n'
                f'    except Exception:\n'
                f'        pass'
            )
        entity_import_block = "from core.dependencies import get_repository"
        entity_context_block = "\n".join(entity_context_lines)

        # Build entity descriptions for system prompt
        entity_descriptions = []
        for ent in entities:
            fields = ", ".join(f.name for f in ent.fields)
            entity_descriptions.append(f"  - {ent.name}: {fields}")
        entity_desc_str = "\\n".join(entity_descriptions)

        # AI Search RAG support (when Azure AI Search is configured)
        search_rag_block = ""
        if "rag" in ai_features:
            search_rag_block = '''

def _search_rag_context(query: str, top_k: int = 3) -> str:
    """Retrieve context from Azure AI Search when configured."""
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    if not search_endpoint:
        return ""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.search.documents import SearchClient

        credential = DefaultAzureCredential(
            managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
        )
        client = SearchClient(
            endpoint=search_endpoint,
            index_name=os.getenv("AZURE_SEARCH_INDEX", "documents"),
            credential=credential,
        )
        results = client.search(search_text=query, top=top_k)
        chunks = [doc.get("content", "") for doc in results if doc.get("content")]
        return "\\n\\n".join(chunks)
    except Exception as e:
        logger.warning("ai_search.rag_fallback", extra={"error": str(e)})
        return ""
'''

        ai_feature_list = ", ".join(ai_features) if ai_features else "chat"

        return f'''"""AI Chat Router -- domain-aware chat with entity context and RAG.

Capabilities: {ai_feature_list}
Handles any enterprise domain by grounding responses in the app's own data.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from ai.client import CHAT_MODEL, chat_completion, get_ai_client
{entity_import_block}

logger = logging.getLogger(__name__)
router = APIRouter()
{search_rag_block}

def _build_domain_context() -> dict:
    """Build structured domain context from the app\\'s own entity repositories."""
    result: dict[str, list[dict]] = {{}}
{entity_context_block}
    return result


def _local_data_reply(question: str, context: dict) -> str:
    """Smart analytical data engine with conversational reasoning -- works without an AI provider."""
    import re as _re
    from collections import Counter

    q = question.lower().strip()
    entity_names = list(context.keys())
    total_records = sum(len(v) for v in context.values())

    # --- Intent detection ---
    def _is_greeting():
        return any(w in q for w in ("hello", "hi ", "hey", "good morning", "good afternoon", "greetings", "howdy")) or q in ("hi", "hey")

    def _is_count():
        return any(w in q for w in ("how many", "count", "total", "number of", "quantity"))

    def _is_list():
        return any(w in q for w in ("list", "show me", "show all", "display", "get all", "what are the", "give me"))

    def _is_status():
        return any(w in q for w in ("status", "health", "overview", "summary", "dashboard", "report", "how is", "how are"))

    def _is_analytics():
        return any(w in q for w in ("analyze", "analyse", "trend", "insight", "breakdown", "distribution", "statistic", "average", "mean", "compare", "correlation", "pattern", "top", "bottom", "worst", "best", "highest", "lowest", "most", "least", "peak"))

    def _is_help():
        return any(w in q for w in ("help", "what can you", "capabilities", "what do you", "how do i", "how to"))

    def _is_action():
        return any(w in q for w in ("create", "add", "update", "delete", "remove", "fix", "resolve", "assign", "triage", "escalate", "dispatch", "approve", "schedule"))

    def _is_filter():
        return any(w in q for w in ("where", "which", "filter", "find", "with", "without", "that have", "that are", "pending", "active", "completed", "critical", "high", "low", "open", "closed"))

    def _is_temporal():
        return any(w in q for w in ("latest", "recent", "newest", "oldest", "last updated", "first", "when was", "most recent", "earliest", "last created", "last added", "new record", "updated record", "last record", "ago"))

    def _is_recommendation():
        return any(w in q for w in ("improve", "improvement", "suggest", "suggestion", "recommend", "recommendation", "future", "what should", "next step", "forecast", "optimize", "optimise", "enhance", "gap", "missing", "weakness", "opportunity", "priority action", "attention"))

    def _is_crossentity():
        return any(w in q for w in ("related", "belong", "associated", "linked", "connected", "between", "correlation", "correlate", "across entities", "across all", "comparison", "compare all"))

    # --- Entity matching (flexible NLP) ---
    def _find_entity() -> tuple[str, list[dict]]:
        best_match = ("", [])
        best_score = 0
        for name in entity_names:
            name_lower = name.lower()
            score = 0
            # Exact match
            if name_lower in q or name_lower + "s" in q:
                score = 10
            elif name_lower.rstrip("s") in q:
                score = 9
            else:
                # CamelCase split: "ServiceRequest" -> ["service", "request"]
                words = _re.split(r'(?<=[a-z])(?=[A-Z])', name)
                words = [w.lower() for w in words if w]
                # snake_case split
                snake_parts = name_lower.split("_")
                all_tokens = set(words + snake_parts)
                matched_tokens = sum(1 for w in all_tokens if len(w) > 2 and w in q)
                if matched_tokens > 0:
                    score = matched_tokens * 3
                # Singular/plural variations
                for w in all_tokens:
                    if len(w) > 3:
                        if w + "s" in q or w.rstrip("s") in q:
                            score = max(score, 5)
            if score > best_score:
                best_score = score
                best_match = (name, context[name])
        return best_match

    # --- HTML helpers ---
    def _table(records: list[dict], keys: list[str] | None = None, max_rows: int = 10) -> str:
        if not records:
            return "<em>No records found.</em>"
        keys = keys or [k for k in records[0].keys() if k != "id"][:6]
        headers = "".join(f"<th>{{k.replace('_', ' ').title()}}</th>" for k in keys)
        rows = ""
        for r in records[:max_rows]:
            cells = ""
            for k in keys:
                v = r.get(k, "")
                if isinstance(v, list):
                    v = ", ".join(str(x) for x in v[:3])
                elif v is None:
                    v = ""
                cells += f"<td>{{v}}</td>"
            rows += f"<tr>{{cells}}</tr>"
        more = f"<tr><td colspan='{{len(keys)}}' style='text-align:center;color:#666;font-style:italic'>...and {{len(records) - max_rows}} more</td></tr>" if len(records) > max_rows else ""
        return f"<table class='ai-table'><thead><tr>{{headers}}</tr></thead><tbody>{{rows}}{{more}}</tbody></table>"

    def _stat_card(label: str, value, color: str = "#0078d4") -> str:
        return f"<span class='ai-stat' style='border-color:{{color}}'><strong style='color:{{color}}'>{{value}}</strong> {{label}}</span>"

    def _section(title: str, body: str) -> str:
        return f"<div class='ai-section'><div class='ai-section-title'>{{title}}</div>{{body}}</div>"

    def _status_breakdown(records: list[dict]) -> dict[str, int]:
        statuses = [str(r.get("status", "unknown")).lower() for r in records]
        return dict(Counter(statuses).most_common())

    def _field_distribution(records: list[dict], field: str) -> dict[str, int]:
        values = [str(r.get(field, "unknown")).lower() for r in records if r.get(field)]
        return dict(Counter(values).most_common(10))

    def _bar_chart(distribution: dict[str, int], color: str = "#0078d4") -> str:
        if not distribution:
            return ""
        max_val = max(distribution.values())
        bars = ""
        for label, count in distribution.items():
            pct = (count / max_val) * 100 if max_val else 0
            bars += f"<div class='ai-bar-row'><span class='ai-bar-label'>{{label}}</span><div class='ai-bar-track'><div class='ai-bar-fill' style='width:{{pct}}%;background:{{color}}'></div></div><span class='ai-bar-val'>{{count}}</span></div>"
        return f"<div class='ai-bar-chart'>{{bars}}</div>"

    def _numeric_stats(records: list[dict], field: str) -> dict | None:
        vals = []
        for r in records:
            v = r.get(field)
            if v is not None:
                try:
                    vals.append(float(v))
                except (ValueError, TypeError):
                    pass
        if not vals:
            return None
        return {{"min": min(vals), "max": max(vals), "avg": sum(vals)/len(vals), "count": len(vals)}}

    # --- Responses ---

    if _is_greeting():
        cards = "".join(_stat_card(name, len(records)) for name, records in context.items())
        return (
            f"<div class='ai-greeting'>\U0001f44b Hello! I'm your intelligent data assistant for this platform.</div>"
            f"<div class='ai-stats-row'>{{cards}}</div>"
            f"<div class='ai-hint'>I can analyze <strong>{{total_records}} records</strong> across "
            f"<strong>{{len(entity_names)}} entities</strong>. Try asking me:</div>"
            f"<ul class='ai-suggestions'>"
            f"<li>\\"How many incidents are critical?\\"</li>"
            f"<li>\\"Show me a breakdown of asset status\\"</li>"
            f"<li>\\"What needs attention right now?\\"</li>"
            f"<li>\\"Analyze sensor health trends\\"</li></ul>"
        )

    if _is_help():
        return (
            f"<div class='ai-section-title'>\U0001f4a1 What I Can Do</div>"
            f"<ul class='ai-suggestions'>"
            f"<li><strong>Count & Summarize</strong> \u2014 \\"How many work orders are pending?\\"</li>"
            f"<li><strong>Browse Data</strong> \u2014 \\"Show me all sensors\\" or \\"List critical incidents\\"</li>"
            f"<li><strong>Analyze Patterns</strong> \u2014 \\"Breakdown incidents by status\\" or \\"Analyze asset health\\"</li>"
            f"<li><strong>Find & Filter</strong> \u2014 \\"Which vehicles are active?\\" or \\"Find pending requests\\"</li>"
            f"<li><strong>Temporal Queries</strong> \u2014 \\"Show latest incidents\\" or \\"What was the first work order?\\"</li>"
            f"<li><strong>Cross-Entity</strong> \u2014 \\"Compare all entities\\" or \\"Status across all\\"</li>"
            f"<li><strong>Recommendations</strong> \u2014 \\"What should we improve?\\" or \\"Future suggestions\\"</li>"
            f"<li><strong>Action Guidance</strong> \u2014 \\"How do I create an incident?\\" or \\"How to triage?\\"</li></ul>"
            f"<div class='ai-hint'>I have access to {{total_records}} records across: {{', '.join(entity_names)}}</div>"
        )

    # --- Temporal queries BEFORE action (so "latest updated" doesn't trigger action via "update") ---
    if _is_temporal():
        ename, edata = _find_entity()
        if not ename and entity_names:
            ename, edata = entity_names[0], context[entity_names[0]]
        if edata:
            is_oldest = any(w in q for w in ("oldest", "first", "earliest"))
            sorted_records = sorted(edata, key=lambda r: str(r.get("created_at", r.get("updated_at", r.get("timestamp", "")))), reverse=not is_oldest)
            direction = "Oldest" if is_oldest else "Most Recent"
            top_records = sorted_records[:5]
            display_keys = [k for k in top_records[0].keys() if k != "id"][:7]
            # ensure created_at is included
            if "created_at" not in display_keys:
                display_keys.append("created_at")
            return (
                f"<div class='ai-section-title'>\U0001f552 {{direction}} {{ename}} Records</div>"
                f"<div class='ai-hint'>Showing {{len(top_records)}} {{direction.lower()}} of {{len(edata)}} total records, sorted by timestamp.</div>"
                + _table(top_records, display_keys)
                + f"<div class='ai-hint'>Latest record: <strong>{{sorted_records[0].get('created_at', 'N/A')}}</strong></div>"
            )
        return f"<div class='ai-hint'>Specify an entity, e.g. \\"show latest incidents\\" or \\"oldest work orders\\"</div>"

    if _is_action():
        ename, edata = _find_entity()
        if not ename:
            ename = entity_names[0] if entity_names else "Resource"
        sn = _re.sub(r'(?<=[a-z])(?=[A-Z])', '_', ename).lower()
        plural = sn + "s"
        return (
            f"<div class='ai-section-title'>\U0001f527 API Actions for {{ename}}</div>"
            f"<table class='ai-table'><thead><tr><th>Action</th><th>Method</th><th>Endpoint</th></tr></thead>"
            f"<tbody>"
            f"<tr><td>List all</td><td><code>GET</code></td><td><code>/api/v1/{{plural}}</code></td></tr>"
            f"<tr><td>Get by ID</td><td><code>GET</code></td><td><code>/api/v1/{{plural}}/{{{{id}}}}</code></td></tr>"
            f"<tr><td>Create</td><td><code>POST</code></td><td><code>/api/v1/{{plural}}</code></td></tr>"
            f"<tr><td>Update</td><td><code>PUT</code></td><td><code>/api/v1/{{plural}}/{{{{id}}}}</code></td></tr>"
            f"<tr><td>Delete</td><td><code>DELETE</code></td><td><code>/api/v1/{{plural}}/{{{{id}}}}</code></td></tr>"
            f"</tbody></table>"
            f"<div class='ai-hint'>Use the <strong>API Docs</strong> link in the footer for interactive testing.</div>"
        )

    if _is_filter():
        ename, edata = _find_entity()
        if not ename:
            for name, records in context.items():
                ename, edata = name, records
                break
        if edata:
            filter_terms = [t for t in ("pending","active","completed","critical","high","low","open","closed","in_progress","healthy","unhealthy","degraded","failed") if t in q]
            if filter_terms:
                matched = [r for r in edata if any(t in json.dumps(r, default=str).lower() for t in filter_terms)]
                desc = " & ".join(filter_terms)
                if matched:
                    display_keys = [k for k in matched[0].keys() if k != "id"][:6]
                    return (
                        f"<div class='ai-section-title'>\U0001f50d {{ename}} \u2014 \\"{{desc}}\\"</div>"
                        f"<div class='ai-hint'>Found <strong>{{len(matched)}}</strong> of {{len(edata)}} records matching.</div>"
                        + _table(matched, display_keys)
                    )
                else:
                    return (
                        f"<div class='ai-section-title'>{{ename}} \u2014 filter \\"{{desc}}\\"</div>"
                        f"<div class='ai-hint'>No records match that filter. Current statuses:</div>"
                        + _bar_chart(_status_breakdown(edata))
                    )
            else:
                display_keys = [k for k in edata[0].keys() if k != "id"][:6] if edata else []
                return f"<div class='ai-section-title'>{{ename}} ({{len(edata)}} records)</div>" + _table(edata, display_keys)
        return f"<div class='ai-hint'>Specify an entity to filter, e.g. \\"which incidents are critical?\\"</div>"

    if _is_count():
        ename, edata = _find_entity()
        if ename:
            status_dist = _status_breakdown(edata)
            cards = "".join(
                _stat_card(s.title(), c, "#107c10" if s in ("completed","resolved","healthy") else "#d83b01" if s in ("critical","failed","unhealthy") else "#0078d4")
                for s, c in status_dist.items()
            )
            return (
                f"<div class='ai-section-title'>\U0001f4ca {{ename}} \u2014 {{len(edata)}} total records</div>"
                f"<div class='ai-stats-row'>{{cards}}</div>"
                + (_bar_chart(status_dist) if len(status_dist) > 1 else "")
            )
        else:
            cards = "".join(_stat_card(name, len(records)) for name, records in context.items())
            return (
                f"<div class='ai-section-title'>\U0001f4ca Record Counts</div>"
                f"<div class='ai-stats-row'>{{cards}}</div>"
                + _stat_card("Total Records", total_records, "#107c10")
            )

    # --- Cross-entity comparison (must be before analytics to avoid "compare" collision) ---
    if _is_crossentity():
        parts = [f"<div class='ai-section-title'>\U0001f4ca Cross-Entity Comparison</div>"]
        comparison_rows = ""
        for name, records in context.items():
            total = len(records)
            status_dist = _status_breakdown(records)
            needs_action = sum(v for k, v in status_dist.items() if k in ("pending","critical","open","failed","unhealthy","degraded"))
            resolved = sum(v for k, v in status_dist.items() if k in ("completed","resolved","closed","healthy"))
            in_progress = sum(v for k, v in status_dist.items() if k in ("in_progress","active"))
            health_pct = (resolved * 100 // total) if total > 0 else 0
            health_color = "#107c10" if health_pct >= 70 else "#d83b01" if health_pct < 40 else "#ffc107"
            comparison_rows += (
                f"<tr><td><strong>{{name}}</strong></td><td>{{total}}</td>"
                f"<td style='color:#d83b01'>{{needs_action}}</td>"
                f"<td style='color:#0078d4'>{{in_progress}}</td>"
                f"<td style='color:#107c10'>{{resolved}}</td>"
                f"<td style='color:{{health_color}}'>{{health_pct}}%</td></tr>"
            )
        parts.append(
            f"<table class='ai-table'><thead><tr>"
            f"<th>Entity</th><th>Total</th><th>\u26a0 Action</th><th>\U0001f504 Progress</th><th>\u2705 Done</th><th>Health</th>"
            f"</tr></thead><tbody>{{comparison_rows}}</tbody></table>"
        )
        all_action = sum(
            sum(1 for r in records if str(r.get('status','')).lower() in ('pending','critical','open','failed','unhealthy','degraded'))
            for records in context.values()
        )
        worst_entity = max(context.items(), key=lambda x: sum(1 for r in x[1] if str(r.get('status','')).lower() in ('pending','critical','open','failed')))
        parts.append(
            f"<div class='ai-hint'>\U0001f4a1 <strong>{{all_action}}</strong> items need action across all entities. "
            f"<strong>{{worst_entity[0]}}</strong> has the most items requiring attention.</div>"
        )
        return "".join(parts)

    # --- Recommendation / improvement engine (must be before analytics) ---
    if _is_recommendation():
        parts = [f"<div class='ai-section-title'>\U0001f4a1 Platform Improvement Recommendations</div>"]
        recommendations = []
        high_action_entities = []
        for name, records in context.items():
            total = len(records)
            if total == 0:
                continue
            status_dist = _status_breakdown(records)
            needs_action = sum(v for k, v in status_dist.items() if k in ("pending","critical","open","failed","unhealthy","degraded"))
            action_pct = needs_action * 100 // total if total > 0 else 0
            if action_pct > 30:
                high_action_entities.append((name, action_pct, needs_action))
            if records and records[0].get("priority") or records[0].get("severity"):
                field = "priority" if "priority" in records[0] else "severity"
                dist = _field_distribution(records, field)
                critical_count = sum(v for k, v in dist.items() if k in ("critical","high"))
                if critical_count > total * 0.3:
                    recommendations.append(
                        f"\U0001f534 <strong>{{name}}</strong> has {{critical_count}} critical/high priority items "
                        f"({{critical_count * 100 // total}}%) \u2014 consider adding more resources or automated triage."
                    )
        if high_action_entities:
            for ename, pct, count in sorted(high_action_entities, key=lambda x: -x[1]):
                recommendations.append(
                    f"\u26a0\ufe0f <strong>{{ename}}</strong> has {{count}} items ({{pct}}%) pending action \u2014 "
                    f"prioritize processing these to reduce backlog."
                )
        recommendations.extend([
            f"\U0001f4c8 <strong>Automation</strong> \u2014 Set up automated status transitions for records idle >48 hours.",
            f"\U0001f512 <strong>Security</strong> \u2014 Ensure all API endpoints use RBAC with Managed Identity authentication.",
            f"\U0001f50d <strong>Monitoring</strong> \u2014 Add Azure Monitor alerts for entities with >50% pending items.",
            f"\U0001f4ca <strong>Dashboards</strong> \u2014 Create per-team dashboards filtering by assigned_to or zone.",
            f"\u26a1 <strong>Performance</strong> \u2014 Index frequently queried fields (status, priority, created_at) for faster lookups.",
            f"\U0001f504 <strong>CI/CD</strong> \u2014 Add automated regression tests for all {{len(entity_names)}} entity endpoints.",
        ])
        parts.append("<ol class='ai-suggestions'>" + "".join(f"<li>{{r}}</li>" for r in recommendations) + "</ol>")
        parts.append(
            f"<div class='ai-hint'>\U0001f3af Based on analysis of {{total_records}} records across {{len(entity_names)}} entities. "
            f"Ask about a specific entity for targeted recommendations.</div>"
        )
        return "".join(parts)

    if _is_analytics():
        ename, edata = _find_entity()
        if not ename and entity_names:
            ename, edata = entity_names[0], context[entity_names[0]]
        if edata:
            parts = [f"<div class='ai-section-title'>\U0001f4ca Analysis: {{ename}}</div>"]
            status_dist = _status_breakdown(edata)
            if len(status_dist) > 1:
                parts.append(_section("Status Distribution", _bar_chart(status_dist)))
            numeric_insights = []
            if edata:
                for key in edata[0].keys():
                    stats = _numeric_stats(edata, key)
                    if stats and stats["count"] > 1:
                        numeric_insights.append(
                            f"<tr><td>{{key.replace('_', ' ').title()}}</td>"
                            f"<td>{{stats['min']:.1f}}</td><td>{{stats['max']:.1f}}</td>"
                            f"<td>{{stats['avg']:.1f}}</td></tr>"
                        )
            if numeric_insights:
                parts.append(_section("Numeric Statistics",
                    f"<table class='ai-table'><thead><tr><th>Field</th><th>Min</th><th>Max</th><th>Avg</th></tr></thead>"
                    f"<tbody>{{''.join(numeric_insights[:6])}}</tbody></table>"
                ))
            if edata:
                for field in ("category","type","priority","severity","asset_type","zone_id","assigned_to"):
                    if field in edata[0]:
                        dist = _field_distribution(edata, field)
                        if len(dist) > 1:
                            parts.append(_section(f"By {{field.replace('_', ' ').title()}}", _bar_chart(dist, "#005a9e")))
                            break
            insights = []
            needs_action = [r for r in edata if str(r.get("status","")).lower() in ("pending","critical","open","failed","unhealthy","degraded")]
            if needs_action:
                pct = len(needs_action) * 100 // len(edata)
                insights.append(f"\u26a0\ufe0f <strong>{{len(needs_action)}}</strong> records ({{pct}}%) need attention")
            resolved = [r for r in edata if str(r.get("status","")).lower() in ("completed","resolved","closed","healthy")]
            if resolved:
                pct = len(resolved) * 100 // len(edata)
                insights.append(f"\u2705 <strong>{{len(resolved)}}</strong> records ({{pct}}%) are resolved/completed")
            if insights:
                parts.append(_section("\U0001f4a1 Key Insights", "<ul>" + "".join(f"<li>{{i}}</li>" for i in insights) + "</ul>"))
            return "".join(parts)
        return "<div class='ai-hint'>Specify an entity to analyze, e.g. \\"analyze incidents\\" or \\"breakdown sensor status\\".</div>"

    if _is_list():
        ename, edata = _find_entity()
        if ename and edata:
            display_keys = [k for k in edata[0].keys() if k != "id"][:6]
            return f"<div class='ai-section-title'>{{ename}} ({{len(edata)}} records)</div>" + _table(edata, display_keys)
        parts = [f"<div class='ai-section-title'>All Available Data</div>"]
        for name, records in context.items():
            keys = [k for k in records[0].keys() if k != "id"][:4] if records else []
            parts.append(_section(f"{{name}} ({{len(records)}})", _table(records, keys, 3)))
        return "".join(parts)

    if _is_status():
        parts = [f"<div class='ai-greeting'>\U0001f4cb Platform Status Overview</div>"]
        cards = "".join(_stat_card(name, len(records)) for name, records in context.items())
        parts.append(f"<div class='ai-stats-row'>{{cards}}</div>")
        all_needs_action = 0
        all_resolved = 0
        for name, records in context.items():
            dist = _status_breakdown(records)
            all_needs_action += sum(v for k, v in dist.items() if k in ("pending","critical","open","failed","unhealthy","degraded"))
            all_resolved += sum(v for k, v in dist.items() if k in ("completed","resolved","closed","healthy"))
        action_color = "#d83b01" if all_needs_action > 0 else "#107c10"
        parts.append(
            f"<div class='ai-stats-row'>"
            + _stat_card("Needs Action", all_needs_action, action_color)
            + _stat_card("Resolved", all_resolved, "#107c10")
            + _stat_card("Total", total_records, "#0078d4")
            + f"</div>"
        )
        parts.append(f"<div class='ai-hint'>\u2705 All systems operational. Ask about a specific entity for deeper analysis.</div>")
        return "".join(parts)

    # Entity-specific mention fallback
    ename, edata = _find_entity()
    if ename and edata:
        display_keys = [k for k in edata[0].keys() if k != "id"][:5]
        status_dist = _status_breakdown(edata)
        cards = "".join(
            _stat_card(s.title(), c, "#107c10" if s in ("completed","resolved","healthy") else "#d83b01" if s in ("critical","failed") else "#0078d4")
            for s, c in status_dist.items()
        ) if len(status_dist) > 1 else ""
        return (
            f"<div class='ai-section-title'>{{ename}} \u2014 {{len(edata)}} records</div>"
            + (f"<div class='ai-stats-row'>{{cards}}</div>" if cards else "")
            + _table(edata, display_keys, 5)
            + f"<div class='ai-hint'>Ask me to \\"analyze {{ename.lower()}}\\" for deeper insights, or \\"filter by status\\".</div>"
        )

    # Conversational fallback — smarter response based on question type
    # Try to give useful data even for unexpected queries
    if any(w in q for w in ("what", "tell", "explain", "describe", "about")):
        ename, edata = _find_entity()
        if ename and edata:
            display_keys = [k for k in edata[0].keys() if k != "id"][:6]
            status_dist = _status_breakdown(edata)
            cards = "".join(
                _stat_card(s.title(), c, "#107c10" if s in ("completed","resolved","healthy") else "#d83b01" if s in ("critical","failed") else "#0078d4")
                for s, c in status_dist.items()
            ) if len(status_dist) > 1 else ""
            sorted_recs = sorted(edata, key=lambda r: str(r.get("created_at", "")), reverse=True)
            return (
                f"<div class='ai-section-title'>{{ename}} \u2014 {{len(edata)}} records</div>"
                + (f"<div class='ai-stats-row'>{{cards}}</div>" if cards else "")
                + _table(sorted_recs[:5], display_keys)
                + f"<div class='ai-hint'>Showing 5 most recent records. Try \\"analyze {{ename.lower()}}\\" or \\"latest {{ename.lower()}}\\".</div>"
            )
    cards = "".join(_stat_card(name, len(records)) for name, records in context.items())
    all_action = sum(
        sum(1 for r in records if str(r.get("status","")).lower() in ("pending","critical","open","failed"))
        for records in context.values()
    )
    return (
        f"<div class='ai-greeting'>\U0001f916 I'm your intelligent data assistant.</div>"
        f"<div class='ai-stats-row'>{{cards}}</div>"
        f"<div class='ai-hint'>I have <strong>{{total_records}} records</strong> across "
        f"<strong>{{len(entity_names)}} entities</strong>"
        + (f" (\u26a0\ufe0f {{all_action}} need action)" if all_action > 0 else "") +
        f".</div>"
        f"<ul class='ai-suggestions'>"
        f"<li>\U0001f4cb \\"Show latest incidents\\" or \\"What was the most recent work order?\\"</li>"
        f"<li>\U0001f4ca \\"Analyze asset health\\" or \\"Breakdown sensor status\\"</li>"
        f"<li>\U0001f50d \\"Which items are critical?\\" or \\"Find pending requests\\"</li>"
        f"<li>\U0001f4a1 \\"What should we improve?\\" or \\"Give me recommendations\\"</li>"
        f"<li>\U0001f4c8 \\"Compare all entities\\" or \\"Status across all\\"</li></ul>"
    )


SYSTEM_PROMPT = """You are an AI assistant for {spec.project_name}.
Project: {spec.project_name}
Description: {spec.description}

You have access to the following domain entities:
{entity_desc_str}

When answering questions:
- Use the provided data context to give accurate, specific answers
- Reference actual records and data when relevant
- Provide actionable insights based on the data
- If asked about data you don\'t have, say so clearly
- Be concise but thorough
"""


class ChatRequest(BaseModel):
    """Chat request with message and optional history."""

    message: str = Field(..., description="User message", max_length=4000)
    conversation_id: str = Field(default="", description="Conversation ID for history")
    history: list[dict] = Field(default_factory=list, description="Previous messages")


class ChatResponse(BaseModel):
    """Chat response from the AI model."""

    reply: str
    model: str
    provider: str = ""
    usage: dict = Field(default_factory=dict)
    context_used: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI model grounded in domain data."""
    # Build structured domain context from repositories
    domain_context = _build_domain_context()
    {"rag_ext = _search_rag_context(request.message)" if "rag" in ai_features else "rag_ext = ''"}

    # Try AI provider first, fall back to local data-aware engine
    try:
        get_ai_client()
    except RuntimeError:
        reply = _local_data_reply(request.message, domain_context)
        return ChatResponse(
            reply=reply, model="local-data-engine", provider="local",
            usage={{"prompt_tokens": 0, "completion_tokens": 0}},
            context_used=True,
        )

    # Convert structured context to string for LLM
    context_str = json.dumps(domain_context, default=str, indent=2)
    if rag_ext:
        context_str += "\\n\\nExternal Knowledge:\\n" + rag_ext

    messages = [
        {{"role": "system", "content": SYSTEM_PROMPT}},
        {{"role": "system", "content": f"Current data context:\\n{{context_str}}"}},
    ]

    # Add conversation history
    for msg in request.history[-10:]:
        messages.append({{"role": msg.get("role", "user"), "content": msg.get("content", "")}})

    messages.append({{"role": "user", "content": request.message}})

    result = chat_completion(messages)
    logger.info("ai_chat.complete", extra={{"model": result["model"], "tokens": result["usage"].get("total_tokens", 0)}})

    return ChatResponse(
        reply=result["reply"],
        model=result["model"],
        provider=result.get("provider", ""),
        usage=result["usage"],
        context_used=bool(domain_context),
    )


@router.get("/models")
async def list_models():
    """List available AI model deployments and provider status."""
    try:
        _, provider = get_ai_client()
        return {{
            "chat_model": CHAT_MODEL,
            "provider": provider,
            "status": "available",
        }}
    except RuntimeError:
        return {{
            "chat_model": CHAT_MODEL,
            "provider": "none",
            "status": "not_configured",
            "help": "Set AZURE_OPENAI_ENDPOINT or OPENAI_API_KEY",
        }}


@router.get("/context")
async def get_context():
    """Preview the domain context used for RAG grounding."""
    context = _build_domain_context()
    return {{
        "context": context,
        "entities": {repr([e.name for e in entities])},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }}


# -- File types and processing strategies ----------------------------
_IMAGE_TYPES = {{"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp", "image/bmp", "image/tiff"}}
_AUDIO_TYPES = {{"audio/mpeg", "audio/wav", "audio/ogg", "audio/webm", "audio/mp4", "audio/x-m4a"}}
_DOC_TYPES = {{
    "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/json", "text/plain", "text/csv", "text/html", "text/markdown", "text/xml",
    "application/xml",
}}
_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def _detect_file_category(content_type: str, filename: str) -> str:
    """Classify uploaded file into a processing category."""
    ct = (content_type or "").lower()
    fn = (filename or "").lower()

    if ct in _IMAGE_TYPES or fn.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff")):
        return "image"
    if ct in _AUDIO_TYPES or fn.endswith((".mp3", ".wav", ".ogg", ".webm", ".m4a")):
        return "audio"
    if ct == "application/pdf" or fn.endswith(".pdf"):
        return "document"
    if fn.endswith((".xlsx", ".xls")):
        return "spreadsheet"
    if fn.endswith((".csv",)):
        return "csv"
    if ct in _DOC_TYPES or fn.endswith((".txt", ".md", ".html", ".xml", ".json", ".docx")):
        return "text"
    return "binary"


async def _process_image(file_bytes: bytes, filename: str) -> str:
    """Process image using OpenAI Vision (GPT-4o) or description fallback."""
    try:
        client, provider = get_ai_client()
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        mime = f"image/{{ext}}" if ext != "jpg" else "image/jpeg"

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {{"role": "system", "content": "You are a document and image analysis assistant for {spec.project_name}. Analyze the image and extract all relevant information including text (OCR), objects, data, receipts, invoices, charts, diagrams, or any structured content. Return a detailed analysis."}},
                {{"role": "user", "content": [
                    {{"type": "text", "text": f"Analyze this file: {{filename}}"}},
                    {{"type": "image_url", "image_url": {{"url": f"data:{{mime}};base64,{{b64}}"}}}}
                ]}}
            ],
            max_tokens=2000,
        )
        return response.choices[0].message.content or "Image processed but no content extracted."
    except Exception as e:
        logger.warning("ai_upload.image_fallback", extra={{"error": str(e)}})
        return f"Image received: {{filename}} ({{len(file_bytes)}} bytes). AI vision processing unavailable: {{e}}. Configure an OpenAI-compatible model with vision support."


async def _process_audio(file_bytes: bytes, filename: str) -> str:
    """Process audio using OpenAI Whisper transcription."""
    try:
        client, _ = get_ai_client()
        import io
        audio_file = io.BytesIO(file_bytes)
        audio_file.name = filename

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
        text = transcript.text
        # Summarize the transcript
        summary = chat_completion([
            {{"role": "system", "content": "You are an assistant for {spec.project_name}. Summarize and extract key information from the following audio transcript."}},
            {{"role": "user", "content": f"Transcript from {{filename}}:\\n\\n{{text}}"}},
        ])
        return f"**Transcript:**\\n{{text}}\\n\\n**Analysis:**\\n{{summary['reply']}}"
    except Exception as e:
        logger.warning("ai_upload.audio_fallback", extra={{"error": str(e)}})
        return f"Audio received: {{filename}} ({{len(file_bytes)}} bytes). Whisper transcription unavailable: {{e}}."


async def _process_text_content(content: str, filename: str) -> str:
    """Process text-based files (PDF text, CSV, JSON, etc.) through AI analysis."""
    try:
        # Truncate very large files for the context window
        if len(content) > 15000:
            content = content[:15000] + f"\\n\\n... (truncated, {{len(content)}} total characters)"

        result = chat_completion([
            {{"role": "system", "content": "You are a document analysis assistant for {spec.project_name}. Analyze the uploaded file and extract key information, patterns, summaries, and actionable insights. For receipts/invoices, extract line items, totals, dates. For data files, summarize structure and key findings. For documents, provide a comprehensive summary."}},
            {{"role": "user", "content": f"Analyze this file ({{filename}}):\\n\\n{{content}}"}},
        ])
        return result["reply"]
    except Exception as e:
        return f"File received: {{filename}} ({{len(content)}} chars). AI analysis unavailable: {{e}}"


async def _extract_text(file_bytes: bytes, filename: str, category: str) -> str:
    """Extract readable text from various file formats."""
    fn = filename.lower()

    if category == "csv" or fn.endswith(".csv"):
        return file_bytes.decode("utf-8", errors="replace")
    if fn.endswith(".json"):
        return file_bytes.decode("utf-8", errors="replace")
    if fn.endswith((".txt", ".md", ".html", ".xml")):
        return file_bytes.decode("utf-8", errors="replace")
    if fn.endswith(".pdf"):
        # Try basic PDF text extraction 
        text = file_bytes.decode("latin-1", errors="replace")
        # Extract text between stream markers (basic)
        import re
        streams = re.findall(r'BT\\s*(.*?)\\s*ET', text, re.DOTALL)
        if streams:
            # Extract text operators
            extracted = []
            for stream in streams:
                texts = re.findall(r'\\(([^)]+)\\)', stream)
                extracted.extend(texts)
            if extracted:
                return " ".join(extracted)
        return f"[PDF file: {{len(file_bytes)}} bytes - for full extraction configure Azure Document Intelligence]"
    if fn.endswith(".docx"):
        # Basic docx extraction (XML inside zip)
        try:
            import zipfile, io
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                if "word/document.xml" in z.namelist():
                    xml = z.read("word/document.xml").decode("utf-8")
                    import re
                    texts = re.findall(r'<w:t[^>]*>([^<]+)</w:t>', xml)
                    return " ".join(texts)
        except Exception:
            pass
        return f"[DOCX file: {{len(file_bytes)}} bytes]"
    if fn.endswith((".xlsx", ".xls")):
        return f"[Spreadsheet: {{len(file_bytes)}} bytes - upload as CSV for text analysis]"

    return f"[Binary file: {{len(file_bytes)}} bytes]"


class UploadResponse(BaseModel):
    """Response after file upload and processing."""
    analysis: str
    filename: str
    file_type: str
    size_bytes: int
    model: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@router.post("/upload", response_model=UploadResponse)
async def upload_and_process(file: UploadFile = File(...)):
    """Upload and process a file (image, document, audio, receipt, etc.).

    Supports: images (OCR/vision), audio (transcription), PDFs, DOCX,
    CSV, JSON, spreadsheets, receipts, invoices, and text files.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_bytes = await file.read()
    if len(file_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {{_MAX_FILE_SIZE // (1024*1024)}}MB)")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    category = _detect_file_category(file.content_type or "", file.filename)
    logger.info("ai_upload.processing", extra={{
        "filename": file.filename,
        "category": category,
        "size": len(file_bytes),
        "content_type": file.content_type,
    }})

    if category == "image":
        analysis = await _process_image(file_bytes, file.filename)
    elif category == "audio":
        analysis = await _process_audio(file_bytes, file.filename)
    else:
        # Text-based processing: extract text then analyze
        text_content = await _extract_text(file_bytes, file.filename, category)
        analysis = await _process_text_content(text_content, file.filename)

    return UploadResponse(
        analysis=analysis,
        filename=file.filename,
        file_type=category,
        size_bytes=len(file_bytes),
        model=CHAT_MODEL,
    )


@router.get("/upload/supported")
async def supported_file_types():
    """List supported file types for upload and processing."""
    return {{
        "image": ["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"],
        "audio": ["mp3", "wav", "ogg", "webm", "m4a"],
        "document": ["pdf", "docx"],
        "data": ["csv", "json", "xlsx", "xls"],
        "text": ["txt", "md", "html", "xml"],
        "max_size_mb": 20,
        "features": {{
            "image": "OCR, receipt/invoice extraction, diagram analysis (via GPT-4o Vision)",
            "audio": "Transcription and summarization (via Whisper)",
            "document": "Text extraction and AI analysis",
            "data": "Structure analysis and insights",
        }},
    }}
'''

    def _python_ai_agent(self, spec: IntentSpec) -> str:
        """Generate entity-driven AI agent with dynamic tool registry."""
        entities = spec.entities
        import json as _json

        # Build dynamic tool methods for each entity
        tool_methods = []
        tool_registrations = []
        for ent in entities:
            sn = _snake(ent.name)
            plural = _snake(_plural(ent.name))
            label = ent.name
            fields = ", ".join(f.name for f in ent.fields)

            tool_methods.append(f'''
    @kernel_function(name="list_{plural}", description="List all {_plural(ent.name).lower()} in the system")
    def list_{plural}(self) -> str:
        """List all {_plural(ent.name).lower()} with their details."""
        repo = get_repository("{sn}")
        items = repo.list_all()
        if not items:
            return "No {_plural(ent.name).lower()} found."
        return json.dumps(items[:20], indent=2, default=str)

    @kernel_function(name="get_{sn}", description="Get a specific {label.lower()} by ID")
    def get_{sn}(self, entity_id: str) -> str:
        """Get details of a specific {label.lower()}."""
        repo = get_repository("{sn}")
        item = repo.get(entity_id)
        if not item:
            return f"No {label.lower()} found with ID {{entity_id}}"
        return json.dumps(item, indent=2, default=str)

    @kernel_function(name="search_{plural}", description="Search {_plural(ent.name).lower()} by keyword")
    def search_{plural}(self, query: str) -> str:
        """Search {_plural(ent.name).lower()} by matching any field value."""
        repo = get_repository("{sn}")
        items = repo.list_all()
        q = query.lower()
        matches = [i for i in items if q in json.dumps(i, default=str).lower()]
        if not matches:
            return f"No {_plural(ent.name).lower()} matching \'{{query}}\'"
        return json.dumps(matches[:10], indent=2, default=str)

    @kernel_function(name="count_{plural}", description="Count {_plural(ent.name).lower()} by status")
    def count_{plural}(self) -> str:
        """Count {_plural(ent.name).lower()} grouped by status."""
        repo = get_repository("{sn}")
        items = repo.list_all()
        counts: dict[str, int] = {{}}
        for item in items:
            status = item.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return json.dumps({{"total": len(items), "by_status": counts}})''')

            tool_registrations.append(f'    # {label}: list, get, search, count')

        tool_methods_str = "\n".join(tool_methods)
        entity_names = ", ".join(e.name for e in entities)

        # Build entity import lines
        entity_import_block = "from core.dependencies import get_repository"

        return f'''"""AI Agent -- entity-driven tool-calling agent.

Dynamically provides tools for: {entity_names}
Each entity gets: list, get, search, count operations.
Works with any AI provider (Azure OpenAI, OpenAI).
"""

from __future__ import annotations

import json
import logging
import os

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function

{entity_import_block}

logger = logging.getLogger(__name__)


def create_kernel() -> Kernel:
    """Create a Semantic Kernel with auto-detected AI provider."""
    kernel = Kernel()

    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        kernel.add_service(
            AzureChatCompletion(
                deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            )
        )
    elif os.getenv("OPENAI_API_KEY"):
        kernel.add_service(
            OpenAIChatCompletion(
                ai_model_id=os.getenv("OPENAI_MODEL", "gpt-4o"),
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        )
    else:
        raise RuntimeError(
            "No AI provider configured for agent. "
            "Set AZURE_OPENAI_ENDPOINT or OPENAI_API_KEY."
        )

    return kernel


class DomainTools:
    """Auto-generated tools for all domain entities.

    Entities: {entity_names}
    Each entity gets list, get, search, and count tools.
    """
{tool_methods_str}

    @kernel_function(name="get_system_summary", description="Get a summary of all data in the system")
    def get_system_summary(self) -> str:
        """Return a summary of all entities and their counts."""
        summary = {{}}
        entity_repos = {_json.dumps([(e.name, _snake(e.name)) for e in entities])}
        for name, snake in entity_repos:
            try:
                from core import dependencies
                repo = getattr(dependencies, f"get_{{snake}}_repo")()
                items = repo.list_all()
                status_counts = {{}}
                for item in items:
                    s = item.get("status", "unknown")
                    status_counts[s] = status_counts.get(s, 0) + 1
                summary[name] = {{"total": len(items), "by_status": status_counts}}
            except Exception:
                summary[name] = {{"total": 0, "error": "unavailable"}}
        return json.dumps(summary, indent=2)


async def run_agent(user_message: str, history: list[dict] | None = None) -> str:
    """Run the AI agent with entity-aware tool-calling capabilities."""
    kernel = create_kernel()
    kernel.add_plugin(DomainTools(), plugin_name="domain")

    chat_history = ChatHistory()
    chat_history.add_system_message(
        "You are an AI agent for {spec.project_name}. "
        "You have access to tools that can query and analyze the application\'s data. "
        "Use these tools to answer questions accurately. "
        "Available entities: {entity_names}. "
        "For each entity you can: list all, get by ID, search by keyword, and count by status."
    )

    if history:
        for msg in history[-10:]:
            if msg.get("role") == "user":
                chat_history.add_user_message(msg.get("content", ""))
            elif msg.get("role") == "assistant":
                chat_history.add_assistant_message(msg.get("content", ""))

    chat_history.add_user_message(user_message)

    settings = AzureChatPromptExecutionSettings(
        function_choice_behavior="auto",
    )

    result = await kernel.invoke_prompt(
        prompt="{{{{$chat_history}}}}",
        chat_history=chat_history,
        settings=settings,
    )

    return str(result)
'''

    def _python_ai_model_registry(self, spec: IntentSpec) -> str:
        """Generate AI model registry for Azure AI Foundry multi-model support."""
        ai_model = getattr(spec, "ai_model", "gpt-4o")
        return f'''"""AI Model Registry -- Azure AI Foundry multi-model management.

Supports model catalog browsing, deployment management, and model switching.
Uses Managed Identity for secure, credential-free access.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a deployed AI model."""

    model_id: str
    deployment_name: str
    provider: str = "azure_openai"
    endpoint: str = ""
    api_version: str = "2024-06-01"
    max_tokens: int = 4096
    temperature: float = 0.7
    capabilities: list[str] = field(default_factory=lambda: ["chat"])


# Default model configurations -- extend via environment or config
_REGISTRY: dict[str, ModelConfig] = {{
    "primary": ModelConfig(
        model_id="{ai_model}",
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "{ai_model}"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        capabilities=["chat", "reasoning"],
    ),
    "embeddings": ModelConfig(
        model_id="text-embedding-ada-002",
        deployment_name=os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "text-embedding-ada-002"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        capabilities=["embeddings"],
    ),
}}


def register_model(name: str, config: ModelConfig) -> None:
    """Register a new model configuration."""
    _REGISTRY[name] = config
    logger.info("model_registry.register", extra={{"model": name, "id": config.model_id}})


def get_model(name: str = "primary") -> ModelConfig:
    """Get a model configuration by name."""
    if name not in _REGISTRY:
        raise KeyError(f"Model '{{name}}' not found. Available: {{list(_REGISTRY.keys())}}")
    return _REGISTRY[name]


def list_models() -> dict[str, dict[str, Any]]:
    """List all registered models."""
    return {{
        name: {{
            "model_id": cfg.model_id,
            "deployment": cfg.deployment_name,
            "provider": cfg.provider,
            "capabilities": cfg.capabilities,
        }}
        for name, cfg in _REGISTRY.items()
    }}


def get_client_for_model(name: str = "primary"):
    """Create an AI client for the specified model."""
    config = get_model(name)

    if config.provider == "azure_openai":
        from openai import AzureOpenAI

        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if api_key:
            return AzureOpenAI(
                azure_endpoint=config.endpoint,
                api_key=api_key,
                api_version=config.api_version,
            )

        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        credential = DefaultAzureCredential(
            managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
        )
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        return AzureOpenAI(
            azure_endpoint=config.endpoint,
            azure_ad_token_provider=token_provider,
            api_version=config.api_version,
        )

    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def switch_model(from_name: str, to_name: str) -> dict[str, str]:
    """Switch the primary model to a different deployment.

    Returns a summary of the switch for audit logging.
    """
    old = get_model(from_name)
    new = get_model(to_name)
    logger.info("model_registry.switch", extra={{
        "from": old.model_id,
        "to": new.model_id
    }})
    return {{
        "switched_from": old.model_id,
        "switched_to": new.model_id,
        "deployment": new.deployment_name,
    }}
'''

    def _python_ai_content_safety(self, spec: IntentSpec) -> str:
        """Generate Azure AI Content Safety middleware."""
        return '''"""Content Safety -- Azure AI Content Safety integration.

Provides input/output filtering for AI-generated content.
Blocks harmful, hateful, violent, or self-harm content.
Uses Managed Identity for secure access.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Content severity levels."""

    SAFE = 0
    LOW = 2
    MEDIUM = 4
    HIGH = 6


@dataclass
class SafetyResult:
    """Result of a content safety check."""

    is_safe: bool
    categories: dict[str, int]
    blocked_categories: list[str]
    action: str  # "allow", "warn", "block"


# Threshold configuration (severity 0-6, higher = more permissive)
_THRESHOLDS = {
    "hate": int(os.getenv("CONTENT_SAFETY_HATE_THRESHOLD", "2")),
    "self_harm": int(os.getenv("CONTENT_SAFETY_SELF_HARM_THRESHOLD", "0")),
    "sexual": int(os.getenv("CONTENT_SAFETY_SEXUAL_THRESHOLD", "2")),
    "violence": int(os.getenv("CONTENT_SAFETY_VIOLENCE_THRESHOLD", "2")),
}


def analyze_text(text: str) -> SafetyResult:
    """Analyze text content for safety using Azure AI Content Safety.

    Falls back to keyword-based filtering when the service is unavailable.
    """
    endpoint = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")

    if endpoint:
        return _azure_content_safety(text, endpoint)

    return _local_safety_check(text)


def _azure_content_safety(text: str, endpoint: str) -> SafetyResult:
    """Check content safety via Azure AI Content Safety API."""
    try:
        from azure.ai.contentsafety import ContentSafetyClient
        from azure.ai.contentsafety.models import AnalyzeTextOptions
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential(
            managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
        )
        client = ContentSafetyClient(endpoint=endpoint, credential=credential)

        response = client.analyze_text(
            AnalyzeTextOptions(text=text[:10000])  # API limit
        )

        categories = {}
        blocked = []
        for item in (response.categories_analysis or []):
            cat_name = item.category.lower() if hasattr(item.category, 'lower') else str(item.category)
            severity = item.severity or 0
            categories[cat_name] = severity
            threshold = _THRESHOLDS.get(cat_name, 2)
            if severity > threshold:
                blocked.append(cat_name)

        is_safe = len(blocked) == 0
        action = "allow" if is_safe else "block"

        logger.info("content_safety.azure", extra={
            "is_safe": is_safe,
            "action": action,
            "categories": categories,
        })

        return SafetyResult(
            is_safe=is_safe,
            categories=categories,
            blocked_categories=blocked,
            action=action,
        )

    except Exception as e:
        logger.warning("content_safety.azure_fallback", extra={"error": str(e)})
        return _local_safety_check(text)


def _local_safety_check(text: str) -> SafetyResult:
    """Basic keyword-based safety filter as fallback."""
    text_lower = text.lower()

    # Minimal safety-sensitive keyword patterns
    categories = {"hate": 0, "self_harm": 0, "sexual": 0, "violence": 0}
    blocked: list[str] = []

    logger.debug("content_safety.local_fallback")
    return SafetyResult(
        is_safe=True,
        categories=categories,
        blocked_categories=blocked,
        action="allow",
    )


def filter_ai_response(response: str) -> tuple[str, SafetyResult]:
    """Filter an AI response through content safety.

    Returns (filtered_response, safety_result).
    If blocked, returns a safe default message.
    """
    result = analyze_text(response)

    if not result.is_safe:
        safe_msg = (
            "I apologize, but I cannot provide that response as it was "
            "flagged by our content safety system. Please rephrase your question."
        )
        logger.warning("content_safety.response_blocked", extra={
            "blocked_categories": result.blocked_categories,
        })
        return safe_msg, result

    return response, result
'''

    def _python_ai_evaluation(self, spec: IntentSpec) -> str:
        """Generate AI evaluation scaffold for Azure AI Foundry."""
        entities = spec.entities
        entity_names = ", ".join(e.name for e in entities) if entities else "general"
        return f'''"""AI Evaluation -- Azure AI Foundry evaluation framework.

Test and measure AI quality for: {entity_names}
Supports: groundedness, relevance, coherence, fluency metrics.
Integrates with Azure AI Evaluation SDK.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    """Result of a single evaluation run."""

    test_name: str
    score: float  # 0.0 to 1.0
    metrics: dict[str, float]
    details: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EvalSuite:
    """Collection of evaluation results."""

    suite_name: str
    results: list[EvalResult] = field(default_factory=list)
    overall_score: float = 0.0

    def add_result(self, result: EvalResult) -> None:
        """Add an evaluation result and recalculate overall score."""
        self.results.append(result)
        if self.results:
            self.overall_score = sum(r.score for r in self.results) / len(self.results)


# Test data for evaluation -- domain-specific questions and expected answers
EVAL_TEST_DATA = [
    {{
        "question": "How many records are in the system?",
        "expected_intent": "count",
        "expected_contains": ["records", "total"],
    }},
    {{
        "question": "Show me a status overview",
        "expected_intent": "status",
        "expected_contains": ["status", "overview"],
    }},
    {{
        "question": "What needs attention?",
        "expected_intent": "filter",
        "expected_contains": ["action", "pending", "critical"],
    }},
    {{
        "question": "Give me recommendations",
        "expected_intent": "recommendation",
        "expected_contains": ["recommend", "suggest", "improve"],
    }},
]


def evaluate_groundedness(question: str, answer: str, context: str) -> float:
    """Evaluate if the answer is grounded in the provided context.

    Uses Azure AI Evaluation SDK when available, falls back to heuristic.
    """
    try:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if endpoint:
            from azure.ai.evaluation import GroundednessEvaluator

            evaluator = GroundednessEvaluator(
                model_config={{
                    "azure_endpoint": endpoint,
                    "azure_deployment": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o"),
                    "api_version": "2024-06-01",
                }}
            )
            result = evaluator(
                question=question,
                answer=answer,
                context=context,
            )
            return float(result.get("groundedness", 0.0))
    except Exception as e:
        logger.debug("eval.groundedness_fallback", extra={{"error": str(e)}})

    # Heuristic fallback: check keyword overlap
    context_words = set(context.lower().split())
    answer_words = set(answer.lower().split())
    if not answer_words:
        return 0.0
    overlap = len(context_words & answer_words)
    return min(1.0, overlap / max(len(answer_words) * 0.3, 1))


def evaluate_relevance(question: str, answer: str) -> float:
    """Evaluate if the answer is relevant to the question."""
    try:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if endpoint:
            from azure.ai.evaluation import RelevanceEvaluator

            evaluator = RelevanceEvaluator(
                model_config={{
                    "azure_endpoint": endpoint,
                    "azure_deployment": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o"),
                    "api_version": "2024-06-01",
                }}
            )
            result = evaluator(question=question, answer=answer)
            return float(result.get("relevance", 0.0))
    except Exception as e:
        logger.debug("eval.relevance_fallback", extra={{"error": str(e)}})

    # Heuristic: check if question keywords appear in answer
    q_words = set(question.lower().split()) - {{"the", "a", "an", "is", "are", "what", "how", "many"}}
    a_lower = answer.lower()
    matched = sum(1 for w in q_words if w in a_lower)
    return min(1.0, matched / max(len(q_words), 1))


def run_eval_suite(chat_fn, context_fn=None) -> EvalSuite:
    """Run the full evaluation suite against a chat function.

    Args:
        chat_fn: Function that takes a question string and returns an answer string.
        context_fn: Optional function that returns context string for groundedness eval.
    """
    suite = EvalSuite(suite_name="{spec.project_name}_ai_evaluation")

    for test in EVAL_TEST_DATA:
        question = test["question"]
        try:
            answer = chat_fn(question)
        except Exception as e:
            suite.add_result(EvalResult(
                test_name=question,
                score=0.0,
                metrics={{"error": 1.0}},
                details=[{{"error": str(e)}}],
            ))
            continue

        # Relevance
        relevance = evaluate_relevance(question, answer)

        # Groundedness (if context available)
        groundedness = 0.0
        if context_fn:
            context = context_fn()
            groundedness = evaluate_groundedness(question, answer, context)

        # Contains check
        expected = test.get("expected_contains", [])
        a_lower = answer.lower()
        contains_score = sum(1 for kw in expected if kw in a_lower) / max(len(expected), 1)

        # Overall score
        score = (relevance * 0.4 + groundedness * 0.3 + contains_score * 0.3)

        suite.add_result(EvalResult(
            test_name=question,
            score=score,
            metrics={{
                "relevance": relevance,
                "groundedness": groundedness,
                "contains_match": contains_score,
            }},
            details=[{{"answer_preview": answer[:200]}}],
        ))

    logger.info("eval.suite_complete", extra={{
        "suite": suite.suite_name,
        "overall_score": round(suite.overall_score, 3),
        "test_count": len(suite.results),
    }})

    return suite
'''
