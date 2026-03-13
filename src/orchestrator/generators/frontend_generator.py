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

from src.orchestrator.intent_schema import DomainType, IntentSpec
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
    """Return True if spec has domain-specific entities (not just default Item)."""
    if not spec.entities:
        return False
    if len(spec.entities) == 1 and spec.entities[0].name == "Item":
        return False
    return True


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
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC
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
        files["frontend/src/components/Layout.tsx"] = self._layout(project)
        files["frontend/src/components/StatusBadge.tsx"] = self._status_badge()
        files["frontend/src/pages/Dashboard.tsx"] = self._dashboard(spec)
        files["frontend/src/pages/DetailPage.tsx"] = self._detail_page(spec)

        # -- Static / env --
        files["frontend/.env"] = f'VITE_API_BASE_URL=http://localhost:8000/api/v1\nVITE_APP_TITLE="{project}"\n'
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
        return """import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DetailPage from './pages/DetailPage';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/detail/:id" element={<DetailPage />} />
      </Routes>
    </Layout>
  );
}
"""

    def _api_client(self, spec: IntentSpec) -> str:
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC
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
        if domain == DomainType.HEALTHCARE:
            base += """// Healthcare API
export const api = {
  listSessions: (status?: string) =>
    request<any[]>(status ? `/sessions?status=${status}` : '/sessions'),
  getSession: (id: string) => request<any>(`/sessions/${id}`),
  createSession: (data: { patient_id: string; intent?: string }) =>
    request<any>('/sessions', { method: 'POST', body: JSON.stringify(data) }),
  endSession: (id: string) =>
    request<any>(`/sessions/${id}/end`, { method: 'POST' }),
  escalateSession: (id: string, reason?: string) =>
    request<any>(`/sessions/${id}/escalate?reason=${encodeURIComponent(reason || '')}`, { method: 'POST' }),

  listAppointments: (patientId?: string) =>
    request<any[]>(patientId ? `/appointments?patient_id=${patientId}` : '/appointments'),
  bookAppointment: (data: { patient_id: string; provider: string; date_time: string; reason?: string }) =>
    request<any>('/appointments', { method: 'POST', body: JSON.stringify(data) }),

  listRefills: (patientId?: string) =>
    request<any[]>(patientId ? `/prescriptions/refills?patient_id=${patientId}` : '/prescriptions/refills'),
  requestRefill: (data: { patient_id: string; medication: string; pharmacy?: string }) =>
    request<any>('/prescriptions/refills', { method: 'POST', body: JSON.stringify(data) }),

  listItems: () => request<any[]>('/items'),
};
"""
        elif domain == DomainType.LEGAL:
            base += """// Legal / Contract Review API
export const api = {
  listContracts: (status?: string) =>
    request<any[]>(status ? `/contracts?status=${status}` : '/contracts'),
  getContract: (id: string) => request<any>(`/contracts/${id}`),
  uploadContract: (data: { title: string; parties: string[] }) =>
    request<any>('/contracts', { method: 'POST', body: JSON.stringify(data) }),
  analyzeContract: (id: string) =>
    request<any>(`/contracts/${id}/analyze`, { method: 'POST' }),
  getRisk: (id: string) => request<any>(`/contracts/${id}/risk`),

  listItems: () => request<any[]>('/items'),
};
"""
        elif domain == DomainType.DOCUMENT_PROCESSING:
            base += """// Document Processing API
export const api = {
  listAnalyses: (status?: string) =>
    request<any[]>(status ? `/analyses?status=${status}` : '/analyses'),
  getAnalysis: (id: string) => request<any>(`/analyses/${id}`),
  submitDocument: (data: { document_name: string; model_id?: string }) =>
    request<any>('/analyses', { method: 'POST', body: JSON.stringify(data) }),
  getExtractions: (id: string) => request<any>(`/analyses/${id}/extractions`),
  listModels: () => request<any[]>('/models'),

  listItems: () => request<any[]>('/items'),
};
"""
        else:
            if _has_custom_entities(spec):
                base += self._dynamic_api_client(spec)
            else:
                base += """// Generic CRUD API
export const api = {
  listItems: () => request<any[]>('/items'),
  getItem: (id: string) => request<any>(`/items/${id}`),
  createItem: (data: { name: string; description?: string }) =>
    request<any>('/items', { method: 'POST', body: JSON.stringify(data) }),
  updateItem: (id: string, data: { name: string; description?: string }) =>
    request<any>(`/items/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteItem: (id: string) =>
    request<void>(`/items/${id}`, { method: 'DELETE' }),
};
"""
        return base

    def _types(self, spec: IntentSpec) -> str:
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC
        base = """// Shared TypeScript type definitions

export interface Item {
  id: string;
  name: string;
  description: string;
  project: string;
}

"""
        if domain == DomainType.HEALTHCARE:
            base += """export interface Session {
  id: string;
  patient_id: string;
  status: 'active' | 'completed' | 'escalated';
  intent_detected: string;
  transcript: string[];
  escalation_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  provider: string;
  date_time: string;
  reason: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  created_at: string;
}

export interface PrescriptionRefill {
  id: string;
  patient_id: string;
  medication: string;
  pharmacy: string;
  status: 'pending' | 'approved' | 'denied';
  created_at: string;
}
"""
        elif domain == DomainType.LEGAL:
            base += """export interface Contract {
  id: string;
  title: string;
  parties: string[];
  status: 'uploaded' | 'analyzed';
  risk_score: number | null;
  created_at: string;
}

export interface Clause {
  id: string;
  contract_id: string;
  category: string;
  text: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  recommendation: string;
}

export interface RiskReport {
  contract_id: string;
  overall_score: number;
  clause_count: number;
  categories: Record<string, number>;
  summary: string;
}
"""
        elif domain == DomainType.DOCUMENT_PROCESSING:
            base += """export interface AnalysisResult {
  id: string;
  document_name: string;
  model_id: string;
  status: string;
  confidence: number;
  page_count: number;
  created_at: string;
}

export interface ExtractedTable {
  id: string;
  analysis_id: string;
  page_number: number;
  column_headers: string[];
  rows: string[][];
}

export interface KeyValuePair {
  id: string;
  analysis_id: string;
  key: string;
  value: string;
  confidence: number;
}
"""
        if _has_custom_entities(spec):
            base += self._dynamic_types(spec)
        return base

    def _layout(self, project: str) -> str:
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
            <Link to="/" className="hover:underline">Dashboard</Link>
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
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC
        if domain == DomainType.HEALTHCARE:
            return """import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function Dashboard() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [appointments, setAppointments] = useState<any[]>([]);
  const [refills, setRefills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.listSessions(), api.listAppointments(), api.listRefills()])
      .then(([s, a, r]) => { setSessions(s); setAppointments(a); setRefills(r); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Healthcare Voice Agent Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Active Sessions</p>
          <p className="text-3xl font-bold text-blue-700">{sessions.filter(s => s.status === 'active').length}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Upcoming Appointments</p>
          <p className="text-3xl font-bold text-green-700">{appointments.filter(a => a.status === 'scheduled').length}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Pending Refills</p>
          <p className="text-3xl font-bold text-orange-600">{refills.filter(r => r.status === 'pending').length}</p>
        </div>
      </div>

      {/* Sessions table */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Recent Sessions</h2>
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Patient</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Intent</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sessions.map(s => (
                <tr key={s.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm"><Link to={`/detail/${s.id}`} className="text-blue-600 hover:underline">{s.id.slice(0,8)}</Link></td>
                  <td className="px-4 py-3 text-sm">{s.patient_id}</td>
                  <td className="px-4 py-3 text-sm">{s.intent_detected}</td>
                  <td className="px-4 py-3"><StatusBadge status={s.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Appointments */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Appointments</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {appointments.map(a => (
            <div key={a.id} className="bg-white rounded-xl shadow p-4">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-medium">{a.provider}</p>
                  <p className="text-sm text-gray-500">{a.reason}</p>
                </div>
                <StatusBadge status={a.status} />
              </div>
              <p className="text-xs text-gray-400 mt-2">{new Date(a.date_time).toLocaleString()}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
"""

        if domain == DomainType.LEGAL:
            return """import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function Dashboard() {
  const [contracts, setContracts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listContracts().then(setContracts).finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;

  const analyzed = contracts.filter(c => c.status === 'analyzed');
  const avgRisk = analyzed.length
    ? (analyzed.reduce((s, c) => s + (c.risk_score || 0), 0) / analyzed.length).toFixed(1)
    : '—';

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Contract Review Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Total Contracts</p>
          <p className="text-3xl font-bold text-blue-700">{contracts.length}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Analyzed</p>
          <p className="text-3xl font-bold text-green-700">{analyzed.length}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Avg Risk Score</p>
          <p className="text-3xl font-bold text-orange-600">{avgRisk}</p>
        </div>
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-3">Contracts</h2>
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Parties</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {contracts.map(c => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">
                    <Link to={`/detail/${c.id}`} className="text-blue-600 hover:underline">{c.title}</Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{(c.parties || []).join(', ')}</td>
                  <td className="px-4 py-3 text-sm font-medium">{c.risk_score != null ? c.risk_score : '—'}</td>
                  <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
"""

        if domain == DomainType.DOCUMENT_PROCESSING:
            return """import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function Dashboard() {
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listAnalyses().then(setAnalyses).finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;

  const avgConfidence = analyses.length
    ? (analyses.reduce((s, a) => s + a.confidence, 0) / analyses.length * 100).toFixed(1)
    : '—';

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Document Intelligence Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Documents Processed</p>
          <p className="text-3xl font-bold text-blue-700">{analyses.length}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Avg Confidence</p>
          <p className="text-3xl font-bold text-green-700">{avgConfidence}%</p>
        </div>
        <div className="bg-white rounded-xl shadow p-6">
          <p className="text-sm text-gray-500">Total Pages</p>
          <p className="text-3xl font-bold text-purple-700">{analyses.reduce((s, a) => s + a.page_count, 0)}</p>
        </div>
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-3">Recent Analyses</h2>
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Document</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {analyses.map(a => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">
                    <Link to={`/detail/${a.id}`} className="text-blue-600 hover:underline">{a.document_name}</Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{a.model_id}</td>
                  <td className="px-4 py-3 text-sm font-medium">{(a.confidence * 100).toFixed(1)}%</td>
                  <td className="px-4 py-3"><StatusBadge status={a.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
"""

        # Generic -- use dynamic dashboard if entities found
        if _has_custom_entities(spec):
            return self._dynamic_dashboard(spec)
        return """import { useEffect, useState } from 'react';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function Dashboard() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');

  useEffect(() => {
    api.listItems().then(setItems).finally(() => setLoading(false));
  }, []);

  const handleCreate = async () => {
    if (!name.trim()) return;
    const item = await api.createItem({ name, description: desc });
    setItems(prev => [...prev, item]);
    setName('');
    setDesc('');
  };

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Create Item</h2>
        <div className="flex gap-3">
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Name"
            className="flex-1 border rounded-lg px-3 py-2 text-sm" />
          <input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Description"
            className="flex-1 border rounded-lg px-3 py-2 text-sm" />
          <button onClick={handleCreate}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
            Add
          </button>
        </div>
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-3">Items</h2>
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {items.map(i => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-mono text-gray-500">{i.id.slice(0,8)}</td>
                  <td className="px-4 py-3 text-sm font-medium">{i.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{i.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
"""

    def _detail_page(self, spec: IntentSpec) -> str:
        domain = spec.domain_type if hasattr(spec, "domain_type") else DomainType.GENERIC
        if domain == DomainType.HEALTHCARE:
            return """import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) api.getSession(id).then(setSession).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;
  if (!session) return <p className="text-center py-12 text-red-500">Session not found</p>;

  const handleEnd = async () => {
    const updated = await api.endSession(session.id);
    setSession(updated);
  };

  const handleEscalate = async () => {
    const updated = await api.escalateSession(session.id, 'Escalated from dashboard');
    setSession(updated);
  };

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/')} className="text-blue-600 hover:underline text-sm">&larr; Back</button>
      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold">Session {session.id.slice(0,8)}</h1>
          <StatusBadge status={session.status} />
        </div>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div><dt className="text-gray-500">Patient ID</dt><dd className="font-medium">{session.patient_id}</dd></div>
          <div><dt className="text-gray-500">Intent</dt><dd className="font-medium">{session.intent_detected || '—'}</dd></div>
          <div><dt className="text-gray-500">Created</dt><dd>{new Date(session.created_at).toLocaleString()}</dd></div>
          <div><dt className="text-gray-500">Updated</dt><dd>{new Date(session.updated_at).toLocaleString()}</dd></div>
        </dl>
        {session.status === 'active' && (
          <div className="mt-6 flex gap-3">
            <button onClick={handleEnd} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">End Session</button>
            <button onClick={handleEscalate} className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700">Escalate</button>
          </div>
        )}
      </div>
    </div>
  );
}
"""

        if domain == DomainType.LEGAL:
            return """import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [contract, setContract] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      Promise.all([api.getContract(id), api.getRisk(id)])
        .then(([c, r]) => { setContract(c); setRisk(r); })
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;
  if (!contract) return <p className="text-center py-12 text-red-500">Contract not found</p>;

  const handleAnalyze = async () => {
    const result = await api.analyzeContract(contract.id);
    setContract(result.contract);
  };

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/')} className="text-blue-600 hover:underline text-sm">&larr; Back</button>
      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold">{contract.title}</h1>
          <StatusBadge status={contract.status} />
        </div>
        <p className="text-sm text-gray-600 mb-4">Parties: {(contract.parties || []).join(', ')}</p>
        {contract.risk_score != null && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
            <p className="text-sm font-medium text-orange-800">Risk Score: {contract.risk_score}</p>
          </div>
        )}
        {contract.status === 'uploaded' && (
          <button onClick={handleAnalyze} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700">
            Analyze Contract
          </button>
        )}
      </div>
      {risk && risk.clause_count > 0 && (
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold mb-3">Risk Assessment</h2>
          <p className="text-sm text-gray-600 mb-2">{risk.summary}</p>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(risk.categories || {}).map(([cat, score]) => (
              <div key={cat} className="flex justify-between text-sm bg-gray-50 rounded px-3 py-2">
                <span>{cat}</span>
                <span className="font-medium">{String(score)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
"""

        if domain == DomainType.DOCUMENT_PROCESSING:
            return """import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<any>(null);
  const [extractions, setExtractions] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      Promise.all([api.getAnalysis(id), api.getExtractions(id)])
        .then(([a, e]) => { setAnalysis(a); setExtractions(e); })
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;
  if (!analysis) return <p className="text-center py-12 text-red-500">Analysis not found</p>;

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/')} className="text-blue-600 hover:underline text-sm">&larr; Back</button>
      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold">{analysis.document_name}</h1>
          <StatusBadge status={analysis.status} />
        </div>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div><dt className="text-gray-500">Model</dt><dd className="font-medium">{analysis.model_id}</dd></div>
          <div><dt className="text-gray-500">Confidence</dt><dd className="font-medium">{(analysis.confidence * 100).toFixed(1)}%</dd></div>
          <div><dt className="text-gray-500">Pages</dt><dd>{analysis.page_count}</dd></div>
          <div><dt className="text-gray-500">Processed</dt><dd>{new Date(analysis.created_at).toLocaleString()}</dd></div>
        </dl>
      </div>
      {extractions?.key_values?.length > 0 && (
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold mb-3">Extracted Fields</h2>
          <div className="space-y-2">
            {extractions.key_values.map((kv: any) => (
              <div key={kv.id} className="flex justify-between text-sm bg-gray-50 rounded px-3 py-2">
                <span className="font-medium">{kv.key}</span>
                <span>{kv.value} <span className="text-gray-400">({(kv.confidence * 100).toFixed(0)}%)</span></span>
              </div>
            ))}
          </div>
        </div>
      )}
      {extractions?.tables?.length > 0 && (
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold mb-3">Extracted Tables</h2>
          {extractions.tables.map((t: any) => (
            <table key={t.id} className="min-w-full divide-y divide-gray-200 mb-4">
              <thead className="bg-gray-50">
                <tr>{t.column_headers.map((h: string) => <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{h}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {t.rows.map((row: string[], i: number) => (
                  <tr key={i}>{row.map((cell, j) => <td key={j} className="px-3 py-2 text-sm">{cell}</td>)}</tr>
                ))}
              </tbody>
            </table>
          ))}
        </div>
      )}
    </div>
  );
}
"""

        # Generic -- use dynamic detail page if entities found
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
        <h1 className="text-xl font-bold">Item Detail</h1>
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


# ====================================================================
# Static component templates used by dynamic generators
# ====================================================================

_DASHBOARD_COMPONENT = r"""const API_BASE = '/api/v1';

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
"""

_DETAIL_PAGE_COMPONENT = r"""const API_BASE = '/api/v1';

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
