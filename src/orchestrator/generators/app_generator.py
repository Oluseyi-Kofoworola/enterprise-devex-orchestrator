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

from src.orchestrator.intent_schema import DataStore, DomainType, EntitySpec, IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


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
    """Return True if spec has domain-specific entities (not just default Item)."""
    if not spec.entities:
        return False
    if len(spec.entities) == 1 and spec.entities[0].name == "Item":
        return False
    return True


def _python_type_default(field_type: str) -> str:
    """Return Python default for a field type."""
    defaults = {
        "str": '""', "int": "0", "float": "0.0", "bool": "False",
        "list": "field(default_factory=list)",
        "list[str]": "field(default_factory=list)",
        "dict": "field(default_factory=dict)",
        "datetime": 'field(default_factory=lambda: datetime.now(timezone.utc).isoformat())',
    }
    return defaults.get(field_type, '""')


def _seed_value(field_spec, entity_name: str, row: int) -> str:
    """Generate a realistic seed value for a field."""
    name = field_spec.name
    ftype = field_spec.type
    ename_lower = entity_name.lower()

    if ftype == "float":
        amounts = [49.99, 125.50, 29.95]
        return str(amounts[(row - 1) % len(amounts)])
    if ftype == "int":
        return str(row * 10)
    if ftype == "bool":
        return "True" if row % 2 == 1 else "False"
    if ftype in ("list", "list[str]"):
        return '["item-001", "item-002"]' if row == 1 else '["item-003"]'
    if ftype == "dict":
        return "{}"
    if ftype == "datetime":
        return f'"2024-03-{10 + row}T{8 + row:02d}:{row * 15:02d}:00Z"'
    # str type — generate contextual values
    if name == "status":
        statuses = ["pending", "in_progress", "completed"]
        return f'"{statuses[(row - 1) % len(statuses)]}"'
    if name.endswith("_id"):
        ref = name.replace("_id", "").upper()
        return f'"{ref}-{1000 + row}"'
    if name == "reason":
        reasons = ["Defective product", "Wrong size", "Changed mind"]
        return f'"{reasons[(row - 1) % len(reasons)]}"'
    if name == "method":
        methods = ["original_payment", "store_credit", "exchange"]
        return f'"{methods[(row - 1) % len(methods)]}"'
    if name == "currency":
        return '"USD"'
    if name == "priority":
        priorities = ["high", "medium", "low"]
        return f'"{priorities[(row - 1) % len(priorities)]}"'
    if name == "notes":
        return f'"Sample {ename_lower} record #{row}"'
    if name in ("name", "title"):
        return f'"{entity_name} #{row}"'
    if name in ("description", "condition"):
        return f'"Sample {name} for record #{row}"'
    if name == "serial_number":
        return f'"SN-{ename_lower[:3].upper()}-2024-{row:04d}"'
    if name in ("location", "address"):
        locations = ["Downtown - Main St", "Industrial Zone B", "Central Park Area"]
        return f'"{locations[(row - 1) % len(locations)]}"'
    if name == "email":
        return f'"user{row}@example.com"'
    if name == "phone":
        return f'"+1-555-010{row}"'
    if name == "date":
        return f'"2024-03-{10 + row}T{6 + row:02d}:00:00Z"'
    return f'"{name}-value-{row}"'


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
        compliance_badges = self._enterprise_compliance_badges(spec)
        data_stores = self._enterprise_data_stores(spec)
        quick_actions = '<a class="action-btn" href="/docs"><span class="icon">\xf0\x9f\x93\x9a</span>API Documentation</a>\\n                    <a class="action-btn" href="/health"><span class="icon">\xf0\x9f\x92\x9a</span>Health Check</a>\\n                    <a class="action-btn" href="/keyvault/status"><span class="icon">\xf0\x9f\x94\x90</span>Key Vault Status</a>\\n                    <a class="action-btn" href="/api/v1/items"><span class="icon">\xf0\x9f\x93\xa6</span>API v1 Items</a>'
        endpoint_list = '<li><span class="method-badge get">GET</span><span class="endpoint-path">/health</span><span class="endpoint-desc">Liveness probe</span></li>\\n                    <li><span class="method-badge get">GET</span><span class="endpoint-path">/docs</span><span class="endpoint-desc">OpenAPI docs</span></li>\\n                    <li><span class="method-badge get">GET</span><span class="endpoint-path">/keyvault/status</span><span class="endpoint-desc">Vault connectivity</span></li>\\n                    <li><span class="method-badge get">GET</span><span class="endpoint-path">/api/v1/items</span><span class="endpoint-desc">Resource listing</span></li>\\n                    <li><span class="method-badge post">POST</span><span class="endpoint-path">/api/v1/items</span><span class="endpoint-desc">Create resource</span></li>'
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
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
{storage_imports}
from api.v1.router import router as v1_router

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

# -- Mount versioned API router --------------------------------------
app.include_router(v1_router, prefix="/api/v1", tags=["v1"])


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


# -- Root Endpoint (Enterprise Dashboard) ------
@app.get("/")
async def root():
    \"\"\"Root endpoint -- enterprise dashboard.\"\"\"
    {self._python_dashboard_block(spec)}
    return HTMLResponse(content=html)


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
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC

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
from api.v1.schemas import ItemCreate, ItemResponse
from core.dependencies import get_settings, get_repository
from core.config import Settings
from core.services import ItemService{storage_import}{storage_dep}

router = APIRouter()


@router.get("/items", response_model=list[ItemResponse], summary="List items")
async def list_items(settings: Settings = Depends(get_settings)):
    """Return items from the service layer."""
    repo = get_repository("item", settings.storage_mode)
    svc = ItemService(project_name=settings.app_name, repo=repo)
    return svc.list_items()


@router.post("/items", response_model=ItemResponse, status_code=201, summary="Create item")
async def create_item(payload: ItemCreate, settings: Settings = Depends(get_settings)):
    """Create a new item via the service layer."""
    repo = get_repository("item", settings.storage_mode)
    svc = ItemService(project_name=settings.app_name, repo=repo)
    return svc.create_item(payload.name, payload.description)


@router.get("/items/{{item_id}}", summary="Get item by ID")
async def get_item(item_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("item", settings.storage_mode)
    svc = ItemService(project_name=settings.app_name, repo=repo)
    item = svc.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/items/{{item_id}}", summary="Update item")
async def update_item(item_id: str, payload: ItemCreate, settings: Settings = Depends(get_settings)):
    repo = get_repository("item", settings.storage_mode)
    svc = ItemService(project_name=settings.app_name, repo=repo)
    item = svc.update_item(item_id, payload.name, payload.description)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/items/{{item_id}}", status_code=204, summary="Delete item")
async def delete_item(item_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("item", settings.storage_mode)
    svc = ItemService(project_name=settings.app_name, repo=repo)
    if not svc.delete_item(item_id):
        raise HTTPException(status_code=404, detail="Item not found")
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

            # Build the list of writable field names for create/update
            writable_fields = [f for f in ent.fields if f.name != "status"]
            create_kwargs = ", ".join(f"payload.{f.name}" for f in writable_fields)

            lines.append(f'''

# --- {label} CRUD ---
@router.get("/{slug}", response_model=list[{label}Response], summary="List {_plural(label).lower()}")
async def list_{slug}(status: str | None = None, settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    return svc.list_all(status)


@router.post("/{slug}", response_model={label}Response, status_code=201, summary="Create {label.lower()}")
async def create_{sn}(payload: {label}Create, settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    return svc.create(payload)


@router.get("/{slug}/{{{sn}_id}}", summary="Get {label.lower()} by ID")
async def get_{sn}({sn}_id: str, settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    item = svc.get({sn}_id)
    if not item:
        raise HTTPException(status_code=404, detail="{label} not found")
    return item


@router.put("/{slug}/{{{sn}_id}}", summary="Update {label.lower()}")
async def update_{sn}({sn}_id: str, payload: {label}Create, settings: Settings = Depends(get_settings)):
    repo = get_repository("{sn}", settings.storage_mode)
    svc = {label}Service(repo)
    item = svc.update({sn}_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="{label} not found")
    return item


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
    item = svc.{action}({sn}_id)
    if not item:
        raise HTTPException(status_code=404, detail="{label} not found")
    return item''')

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

            lines.append(f'class {label}Service:')
            lines.append(f'    """{ent.description or f"Manages {label} domain entities."}"""')
            lines.append('')
            lines.append('    def __init__(self, repo: BaseRepository) -> None:')
            lines.append('        self.repo = repo')
            lines.append('')

            # list_all
            lines.append('    def list_all(self, status: str | None = None) -> list[dict]:')
            lines.append('        items = self.repo.list_all()')
            lines.append('        if status:')
            lines.append('            items = [i for i in items if i.get("status") == status]')
            lines.append('        return items')
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
        for idx, ent in enumerate(spec.entities):
            sn = _snake(ent.name)
            lines.append(f'    "{sn}": [')
            # Generate 3 sample records per entity
            for rid in range(1, 4):
                record_parts = [f'"id": "{sn}-{rid:03d}"']
                for f in ent.fields:
                    val = _seed_value(f, ent.name, rid)
                    record_parts.append(f'"{f.name}": {val}')
                record_parts.append(f'"created_at": "2024-03-{10+rid}T0{8+rid}:00:00Z"')
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
        .kpi-bar { max-width:1200px; margin:-32px auto 20px; padding:0 24px; display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; }
        .kpi { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:20px; text-align:center; box-shadow:var(--shadow); transition:transform .15s; }
        .kpi:hover { transform:translateY(-2px); box-shadow:var(--shadow-lg); }
        .kpi .number { font-size:32px; font-weight:700; }
        .kpi .label { font-size:11px; text-transform:uppercase; letter-spacing:.8px; color:var(--text-secondary); margin-top:4px; }
        .kpi.ok .number { color:var(--success); }
        .kpi.warn .number { color:var(--warning); }
        .kpi.danger .number { color:var(--danger); }
        .main { max-width:1200px; margin:0 auto 40px; padding:0 24px; }
        .tab-bar { display:flex; gap:0; margin-bottom:0; border-bottom:2px solid var(--border); }
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
        .badge-pending { background:#fff3e0; color:#e65100; }
        .badge-in_progress,.badge-in-progress,.badge-processing { background:#e3f2fd; color:#1565c0; }
        .badge-approved,.badge-completed,.badge-processed { background:#e6f4ea; color:#1b5e20; }
        .badge-rejected,.badge-cancelled,.badge-failed { background:#fce4ec; color:#b71c1c; }
        .badge-escalated { background:#f3e5f5; color:#6a1b9a; }
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
        .info-card ul li::before { content:''; width:6px; height:6px; border-radius:50%; background:var(--primary); flex-shrink:0; }"""
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
        kpi_html.append(
            '<div class=\\"kpi warn\\" id=\\"kpi-pending\\">'
            '<div class=\\"number\\" id=\\"count-pending\\">--</div>'
            '<div class=\\"label\\">Pending Review</div></div>'
        )
        kpi_html.append(
            '<div class=\\"kpi ok\\" id=\\"kpi-completed\\">'
            '<div class=\\"number\\" id=\\"count-completed\\">--</div>'
            '<div class=\\"label\\">Completed</div></div>'
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

        async function loadAll() {lb}
            let totalPending = 0, totalCompleted = 0;
            for (const ent of ENTITIES) {lb}
                try {lb}
                    const r = await fetch('/api/v1/' + ent.slug);
                    const d = await r.json();
                    const rows = Array.isArray(d) ? d : (d.value || d.items || d.data || []);
                    allData[ent.slug] = rows;
                    document.getElementById('count-' + ent.slug).textContent = rows.length;
                    totalPending += rows.filter(r => r.status === 'pending').length;
                    totalCompleted += rows.filter(r => ['completed','approved','processed'].includes(r.status)).length;
                    renderTable(ent, rows);
                {rb} catch(e) {lb}
                    console.error('Failed to load ' + ent.slug, e);
                    document.getElementById('count-' + ent.slug).textContent = '!';
                {rb}
            {rb}
            document.getElementById('count-pending').textContent = totalPending;
            document.getElementById('count-completed').textContent = totalCompleted;
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
                    if (f === 'status') {lb}
                        cells += '<td><span class="badge badge-' + String(val).replace(/ /g,'-') + '">' + val + '</span></td>';
                    {rb} else if (f === 'amount') {lb}
                        cells += '<td style="font-weight:600">$' + Number(val).toFixed(2) + '</td>';
                    {rb} else if (f === 'priority') {lb}
                        const pcolor = val === 'high' ? 'var(--danger)' : val === 'medium' ? 'var(--warning)' : 'var(--text-secondary)';
                        cells += '<td style="font-weight:600;color:' + pcolor + '">' + val + '</td>';
                    {rb} else if (f === 'created_at') {lb}
                        cells += '<td>' + new Date(val).toLocaleDateString() + '</td>';
                    {rb} else {lb}
                        cells += '<td>' + val + '</td>';
                    {rb}
                {rb});
                let actionBtns = '';
                if (row.status === 'pending') {lb}
                    if (ent.actions.includes('approve')) actionBtns += '<button class="btn btn-success btn-sm" onclick="doAction(&#39;' + ent.slug + '&#39;,&#39;' + row.id + '&#39;,&#39;approve&#39;)">Approve</button> ';
                    if (ent.actions.includes('reject')) actionBtns += '<button class="btn btn-danger btn-sm" onclick="doAction(&#39;' + ent.slug + '&#39;,&#39;' + row.id + '&#39;,&#39;reject&#39;)">Reject</button> ';
                {rb}
                if (row.status === 'approved' && ent.actions.includes('process')) {lb}
                    actionBtns += '<button class="btn btn-warning btn-sm" onclick="doAction(&#39;' + ent.slug + '&#39;,&#39;' + row.id + '&#39;,&#39;process&#39;)">Process</button> ';
                {rb}
                if (['pending','approved','in_progress'].includes(row.status) && ent.actions.includes('escalate')) {lb}
                    actionBtns += '<button class="btn btn-sm" style="background:#7b1fa2;color:white" onclick="doAction(&#39;' + ent.slug + '&#39;,&#39;' + row.id + '&#39;,&#39;escalate&#39;)">Escalate</button> ';
                {rb}
                if (!actionBtns) actionBtns = '<span style="color:var(--text-secondary);font-size:12px">No actions</span>';
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
                if (k === 'status') display = '<span class="badge badge-' + String(v).replace(/ /g,'-') + '">' + v + '</span>';
                if (k === 'amount') display = '$' + Number(v).toFixed(2);
                html += '<div class="detail-row"><div class="dl">' + label + '</div><div>' + display + '</div></div>';
            {rb});
            document.getElementById('detailBody').innerHTML = html;

            // Action buttons in detail
            let actionsHtml = '<button class="btn" onclick="closeDetail()">Close</button>';
            if (row.status === 'pending') {lb}
                if (ent.actions.includes('approve')) actionsHtml += ' <button class="btn btn-success" onclick="doAction(&#39;' + slug + '&#39;,&#39;' + id + '&#39;,&#39;approve&#39;);closeDetail()">Approve</button>';
                if (ent.actions.includes('reject')) actionsHtml += ' <button class="btn btn-danger" onclick="doAction(&#39;' + slug + '&#39;,&#39;' + id + '&#39;,&#39;reject&#39;);closeDetail()">Reject</button>';
            {rb}
            if (row.status === 'approved' && ent.actions.includes('process')) {lb}
                actionsHtml += ' <button class="btn btn-warning" onclick="doAction(&#39;' + slug + '&#39;,&#39;' + id + '&#39;,&#39;process&#39;);closeDetail()">Process</button>';
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
        return raw.replace(lb, lb * 2).replace(rb, rb * 2)

    def _python_v1_schemas(self, spec: IntentSpec) -> str:
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC

        # Dynamic generation when entities come from intent parsing
        if _has_custom_entities(spec):
            return self._dynamic_schemas(spec)

        # Base schemas always included for backward compatibility
        base = '''"""API v1 request/response schemas.

Keep Pydantic models here so routers stay thin.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Schema for creating a new item."""

    name: str = Field(..., min_length=1, max_length=120, description="Item name")
    description: str = Field(default="", max_length=500, description="Item description")


class ItemResponse(BaseModel):
    """Schema returned by item endpoints."""

    id: str = Field(..., description="Unique item identifier")
    name: str = Field(..., description="Item name")
    description: str = Field(default="", description="Item description")
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
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC

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


class ItemService:
    """Generic CRUD domain service with repository-backed persistence."""

    def __init__(self, project_name: str = "{spec.project_name}", repo: BaseRepository | None = None) -> None:
        self.project_name = project_name
        self.repo = repo

    def list_items(self) -> list[dict]:
        """Return all items from the repository."""
        if self.repo:
            return self.repo.list_all()
        return [
            {{
                "id": "sample-001",
                "name": "Example Item",
                "description": "Replace this stub with your data store query.",
                "project": self.project_name,
            }}
        ]

    def create_item(self, name: str, description: str = "") -> dict:
        """Create and return a new item."""
        item = {{
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "project": self.project_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }}
        if self.repo:
            self.repo.create(item["id"], item)
        return item

    def get_item(self, item_id: str) -> dict | None:
        """Get a single item by ID."""
        if self.repo:
            return self.repo.get(item_id)
        return None

    def update_item(self, item_id: str, name: str | None = None, description: str | None = None) -> dict | None:
        """Update an existing item."""
        if not self.repo:
            return None
        item = self.repo.get(item_id)
        if not item:
            return None
        if name is not None:
            item["name"] = name
        if description is not None:
            item["description"] = description
        item["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.repo.update(item_id, item)
        return item

    def delete_item(self, item_id: str) -> bool:
        """Delete an item by ID."""
        if self.repo:
            return self.repo.delete(item_id)
        return False
'''

    # ===============================================================
    # Domain layer file generators
    # ===============================================================

    def _python_domain_models(self, spec: IntentSpec) -> str:
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC

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
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC

        if _has_custom_entities(spec):
            return self._dynamic_seed_data(spec)

        # Generic
        return '''"""Seed data -- generic demo records."""

from __future__ import annotations

_SEED: dict[str, list[dict]] = {
    "item": [
        {"id": "item-001", "name": "Example Widget", "description": "A sample product item", "status": "active", "project": "demo", "created_at": "2024-03-15T08:00:00Z"},
        {"id": "item-002", "name": "Test Service", "description": "A sample service offering", "status": "active", "project": "demo", "created_at": "2024-03-15T09:00:00Z"},
        {"id": "item-003", "name": "Draft Report", "description": "Quarterly financial summary", "status": "draft", "project": "demo", "created_at": "2024-03-15T10:00:00Z"},
        {"id": "item-004", "name": "Archived Task", "description": "Completed migration task", "status": "archived", "project": "demo", "created_at": "2024-03-14T14:00:00Z"},
        {"id": "item-005", "name": "Pending Review", "description": "Code review for feature branch", "status": "pending", "project": "demo", "created_at": "2024-03-15T11:00:00Z"},
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
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC

        if _has_custom_entities(spec):
            return self._dynamic_node_services(spec)

        # Generic
        return """const { v4: uuid } = require("uuid");
const { seedData } = require("./data");

const db = { items: { ...seedData.items } };

class ItemService {
  list() { return Object.values(db.items); }
  get(id) { return db.items[id] || null; }
  create({ name, description }) {
    const item = { id: uuid(), name, description: description || "", project: "default", created_at: new Date().toISOString() };
    db.items[item.id] = item;
    return item;
  }
  update(id, { name, description }) {
    const item = db.items[id];
    if (!item) return null;
    if (name !== undefined) item.name = name;
    if (description !== undefined) item.description = description;
    return item;
  }
  delete(id) { const existed = !!db.items[id]; delete db.items[id]; return existed; }
}

module.exports = { ItemService };
"""

    def _node_seed_data(self, spec: IntentSpec) -> str:
        """Generate seed data for Node.js."""
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC

        if _has_custom_entities(spec):
            return self._dynamic_node_seed_data(spec)

        return """const seedData = {
  items: {
    "i1": { id: "i1", name: "Sample Item 1", description: "First demo item", project: "default", created_at: "2024-01-01T00:00:00Z" },
    "i2": { id: "i2", name: "Sample Item 2", description: "Second demo item", project: "default", created_at: "2024-01-02T00:00:00Z" },
    "i3": { id: "i3", name: "Sample Item 3", description: "Third demo item", project: "default", created_at: "2024-01-03T00:00:00Z" },
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
                    val = _seed_value(f, ent.name, rid)
                    parts.append(f'{f.name}: {val}')
                parts.append(f'created_at: "2024-03-{10+rid}T0{8+rid}:00:00Z"')
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
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC

        if _has_custom_entities(spec):
            return self._dynamic_dotnet_services(spec)

        # Generic
        return """// Domain Services -- Generic CRUD
using System.Collections.Concurrent;

namespace App.Services;

public record Item(string Id, string Name, string Description, string Project, DateTime CreatedAt);

public class ItemService
{
    private readonly ConcurrentDictionary<string, Item> _items = new();

    public ItemService(SeedData seed) { foreach (var i in seed.Items) _items[i.Id] = i; }
    public IEnumerable<Item> List() => _items.Values;
    public Item? Get(string id) => _items.GetValueOrDefault(id);
    public Item Create(string name, string? description = null) { var i = new Item(Guid.NewGuid().ToString(), name, description ?? "", "default", DateTime.UtcNow); _items[i.Id] = i; return i; }
    public Item? Update(string id, string name, string? description = null) { if (!_items.TryGetValue(id, out var old)) return null; var u = old with { Name = name, Description = description ?? old.Description }; _items[id] = u; return u; }
    public bool Delete(string id) => _items.TryRemove(id, out _);
}
"""

    def _dotnet_seed_data(self, spec: IntentSpec) -> str:
        """Generate seed data for .NET."""
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC

        if _has_custom_entities(spec):
            return self._dynamic_dotnet_seed_data(spec)

        return """// Seed Data -- Generic
namespace App.Services;

public class SeedData
{
    public List<Item> Items { get; } = new()
    {
        new("i1", "Sample Item 1", "First demo item", "default", DateTime.Parse("2024-01-01T00:00:00Z")),
        new("i2", "Sample Item 2", "Second demo item", "default", DateTime.Parse("2024-01-02T00:00:00Z")),
        new("i3", "Sample Item 3", "Third demo item", "default", DateTime.Parse("2024-01-03T00:00:00Z")),
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
                parts.append(f'DateTime.Parse("2024-03-{10+rid}T0{8+rid}:00:00Z")')
                lines.append(f'        new({", ".join(parts)}),')
            lines.append('    };')
        lines.append('}')
        lines.append('')
        return "\n".join(lines)
