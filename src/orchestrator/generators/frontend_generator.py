"""Frontend Generator -- produces React + Vite + TypeScript SPA.

Generates a modern React application with:
    - Vite build tooling
    - TypeScript configuration
    - Domain-specific pages and components
    - API client with typed endpoints
    - Responsive dashboard UI
    - TailwindCSS styling via CDN
"""

from __future__ import annotations

import re as _re

from src.orchestrator.intent_schema import IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


# -- Helpers for dynamic frontend generation ---------------------------

def _snake(name: str) -> str:
    """PascalCase -> snake_case."""
    return _re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name).lower()


def _plural(name: str) -> str:
    """Simple English pluralizer."""
    lower = name.lower()
    if lower.endswith("y") and lower[-2:] not in ("ay", "ey", "oy", "uy"):
        return name[:-1] + "ies"
    if lower.endswith(("s", "sh", "ch", "x", "z")):
        return name + "es"
    return name + "s"


def _has_custom_entities(spec: IntentSpec) -> bool:
    """Return True if spec has any entities (including fallback Resource)."""
    return bool(spec.entities)


_TS_TYPE_MAP = {
    "str": "string", "int": "number", "float": "number",
    "bool": "boolean", "list": "string[]", "list[str]": "string[]",
    "dict": "Record<string, any>", "datetime": "string",
}


def _ts_type(python_type: str) -> str:
    """Map Python type to TypeScript type."""
    return _TS_TYPE_MAP.get(python_type, "string")


class FrontendGenerator:
    """Generates a React + Vite + TypeScript SPA frontend."""

    def generate(self, spec: IntentSpec) -> dict[str, str]:
        """Return file-path -> content mapping for the frontend SPA."""
        project = spec.project_name

        files: dict[str, str] = {}

        # -- Build / config files --
        files["frontend/package.json"] = self._package_json(project)
        files["frontend/tsconfig.json"] = self._tsconfig()
        files["frontend/tsconfig.node.json"] = self._tsconfig_node()
        files["frontend/vite.config.ts"] = self._vite_config()
        files["frontend/index.html"] = self._index_html(project)

        # -- Source files --
        files["frontend/src/main.tsx"] = self._main_tsx()
        files["frontend/src/App.tsx"] = self._app_tsx(spec)
        files["frontend/src/api/client.ts"] = self._api_client(spec)
        files["frontend/src/types/index.ts"] = self._types(spec)
        files["frontend/src/components/Layout.tsx"] = self._layout(project, spec)
        files["frontend/src/components/StatusBadge.tsx"] = self._status_badge()
        files["frontend/src/pages/Dashboard.tsx"] = self._dashboard(spec)
        files["frontend/src/pages/DetailPage.tsx"] = self._detail_page(spec)

        # -- AI Chat page (when uses_ai is True) --
        if spec.uses_ai:
            files["frontend/src/pages/ChatPage.tsx"] = self._chat_page(spec)

        # -- Static / env --
        files["frontend/.env"] = f'VITE_API_BASE_URL=/api/v1\nVITE_APP_TITLE="{project}"\n'
        files["frontend/Dockerfile"] = self._dockerfile()
        files["frontend/docker-entrypoint.sh"] = self._docker_entrypoint()

        logger.info("FrontendGenerator produced %d files", len(files))
        return files

    # ================================================================
    # Config / build files
    # ================================================================

    def _package_json(self, project: str) -> str:
        return f'''{{"name": "{project}-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.3",
    "vite": "^5.4.0"
  }}
}}
'''

    def _tsconfig(self) -> str:
        return """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
"""

    def _tsconfig_node(self) -> str:
        return """{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
"""

    def _vite_config(self) -> str:
        return """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
"""

    def _index_html(self, project: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
      body {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; }}
    </style>
  </head>
  <body class="bg-gray-50 text-gray-900">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

    # ================================================================
    # Source files
    # ================================================================

    def _main_tsx(self) -> str:
        return """import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
"""

    def _app_tsx(self, spec: IntentSpec) -> str:
        chat_import = ""
        chat_route = ""
        if spec.uses_ai:
            chat_import = "import ChatPage from './pages/ChatPage';"
            chat_route = '        <Route path="/chat" element={<ChatPage />} />'

        return f"""import {{ Routes, Route }} from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DetailPage from './pages/DetailPage';
{chat_import}

export default function App() {{
  return (
    <Layout>
      <Routes>
        <Route path="/" element={{<Dashboard />}} />
        <Route path="/detail/:id" element={{<DetailPage />}} />
{chat_route}
      </Routes>
    </Layout>
  );
}}
"""

    def _api_client(self, spec: IntentSpec) -> str:
        base = """const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

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

"""
        # Always use the dynamic API client when entities exist
        if _has_custom_entities(spec):
            base += self._dynamic_api_client(spec)
        else:
            _slug = "resources"
            base += f"""// Generic CRUD API
export const api = {{
  listResources: () => request<any[]>('/{_slug}'),
  getResource: (id: string) => request<any>(`/{_slug}/${{id}}`),
  createResource: (data: any) =>
    request<any>('/{_slug}', {{ method: 'POST', body: JSON.stringify(data) }}),
  updateResource: (id: string, data: any) =>
    request<any>(`/{_slug}/${{id}}`, {{ method: 'PUT', body: JSON.stringify(data) }}),
  deleteResource: (id: string) =>
    request<void>(`/{_slug}/${{id}}`, {{ method: 'DELETE' }}),
}};
"""
        return base

    def _types(self, spec: IntentSpec) -> str:
        base = "// Shared TypeScript type definitions\n\n"
        # Always use dynamic types when entities exist
        if _has_custom_entities(spec):
            base += self._dynamic_types(spec)
        else:
            base += """export interface Resource {
  id: string;
  name: string;
  description: string;
  status: string;
}

"""
        return base

    def _layout(self, project: str, spec: IntentSpec | None = None) -> str:
        chat_link = ''
        if spec and spec.uses_ai:
            chat_link = '\n            <Link to="/chat" className="hover:underline">AI Chat</Link>'
        return f"""import {{ ReactNode }} from 'react';
import {{ Link }} from 'react-router-dom';

export default function Layout({{ children }}: {{ children: ReactNode }}) {{
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gradient-to-r from-blue-700 to-indigo-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold tracking-tight hover:opacity-90">
            {project}
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link to="/" className="hover:underline">Dashboard</Link>{chat_link}
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8">
        {{children}}
      </main>
      <footer className="bg-gray-100 border-t text-center text-xs text-gray-500 py-3">
        {project} &mdash; Enterprise DevEx Orchestrator
      </footer>
    </div>
  );
}}
"""

    def _status_badge(self) -> str:
        return """const colors: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  completed: 'bg-blue-100 text-blue-800',
  escalated: 'bg-red-100 text-red-800',
  scheduled: 'bg-yellow-100 text-yellow-800',
  cancelled: 'bg-gray-100 text-gray-600',
  pending: 'bg-orange-100 text-orange-800',
  approved: 'bg-emerald-100 text-emerald-800',
  uploaded: 'bg-purple-100 text-purple-800',
  analyzed: 'bg-indigo-100 text-indigo-800',
  draft: 'bg-gray-100 text-gray-600',
  archived: 'bg-gray-200 text-gray-500',
};

export default function StatusBadge({ status }: { status: string }) {
  const cls = colors[status] || 'bg-gray-100 text-gray-800';
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}
"""

    def _dashboard(self, spec: IntentSpec) -> str:
        # Always use the dynamic entity-driven dashboard
        if _has_custom_entities(spec):
            return self._dynamic_dashboard(spec)
        return """import { useEffect, useState } from 'react';

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="text-gray-500">No entities configured. Run the scaffold with an intent file to generate a full dashboard.</p>
    </div>
  );
}
"""

    def _detail_page(self, spec: IntentSpec) -> str:
        # Always use the dynamic entity-driven detail page
        if _has_custom_entities(spec):
            return self._dynamic_detail_page(spec)
        return """import { useParams, useNavigate } from 'react-router-dom';

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/')} className="text-blue-600 hover:underline text-sm">&larr; Back</button>
      <div className="bg-white rounded-xl shadow p-6">
        <h1 className="text-xl font-bold">Detail</h1>
        <p className="text-sm text-gray-500 mt-2">ID: {id}</p>
      </div>
    </div>
  );
}
"""

    def _dockerfile(self) -> str:
        return """# Multi-stage build for React SPA
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve with lightweight nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
# Default: Docker Compose service name. Override for Azure Container Apps:
#   docker run -e API_BACKEND_URL=https://<your-api>.azurecontainerapps.io ...
ENV API_BACKEND_URL=http://api:8000
EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]
"""

    def _docker_entrypoint(self) -> str:
        return """#!/bin/sh
# Generate nginx config with the API backend URL from environment
cat > /etc/nginx/conf.d/default.conf <<EOF
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \\$uri \\$uri/ /index.html;
    }

    location /api/ {
        proxy_pass ${API_BACKEND_URL};
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
    }
}
EOF
exec nginx -g 'daemon off;'
"""

    # ================================================================
    # Dynamic entity-driven generation (domain-agnostic)
    # ================================================================

    def _dynamic_tab_config(self, spec: IntentSpec) -> str:
        """Generate TypeScript tabConfig object from spec.entities."""
        lines = ["const tabConfig: Record<string, any> = {"]
        for ent in spec.entities:
            slug = _snake(_plural(ent.name))
            # Build columns: id first, then entity fields (deduped)
            columns = ["id"]
            seen = {"id"}
            for f in ent.fields:
                if f.name not in seen:
                    columns.append(f.name)
                    seen.add(f.name)
            headers = [c.replace("_", " ").title() for c in columns]
            has_status = any(f.name == "status" for f in ent.fields)

            # Collect action endpoints
            actions: list[str] = []
            for ep in (spec.endpoints or []):
                parts = ep.path.strip("/").split("/")
                if (len(parts) >= 3 and ep.method == "POST"
                        and parts[0] == slug and parts[-1] not in ("", slug)):
                    action = parts[-1]
                    if action not in actions:
                        actions.append(action)

            lines.append(f"  '{slug}': {{")
            lines.append(f"    label: '{_plural(ent.name)}',")
            lines.append(f"    entityName: '{ent.name}',")
            lines.append(f"    columns: {columns},")
            lines.append(f"    headers: {headers},")
            lines.append(f"    hasStatus: {'true' if has_status else 'false'},")
            lines.append(f"    actions: {actions},")
            lines.append("  },")
        lines.append("};")
        lines.append("const tabKeys = Object.keys(tabConfig);")
        return "\n".join(lines)

    def _dynamic_api_client(self, spec: IntentSpec) -> str:
        """Generate TypeScript API client from spec.entities."""
        lines = ["// Domain-specific API — auto-generated from business entities"]
        lines.append("export const api = {")

        for i, ent in enumerate(spec.entities):
            slug = _snake(_plural(ent.name))
            name = ent.name
            plural_name = _plural(name)
            has_status = any(f.name == "status" for f in ent.fields)

            if i > 0:
                lines.append("")
            lines.append(f"  // {name}")

            if has_status:
                lines.append(f"  list{plural_name}: (status?: string) =>")
                lines.append(f"    request<any[]>(status ? `/{slug}?status=${{status}}` : '/{slug}'),")
            else:
                lines.append(f"  list{plural_name}: () => request<any[]>('/{slug}'),")

            lines.append(f"  get{name}: (id: string) => request<any>(`/{slug}/${{id}}`),")
            lines.append(f"  create{name}: (data: any) =>")
            lines.append(f"    request<any>('/{slug}', {{ method: 'POST', body: JSON.stringify(data) }}),")

            # Action endpoints from spec.endpoints
            for ep in (spec.endpoints or []):
                parts = ep.path.strip("/").split("/")
                if (len(parts) >= 3 and ep.method == "POST"
                        and parts[0] == slug and parts[-1] not in ("", slug)):
                    action = parts[-1]
                    lines.append(f"  {action}{name}: (id: string) =>")
                    lines.append(f"    request<any>(`/{slug}/${{id}}/{action}`, {{ method: 'POST' }}),")

        lines.append("};")
        return "\n".join(lines)

    def _dynamic_types(self, spec: IntentSpec) -> str:
        """Generate TypeScript interfaces from spec.entities."""
        lines = ["// Domain-specific types — auto-generated from business entities", ""]
        for ent in spec.entities:
            lines.append(f"export interface {ent.name} {{")
            lines.append("  id: string;")
            for field in ent.fields:
                ts = _ts_type(field.type)
                opt = "?" if not field.required else ""
                lines.append(f"  {field.name}{opt}: {ts};")
            lines.append("}")
            lines.append("")
        return "\n".join(lines)

    def _dynamic_dashboard(self, spec: IntentSpec) -> str:
        """Generate a fully interactive, entity-driven Dashboard component."""
        tab_config = self._dynamic_tab_config(spec)
        # The Dashboard component is static — only tabConfig varies
        return (
            "import { useEffect, useState } from 'react';\n"
            "import { Link } from 'react-router-dom';\n"
            "import StatusBadge from '../components/StatusBadge';\n"
            "\n"
            + tab_config + "\n\n"
            + _DASHBOARD_COMPONENT
        )

    def _dynamic_detail_page(self, spec: IntentSpec) -> str:
        """Generate an entity-driven DetailPage component."""
        tab_config = self._dynamic_tab_config(spec)
        return (
            "import { useEffect, useState } from 'react';\n"
            "import { useParams, useNavigate, useSearchParams } from 'react-router-dom';\n"
            "import StatusBadge from '../components/StatusBadge';\n"
            "\n"
            + tab_config + "\n\n"
            + _DETAIL_PAGE_COMPONENT
        )

    def _chat_page(self, spec: IntentSpec) -> str:
        """Generate an AI chat interface page."""
        project = spec.project_name
        return f"""import {{ useState, useRef, useEffect }} from 'react';

interface Message {{
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export default function ChatPage() {{
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {{
    bottomRef.current?.scrollIntoView({{ behavior: 'smooth' }});
  }}, [messages]);

  const sendMessage = async () => {{
    if (!input.trim() || loading) return;

    const userMsg: Message = {{
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }};

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {{
      const res = await fetch(`${{API_BASE}}/ai/chat`, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          message: userMsg.content,
          history: messages.map((m) => ({{ role: m.role, content: m.content }})),
        }}),
      }});
      const data = await res.json();
      const assistantMsg: Message = {{
        role: 'assistant',
        content: data.reply || 'No response',
        timestamp: new Date().toISOString(),
      }};
      setMessages((prev) => [...prev, assistantMsg]);
    }} catch (err) {{
      setMessages((prev) => [
        ...prev,
        {{ role: 'assistant', content: 'Error: Could not reach AI service.', timestamp: new Date().toISOString() }},
      ]);
    }} finally {{
      setLoading(false);
    }}
  }};

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">{project} AI Assistant</h1>
        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
          AI Powered
        </span>
      </div>

      {{/* Chat messages */}}
      <div className="flex-1 overflow-y-auto bg-gray-50 rounded-lg border p-4 space-y-4">
        {{messages.length === 0 && (
          <div className="text-center text-gray-400 py-12">
            <p className="text-lg">Welcome to {project} AI Assistant</p>
            <p className="text-sm mt-2">Ask a question to get started.</p>
          </div>
        )}}
        {{messages.map((msg, i) => (
          <div key={{i}} className={{`flex ${{msg.role === 'user' ? 'justify-end' : 'justify-start'}}`}}>
            <div
              className={{`max-w-[70%] rounded-lg px-4 py-2 ${{
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border text-gray-900'
              }}`}}
            >
              <p className="whitespace-pre-wrap">{{msg.content}}</p>
              <p className={{`text-xs mt-1 ${{msg.role === 'user' ? 'text-blue-200' : 'text-gray-400'}}`}}>
                {{new Date(msg.timestamp).toLocaleTimeString()}}
              </p>
            </div>
          </div>
        ))}}
        {{loading && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-lg px-4 py-2 text-gray-500">
              Thinking...
            </div>
          </div>
        )}}
        <div ref={{bottomRef}} />
      </div>

      {{/* Input area */}}
      <div className="mt-4 flex gap-2">
        <input
          type="text"
          value={{input}}
          onChange={{(e) => setInput(e.target.value)}}
          onKeyDown={{(e) => e.key === 'Enter' && sendMessage()}}
          placeholder="Type your message..."
          className="flex-1 border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          disabled={{loading}}
        />
        <button
          onClick={{sendMessage}}
          disabled={{loading || !input.trim()}}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </div>
  );
}}
"""


# ====================================================================
# Static component templates used by dynamic generators
# ====================================================================

_DASHBOARD_COMPONENT = r"""const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

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
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
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
"""

_DETAIL_PAGE_COMPONENT = r"""const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

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
"""
