"""Frontend Generator -- produces React + Vite + TypeScript SPA.

Generates a modern React application with:
    - Vite build tooling
    - TypeScript configuration
    - Domain-specific pages and components
    - API client with typed endpoints
    - Design-system-driven responsive dashboard UI
    - Dark mode support with system preference detection
    - SVG icon library (Lucide-style, zero external deps)
    - Mini charts (SVG sparklines in KPI cards)
    - Loading skeletons with shimmer animation
    - Form validation with type-aware inputs
    - Table pagination and sortable columns
    - Toast notification system
    - Error boundary component
    - WCAG AA accessible (4.5:1 contrast, focus rings, reduced-motion)
    - HTML rendering in chat for LLM responses
    - CSP meta tag for security hardening
    - TailwindCSS styling via CDN + CSS custom property design tokens
"""

from __future__ import annotations

import re as _re

from src.orchestrator.generators.design_system import DesignSystem
from src.orchestrator.intent_schema import IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)

_design_system = DesignSystem()


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


# -- Column intelligence for smart dashboard rendering ----------------

_PRIORITY_NAMES = [
    'name', 'title', 'username', 'display_name', 'label',
    'status', 'severity', 'priority',
    'type', 'category', 'role', 'channel', 'route_type',
    'zone_type', 'asset_type', 'vehicle_type', 'sensor_type',
    'work_type', 'notification_type', 'query_type', 'event_type',
    'email', 'department',
]

_SKIP_DISPLAY = {
    'latitude', 'longitude', 'created_at', 'updated_at', 'created_by',
    'correlation_id', 'session_id', 'ip_address', 'vin_number',
    'firmware_version', 'calibration_date', 'protocol',
    'ai_triage_notes', 'ai_justification', 'ai_optimization_notes',
    'ai_trend_summary', 'ai_suggested_resolution', 'resolution_notes',
    'completion_notes', 'audio_transcript', 'last_message_preview',
    'prompt_text', 'completion_text', 'response_text', 'query_text',
    'sensor_ids', 'zone_ids', 'emergency_contacts', 'assigned_zones',
    'notification_preferences', 'content_safety_categories',
    'domain_entities_referenced', 'feedback_comment',
}


def _detect_field_type(name: str, python_type: str) -> str:
    """Detect rendering hint for a field."""
    if name in ('status', 'priority', 'severity'):
        return 'badge'
    if name.endswith('_id') and name != 'id':
        return 'id_ref'
    if name.endswith('_url') or name == 'action_url':
        return 'url'
    if name.endswith('_date') or name.endswith('_at') or name in (
        'install_date', 'scheduled_date',
    ):
        return 'date'
    if any(name.endswith(s) for s in (
        '_pct', '_score', '_level', '_percentage', '_index',
    )):
        return 'pct'
    if any(name.endswith(s) for s in (
        '_cost', '_revenue', '_price', '_budget', '_damage',
    )):
        return 'currency'
    if python_type == 'bool':
        return 'bool'
    if name == 'email' or name.endswith('_email'):
        return 'email'
    if name in ('latitude', 'longitude'):
        return 'latlng'
    if python_type in ('int', 'float') and not name.endswith('_id'):
        return 'number'
    return 'text'


def _select_display_columns(
    columns: list[str],
    field_types: dict[str, str],
) -> list[str]:
    """Select 5-7 key columns for table display."""
    display = ['id']
    remaining = [c for c in columns if c != 'id']

    # Phase 1: priority fields in order of importance
    for pname in _PRIORITY_NAMES:
        if pname in remaining and pname not in _SKIP_DISPLAY and len(display) < 7:
            display.append(pname)
            remaining.remove(pname)

    # Phase 2: fill with remaining visible fields
    for col in remaining:
        if len(display) >= 7:
            break
        if col not in _SKIP_DISPLAY and field_types.get(col) not in ('latlng',):
            display.append(col)

    return display


def _pretty_name(slug: str) -> str:
    """Convert kebab-case project slug to display name."""
    # Remove common suffixes
    clean = slug
    for suffix in ('-dev', '-staging', '-prod', '-output'):
        if clean.endswith(suffix):
            clean = clean[: -len(suffix)]
    # Truncate overly long names (from intent descriptions)
    parts = clean.split('-')
    if len(parts) > 5:
        parts = parts[:5]
    return ' '.join(p.capitalize() for p in parts)


class FrontendGenerator:
    """Generates a React + Vite + TypeScript SPA frontend."""

    def generate(self, spec: IntentSpec) -> dict[str, str]:
        """Return file-path -> content mapping for the frontend SPA."""
        project = spec.project_name
        tokens = _design_system.generate_tokens(spec)

        files: dict[str, str] = {}

        # -- Design system --
        files.update(_design_system.generate_design_spec(spec))

        # -- Build / config files --
        files["frontend/package.json"] = self._package_json(project)
        files["frontend/tsconfig.json"] = self._tsconfig()
        files["frontend/tsconfig.node.json"] = self._tsconfig_node()
        files["frontend/vite.config.ts"] = self._vite_config()
        files["frontend/index.html"] = self._index_html(project, tokens)

        # -- Source files --
        files["frontend/src/main.tsx"] = self._main_tsx()
        files["frontend/src/App.tsx"] = self._app_tsx(spec)
        files["frontend/src/api/client.ts"] = self._api_client(spec)
        files["frontend/src/types/index.ts"] = self._types(spec)
        files["frontend/src/components/Layout.tsx"] = self._layout(project, spec)
        files["frontend/src/components/StatusBadge.tsx"] = self._status_badge()
        files["frontend/src/components/Icons.tsx"] = self._icons()
        files["frontend/src/components/Skeleton.tsx"] = self._skeleton()
        files["frontend/src/components/Toast.tsx"] = self._toast()
        files["frontend/src/components/ErrorBoundary.tsx"] = self._error_boundary()
        files["frontend/src/components/MiniChart.tsx"] = self._mini_chart()
        files["frontend/src/components/ThemeToggle.tsx"] = self._theme_toggle()
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

    def _index_html(self, project: str, tokens=None) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="Content-Security-Policy"
          content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; connect-src 'self' http://localhost:* ws://localhost:*; img-src 'self' data: blob:;" />
    <title>{project}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="/src/styles/design-tokens.css" />
    <script>
      // Dark mode: check localStorage then system preference
      if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {{
        document.documentElement.classList.add('dark');
      }}
    </script>
  </head>
  <body>
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
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/Toast';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <ToastProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ToastProvider>
    </ErrorBoundary>
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
        display = _pretty_name(project)
        chat_link = ''
        chat_mobile = ''
        if spec and spec.uses_ai:
            chat_link = '\n            <Link to="/chat" className="hover:opacity-80 transition-opacity">AI Chat</Link>'
            chat_mobile = '''
                <Link to="/chat" onClick={() => setOpen(false)}
                  className="block px-3 py-2 rounded-md text-sm hover:bg-white/10">AI Chat</Link>'''
        return f"""import {{ ReactNode, useState }} from 'react';
import {{ Link }} from 'react-router-dom';
import ThemeToggle from './ThemeToggle';
import {{ IconMenu, IconX }} from './Icons';

export default function Layout({{ children }}: {{ children: ReactNode }}) {{
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <header style={{{{ background: 'var(--gradient-header)' }}}} className="text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold tracking-tight hover:opacity-90 font-[var(--font-heading)]">
            {display}
          </Link>

          {{/* Desktop nav */}}
          <nav className="hidden md:flex items-center gap-4 text-sm">
            <Link to="/" className="hover:opacity-80 transition-opacity">Dashboard</Link>{chat_link}
            <ThemeToggle />
          </nav>

          {{/* Mobile hamburger */}}
          <button onClick={{() => setOpen(!open)}} className="md:hidden p-1"
                  aria-label="Toggle navigation">
            {{open ? <IconX /> : <IconMenu />}}
          </button>
        </div>

        {{/* Mobile menu */}}
        {{open && (
          <div className="md:hidden border-t border-white/20 px-4 py-3 space-y-1">
            <Link to="/" onClick={{() => setOpen(false)}}
              className="block px-3 py-2 rounded-md text-sm hover:bg-white/10">Dashboard</Link>{chat_mobile}
            <div className="px-3 py-2"><ThemeToggle /></div>
          </div>
        )}}
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8">
        {{children}}
      </main>

      <footer className="bg-[var(--bg-tertiary)] border-t border-[var(--border-color)] text-center text-xs text-[var(--text-muted)] py-3">
        {display} &mdash; Enterprise DevEx Orchestrator
      </footer>
    </div>
  );
}}
"""

    def _status_badge(self) -> str:
        return """const colors: Record<string, string> = {
  active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  escalated: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  scheduled: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  cancelled: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  pending: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  uploaded: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  analyzed: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
  draft: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  archived: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
  resolved: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400',
  open: 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-400',
  closed: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400',
  critical: 'bg-red-200 text-red-900 dark:bg-red-900/40 dark:text-red-300',
  high: 'bg-orange-200 text-orange-900 dark:bg-orange-900/40 dark:text-orange-300',
  medium: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  low: 'bg-lime-100 text-lime-800 dark:bg-lime-900/30 dark:text-lime-400',
  in_progress: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
};

export default function StatusBadge({ status }: { status: string }) {
  const normalized = status?.toLowerCase().replace(/[- ]/g, '_') || '';
  const cls = colors[normalized] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium cursor-default ${cls}`}>
      {status}
    </span>
  );
}
"""

    # ================================================================
    # New UI/UX components
    # ================================================================

    def _icons(self) -> str:
        """SVG icon components — Lucide-style, zero external deps."""
        return """// Inline SVG icons — no external icon library needed.
// Based on Lucide icon design language (24x24 viewBox, 2px stroke).

const I = ({ d, ...p }: { d: string } & React.SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={20} height={20} viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round"
    strokeLinejoin="round" {...p}>{d.split('|').map((seg, i) => <path key={i} d={seg} />)}</svg>
);

export const IconMenu = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M4 6h16|M4 12h16|M4 18h16" {...p} />;
export const IconX = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M18 6L6 18|M6 6l12 12" {...p} />;
export const IconSun = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M12 2v2|M12 20v2|M4.93 4.93l1.41 1.41|M17.66 17.66l1.41 1.41|M2 12h2|M20 12h2|M6.34 17.66l-1.41 1.41|M19.07 4.93l-1.41 1.41" {...p} />;
export const IconMoon = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" {...p} />;
export const IconSearch = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M11 3a8 8 0 100 16 8 8 0 000-16z|M21 21l-4.35-4.35" {...p} />;
export const IconPlus = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M12 5v14|M5 12h14" {...p} />;
export const IconChevronUp = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M18 15l-6-6-6 6" {...p} />;
export const IconChevronDown = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M6 9l6 6 6-6" {...p} />;
export const IconChevronLeft = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M15 18l-6-6 6-6" {...p} />;
export const IconChevronRight = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M9 18l6-6-6-6" {...p} />;
export const IconRefresh = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M1 4v6h6|M23 20v-6h-6|M20.49 9A9 9 0 005.64 5.64L1 10|M23 14l-4.64 4.36A9 9 0 013.51 15" {...p} />;
export const IconTrash = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M3 6h18|M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6|M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2" {...p} />;
export const IconSend = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M22 2L11 13|M22 2l-7 20-4-9-9-4z" {...p} />;
export const IconAlert = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z|M12 9v4|M12 17h.01" {...p} />;
export const IconFilter = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z" {...p} />;
export const IconDownload = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4|M7 10l5 5 5-5|M12 15V3" {...p} />;
export const IconCheck = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M20 6L9 17l-5-5" {...p} />;
export const IconClock = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M12 2a10 10 0 100 20 10 10 0 000-20z|M12 6v6l4 2" {...p} />;
export const IconExternalLink = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6|M15 3h6v6|M10 14L21 3" {...p} />;
export const IconActivity = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M22 12h-4l-3 9L9 3l-3 9H2" {...p} />;
export const IconEye = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" {...p} />;
export const IconBarChart = (p: React.SVGProps<SVGSVGElement>) =>
  <I d="M12 20V10|M18 20V4|M6 20v-4" {...p} />;
"""

    def _skeleton(self) -> str:
        """Loading skeleton component with shimmer animation."""
        return """export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`skeleton rounded ${className}`} aria-hidden="true" />;
}

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="bg-[var(--surface-card)] rounded-xl shadow overflow-hidden">
      <div className="p-4 space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-4">
            {Array.from({ length: cols }).map((_, j) => (
              <div key={j} className="skeleton h-4 flex-1" style={{ animationDelay: `${j * 100}ms` }} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-[var(--surface-card)] rounded-xl shadow p-4 space-y-3">
      <div className="skeleton h-3 w-24" />
      <div className="skeleton h-8 w-16" />
    </div>
  );
}
"""

    def _toast(self) -> str:
        """Toast notification system."""
        return """import { useState, useEffect, createContext, useContext, useCallback, ReactNode } from 'react';

interface Toast { id: number; message: string; type: 'success' | 'error' | 'info'; }

const Ctx = createContext<{ addToast: (msg: string, type?: Toast['type']) => void }>({
  addToast: () => {},
});

export const useToast = () => useContext(Ctx);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  let nextId = 0;

  const addToast = useCallback((message: string, type: Toast['type'] = 'info') => {
    const id = ++nextId;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  }, []);

  return (
    <Ctx.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-4 right-4 z-[100] space-y-2 pointer-events-none">
        {toasts.map(t => (
          <div key={t.id} className={`toast pointer-events-auto px-4 py-3 rounded-lg shadow-lg text-sm font-medium
            ${t.type === 'success' ? 'bg-green-600 text-white' :
              t.type === 'error' ? 'bg-red-600 text-white' :
              'bg-[var(--surface-card)] text-[var(--text-primary)] border border-[var(--border-color)]'}`}>
            {t.message}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
"""

    def _error_boundary(self) -> str:
        """React error boundary component."""
        return """import { Component, ReactNode } from 'react';
import { IconAlert } from './Icons';

interface Props { children: ReactNode; }
interface State { hasError: boolean; error?: Error; }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8">
          <IconAlert className="w-12 h-12 text-[var(--color-danger)] mb-4" />
          <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">Something went wrong</h2>
          <p className="text-[var(--text-secondary)] mb-4 max-w-md">
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <button
            onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
            className="px-4 py-2 rounded-lg text-sm font-medium"
            style={{ background: 'var(--color-primary)', color: 'var(--text-on-primary)' }}
          >
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
"""

    def _mini_chart(self) -> str:
        """SVG mini chart / sparkline / donut components for dashboard."""
        return """interface MiniChartProps {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
}

export default function MiniChart({ data, color = 'var(--color-primary)', height = 32, width = 80 }: MiniChartProps) {
  if (!data.length) return null;
  const max = Math.max(...data, 1);
  const points = data.map((v, i) => {
    const x = (i / Math.max(data.length - 1, 1)) * width;
    const y = height - (v / max) * (height - 4);
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className="inline-block" aria-hidden="true">
      <polyline fill="none" stroke={color} strokeWidth={2} strokeLinecap="round"
                strokeLinejoin="round" points={points} />
    </svg>
  );
}

export function MiniBar({ data, color = 'var(--color-primary)', height = 32, width = 60 }: MiniChartProps) {
  if (!data.length) return null;
  const max = Math.max(...data, 1);
  const barW = Math.max(width / data.length - 1, 2);

  return (
    <svg width={width} height={height} className="inline-block" aria-hidden="true">
      {data.map((v, i) => {
        const barH = (v / max) * (height - 2);
        return (
          <rect key={i} x={i * (barW + 1)} y={height - barH} width={barW} height={barH}
                rx={1} fill={color} opacity={0.8 + (i / data.length) * 0.2} />
        );
      })}
    </svg>
  );
}

const DONUT_COLORS = [
  'var(--chart-1, #22c55e)', 'var(--chart-2, #3b82f6)', 'var(--chart-3, #f59e0b)',
  'var(--chart-4, #ef4444)', 'var(--chart-5, #8b5cf6)', 'var(--chart-6, #06b6d4)',
  'var(--chart-7, #ec4899)', 'var(--chart-8, #6b7280)',
];

interface DonutProps {
  segments: { label: string; value: number }[];
  size?: number;
}

export function DonutChart({ segments, size = 64 }: DonutProps) {
  const total = segments.reduce((s, seg) => s + seg.value, 0);
  if (!total) return null;
  const r = (size - 8) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * r;
  let offset = 0;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="transform -rotate-90">
        {segments.map((seg, i) => {
          const pct = seg.value / total;
          const dash = pct * circumference;
          const gap = circumference - dash;
          const el = (
            <circle key={i} cx={cx} cy={cy} r={r} fill="none" strokeWidth={6}
              stroke={DONUT_COLORS[i % DONUT_COLORS.length]}
              strokeDasharray={`${dash} ${gap}`} strokeDashoffset={-offset}
              strokeLinecap="round" className="transition-all duration-500" />
          );
          offset += dash;
          return el;
        })}
      </svg>
      <span className="absolute text-xs font-bold text-[var(--text-primary)]">{total}</span>
    </div>
  );
}

export function ProgressBar({ value, max = 100, color }: { value: number; max?: number; color?: string }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const barColor = color || (pct > 80 ? 'var(--color-success, #22c55e)' : pct > 40 ? 'var(--color-warning, #f59e0b)' : 'var(--color-danger, #ef4444)');
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-[var(--bg-tertiary)] rounded-full overflow-hidden" style={{ maxWidth: 64 }}>
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: barColor }} />
      </div>
      <span className="text-xs tabular-nums">{Math.round(value)}{max === 100 ? '%' : ''}</span>
    </div>
  );
}
"""

    def _theme_toggle(self) -> str:
        """Dark / light mode toggle component."""
        return """import { useState, useEffect } from 'react';
import { IconSun, IconMoon } from './Icons';

export default function ThemeToggle() {
  const [dark, setDark] = useState(() =>
    typeof window !== 'undefined' && document.documentElement.classList.contains('dark')
  );

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [dark]);

  return (
    <button onClick={() => setDark(!dark)}
      className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}>
      {dark ? <IconSun className="w-4 h-4" /> : <IconMoon className="w-4 h-4" />}
    </button>
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
            all_columns = ["id"]
            seen = {"id"}
            field_type_map: dict[str, str] = {"id": "text"}
            for f in ent.fields:
                if f.name not in seen:
                    all_columns.append(f.name)
                    seen.add(f.name)
                    field_type_map[f.name] = _detect_field_type(f.name, f.type)

            display_columns = _select_display_columns(all_columns, field_type_map)
            headers = {c: c.replace("_", " ").title() for c in all_columns}
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
            lines.append(f"    displayColumns: {display_columns},")
            lines.append(f"    allColumns: {all_columns},")
            lines.append(f"    headers: {headers},")
            lines.append(f"    fieldMeta: {field_type_map},")
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
        display_name = _pretty_name(spec.project_name)
        return (
            "import { useEffect, useState, useMemo } from 'react';\n"
            "import { Link } from 'react-router-dom';\n"
            "import StatusBadge from '../components/StatusBadge';\n"
            "import { DonutChart, ProgressBar } from '../components/MiniChart';\n"
            "import { useToast } from '../components/Toast';\n"
            "import { IconSearch, IconPlus, IconChevronLeft, IconChevronRight, IconTrash,\n"
            "         IconFilter, IconDownload, IconRefresh, IconActivity, IconCheck, IconClock,\n"
            "         IconExternalLink, IconBarChart } from '../components/Icons';\n"
            "import { CardSkeleton, TableSkeleton } from '../components/Skeleton';\n"
            "\n"
            + tab_config + "\n\n"
            f"const DISPLAY_NAME = '{display_name}';\n\n"
            + _DASHBOARD_COMPONENT
        )

    def _dynamic_detail_page(self, spec: IntentSpec) -> str:
        """Generate an entity-driven DetailPage component."""
        tab_config = self._dynamic_tab_config(spec)
        return (
            "import { useEffect, useState } from 'react';\n"
            "import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';\n"
            "import StatusBadge from '../components/StatusBadge';\n"
            "import { ProgressBar } from '../components/MiniChart';\n"
            "import { useToast } from '../components/Toast';\n"
            "import { IconChevronLeft, IconChevronRight, IconTrash, IconCheck, IconClock, IconExternalLink } from '../components/Icons';\n"
            "import { CardSkeleton } from '../components/Skeleton';\n"
            "\n"
            + tab_config + "\n\n"
            + _DETAIL_PAGE_COMPONENT
        )

    def _chat_page(self, spec: IntentSpec) -> str:
        """Generate an AI chat interface page with HTML rendering and design tokens."""
        project = spec.project_name
        return f"""import {{ useState, useRef, useEffect }} from 'react';
import {{ IconSend }} from '../components/Icons';

interface Message {{
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const suggestions = [
  'Show me a summary of all entities',
  'What are the latest updates?',
  'Give me recommendations',
  'How many items need attention?',
];

export default function ChatPage() {{
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {{
    bottomRef.current?.scrollIntoView({{ behavior: 'smooth' }});
  }}, [messages]);

  useEffect(() => {{ inputRef.current?.focus(); }}, []);

  const sendMessage = async (text?: string) => {{
    const msg = (text || input).trim();
    if (!msg || loading) return;

    const userMsg: Message = {{
      role: 'user',
      content: msg,
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
    }} catch {{
      setMessages((prev) => [
        ...prev,
        {{ role: 'assistant', content: 'Error: Could not reach AI service.', timestamp: new Date().toISOString() }},
      ]);
    }} finally {{
      setLoading(false);
      inputRef.current?.focus();
    }}
  }};

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">{project} AI Assistant</h1>
        <span className="text-xs px-2 py-1 rounded-full font-medium"
          style={{{{ background: 'var(--color-primary)', color: 'white', opacity: 0.9 }}}}>
          AI Powered
        </span>
      </div>

      {{/* Chat messages */}}
      <div className="flex-1 overflow-y-auto bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border-color)] p-4 space-y-4">
        {{messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-3">&#x1F916;</div>
            <p className="text-lg text-[var(--text-primary)] font-medium">Welcome to {project} AI</p>
            <p className="text-sm text-[var(--text-muted)] mt-1 mb-6">Ask a question or try a suggestion below.</p>
            <div className="flex flex-wrap justify-center gap-2 max-w-lg mx-auto">
              {{suggestions.map((s, i) => (
                <button key={{i}} onClick={{() => sendMessage(s)}}
                  className="text-xs px-3 py-1.5 rounded-full border border-[var(--border-color)]
                    bg-[var(--surface-card)] text-[var(--text-secondary)]
                    hover:border-[var(--color-primary)] hover:text-[var(--color-primary)]
                    cursor-pointer transition-colors">
                  {{s}}
                </button>
              ))}}
            </div>
          </div>
        )}}
        {{messages.map((msg, i) => (
          <div key={{i}} className={{`flex ${{msg.role === 'user' ? 'justify-end' : 'justify-start'}}`}}>
            <div
              className={{`max-w-[75%] rounded-xl px-4 py-3 ${{
                msg.role === 'user'
                  ? 'text-white'
                  : 'bg-[var(--surface-card)] border border-[var(--border-color)] text-[var(--text-primary)]'
              }}`}}
              style={{{{
                ...(msg.role === 'user' ? {{ background: 'var(--color-primary)' }} : {{}})
              }}}}
            >
              {{msg.role === 'assistant' ? (
                <div className="prose prose-sm dark:prose-invert max-w-none [&_table]:text-sm [&_table]:border-collapse
                  [&_td]:px-2 [&_td]:py-1 [&_th]:px-2 [&_th]:py-1 [&_td]:border [&_th]:border
                  [&_td]:border-[var(--border-color)] [&_th]:border-[var(--border-color)]"
                  dangerouslySetInnerHTML={{{{ __html: msg.content }}}} />
              ) : (
                <p className="whitespace-pre-wrap">{{msg.content}}</p>
              )}}
              <p className={{`text-xs mt-1.5 ${{msg.role === 'user' ? 'opacity-70' : 'text-[var(--text-muted)]'}}`}}>
                {{new Date(msg.timestamp).toLocaleTimeString()}}
              </p>
            </div>
          </div>
        ))}}
        {{loading && (
          <div className="flex justify-start">
            <div className="bg-[var(--surface-card)] border border-[var(--border-color)] rounded-xl px-4 py-3">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[var(--text-muted)] animate-bounce" style={{{{animationDelay:'0ms'}}}}/>
                <span className="w-2 h-2 rounded-full bg-[var(--text-muted)] animate-bounce" style={{{{animationDelay:'150ms'}}}}/>
                <span className="w-2 h-2 rounded-full bg-[var(--text-muted)] animate-bounce" style={{{{animationDelay:'300ms'}}}}/>
              </div>
            </div>
          </div>
        )}}
        <div ref={{bottomRef}} />
      </div>

      {{/* Input area */}}
      <div className="mt-4 flex gap-2">
        <input
          ref={{inputRef}}
          type="text"
          value={{input}}
          onChange={{(e) => setInput(e.target.value)}}
          onKeyDown={{(e) => e.key === 'Enter' && sendMessage()}}
          placeholder="Type your message..."
          className="flex-1 border border-[var(--border-color)] rounded-xl px-4 py-2.5
            bg-[var(--surface-card)] text-[var(--text-primary)]
            focus:ring-2 focus:ring-[var(--border-focus)] focus:outline-none
            disabled:opacity-50"
          disabled={{loading}}
        />
        <button
          onClick={{() => sendMessage()}}
          disabled={{loading || !input.trim()}}
          className="text-white px-5 py-2.5 rounded-xl hover:opacity-90
            disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-opacity"
          style={{{{ background: 'var(--color-primary)' }}}}
        >
          <IconSend width={{20}} height={{20}} />
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
const PAGE_SIZE = 12;

// -- Type-aware cell renderer --
function RenderCell({ col, value, fieldType }: { col: string; value: any; fieldType: string }) {
  if (value == null || value === '') return <span className="text-[var(--text-muted)]">—</span>;
  switch (fieldType) {
    case 'badge':
      return <StatusBadge status={String(value)} />;
    case 'date':
      try { return <span className="tabular-nums whitespace-nowrap">{new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</span>; }
      catch { return <span>{String(value)}</span>; }
    case 'bool':
      return value === true || value === 'true'
        ? <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400"><IconCheck width={14} height={14} /> Yes</span>
        : <span className="text-[var(--text-muted)]">No</span>;
    case 'pct':
      return <ProgressBar value={Number(value)} />;
    case 'currency':
      return <span className="tabular-nums">${Number(value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>;
    case 'url':
      return <a href={String(value)} target="_blank" rel="noopener noreferrer"
        className="inline-flex items-center gap-1 hover:underline" style={{ color: 'var(--color-primary)' }}>
        <IconExternalLink width={12} height={12} /> Link</a>;
    case 'email':
      return <a href={`mailto:${value}`} className="hover:underline" style={{ color: 'var(--color-primary)' }}>{String(value)}</a>;
    case 'number':
      return <span className="tabular-nums">{Number(value).toLocaleString()}</span>;
    case 'id_ref':
      return <span className="font-mono text-xs text-[var(--text-secondary)]">{String(value).slice(0, 8)}</span>;
    default:
      return <span className="truncate block max-w-[220px]" title={String(value)}>{String(value)}</span>;
  }
}

// -- Status color helper for donut --
function getStatusSegments(items: any[]): { label: string; value: number }[] {
  const counts: Record<string, number> = {};
  items.forEach(item => {
    const s = String(item.status || item.priority || item.severity || 'other').toLowerCase();
    counts[s] = (counts[s] || 0) + 1;
  });
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([label, value]) => ({ label, value }));
}

// -- CSV export helper --
function exportCSV(data: any[], columns: string[], entityName: string) {
  const header = columns.join(',');
  const rows = data.map(item => columns.map(c => {
    const v = String(item[c] ?? '').replace(/"/g, '""');
    return `"${v}"`;
  }).join(','));
  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `${entityName}.csv`; a.click();
  URL.revokeObjectURL(url);
}

export default function Dashboard() {
  const [allData, setAllData] = useState<Record<string, any[]>>({});
  const [activeTab, setActiveTab] = useState(tabKeys[0]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(0);
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const { addToast } = useToast();

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

  // Unique statuses for filter
  const statuses = useMemo(() => {
    const s = new Set<string>();
    currentData.forEach(item => { if (item.status) s.add(item.status); });
    return Array.from(s).sort();
  }, [currentData]);

  // Status filter
  const statusFiltered = statusFilter !== 'all'
    ? currentData.filter(item => item.status === statusFilter)
    : currentData;

  // Search filter
  const filtered = search
    ? statusFiltered.filter((item: any) =>
        Object.values(item).some(v =>
          String(v).toLowerCase().includes(search.toLowerCase())
        )
      )
    : statusFiltered;

  // Sort
  const sorted = sortCol
    ? [...filtered].sort((a, b) => {
        const va = a[sortCol]; const vb = b[sortCol];
        if (typeof va === 'number' && typeof vb === 'number') return sortAsc ? va - vb : vb - va;
        return sortAsc ? String(va ?? '').localeCompare(String(vb ?? '')) : String(vb ?? '').localeCompare(String(va ?? ''));
      })
    : filtered;

  // Paginate
  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const paginated = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const toggleSort = (col: string) => {
    if (sortCol === col) { setSortAsc(!sortAsc); }
    else { setSortCol(col); setSortAsc(true); }
  };

  // Summary metrics
  const totalItems = tabKeys.reduce((sum, k) => sum + (allData[k] || []).length, 0);
  const activeItems = tabKeys.reduce((sum, k) => sum + (allData[k] || []).filter(i => ['active', 'open', 'in_progress'].includes(String(i.status || '').toLowerCase())).length, 0);
  const criticalItems = tabKeys.reduce((sum, k) => sum + (allData[k] || []).filter(i => ['critical', 'escalated', 'high'].includes(String(i.status || i.severity || i.priority || '').toLowerCase())).length, 0);

  const handleCreate = async () => {
    try {
      await fetch(`${API_BASE}/${activeTab}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      setShowCreate(false);
      setFormData({});
      addToast(`${config.entityName} created`, 'success');
      fetchAll();
    } catch { addToast('Failed to create', 'error'); }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`${API_BASE}/${activeTab}/${id}`, { method: 'DELETE' });
      setDeleteTarget(null);
      addToast(`${config.entityName} deleted`, 'success');
      fetchAll();
    } catch { addToast('Failed to delete', 'error'); }
  };

  const handleAction = async (action: string, id: string) => {
    try {
      await fetch(`${API_BASE}/${activeTab}/${id}/${action}`, { method: 'POST' });
      addToast(`Action "${action}" executed`, 'success');
      fetchAll();
    } catch { addToast(`Action "${action}" failed`, 'error'); }
  };

  if (loading) return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[1,2,3,4].map(k => <CardSkeleton key={k} />)}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7 gap-3">
        {tabKeys.slice(0, 7).map(k => <CardSkeleton key={k} />)}
      </div>
      <TableSkeleton rows={6} cols={5} />
    </div>
  );

  const displayCols = config.displayColumns || config.allColumns?.slice(0, 6) || [];
  const createFields = (config.allColumns || []).filter((c: string) => c !== 'id' && c !== 'status');

  return (
    <div className="space-y-6">
      {/* ── Overview Summary Bar ── */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">{DISPLAY_NAME}</h1>
          <p className="text-sm text-[var(--text-muted)] mt-0.5">{tabKeys.length} entities &middot; {totalItems} total records</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchAll}
            className="p-2 rounded-lg border border-[var(--border-color)] hover:bg-[var(--bg-tertiary)] cursor-pointer transition-colors"
            title="Refresh data">
            <IconRefresh width={16} height={16} className="text-[var(--text-secondary)]" />
          </button>
        </div>
      </div>

      {/* ── Summary Metric Cards ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4">
          <div className="flex items-center gap-2 text-[var(--text-muted)] mb-1">
            <IconBarChart width={14} height={14} /> <span className="text-xs font-medium uppercase">Total Records</span>
          </div>
          <p className="text-3xl font-bold text-[var(--text-primary)]">{totalItems}</p>
        </div>
        <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4">
          <div className="flex items-center gap-2 text-[var(--text-muted)] mb-1">
            <IconActivity width={14} height={14} /> <span className="text-xs font-medium uppercase">Active</span>
          </div>
          <p className="text-3xl font-bold text-green-600 dark:text-green-400">{activeItems}</p>
          <p className="text-xs text-[var(--text-muted)]">{totalItems ? Math.round((activeItems / totalItems) * 100) : 0}% of total</p>
        </div>
        <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4">
          <div className="flex items-center gap-2 text-[var(--text-muted)] mb-1">
            <IconClock width={14} height={14} /> <span className="text-xs font-medium uppercase">Entities</span>
          </div>
          <p className="text-3xl font-bold text-[var(--text-primary)]">{tabKeys.length}</p>
        </div>
        <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4">
          <div className="flex items-center gap-2 text-[var(--text-muted)] mb-1">
            <span className="text-red-500"><IconActivity width={14} height={14} /></span>
            <span className="text-xs font-medium uppercase">Needs Attention</span>
          </div>
          <p className="text-3xl font-bold text-red-600 dark:text-red-400">{criticalItems}</p>
          <p className="text-xs text-[var(--text-muted)]">critical / escalated / high</p>
        </div>
      </div>

      {/* ── Entity KPI Cards with Donut Charts ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7 gap-3">
        {tabKeys.map(key => {
          const items = allData[key] || [];
          const segments = getStatusSegments(items);
          const isActive = activeTab === key;
          return (
            <div
              key={key}
              onClick={() => { setActiveTab(key); setPage(0); setSortCol(null); setStatusFilter('all'); setSearch(''); }}
              className={`bg-[var(--surface-card)] rounded-xl p-3 cursor-pointer border-2 transition-all
                hover:shadow-md ${isActive ? 'border-[var(--color-primary)] shadow-md' : 'border-transparent hover:border-[var(--border-color)]'}`}
            >
              <p className="text-xs font-medium text-[var(--text-secondary)] truncate">{tabConfig[key].label}</p>
              <div className="flex items-center justify-between mt-2 gap-2">
                <div>
                  <p className="text-xl font-bold text-[var(--text-primary)]">{items.length}</p>
                  {segments.length > 0 && (
                    <div className="flex flex-wrap gap-x-2 mt-1">
                      {segments.slice(0, 2).map(s => (
                        <span key={s.label} className="text-[10px] text-[var(--text-muted)] whitespace-nowrap">
                          {s.value} {s.label}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {segments.length > 0 && <DonutChart segments={segments} size={44} />}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Table Section Header ── */}
      <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] shadow-sm overflow-hidden">

        {/* Table toolbar */}
        <div className="px-4 py-3 border-b border-[var(--border-color)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">
              {config.label}
              <span className="text-sm font-normal text-[var(--text-muted)] ml-2">({filtered.length})</span>
            </h2>
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto flex-wrap">
            {/* Status filter pills */}
            {config.hasStatus && statuses.length > 0 && (
              <div className="flex items-center gap-1 overflow-x-auto">
                <button onClick={() => { setStatusFilter('all'); setPage(0); }}
                  className={`px-2.5 py-1 text-xs rounded-full border transition-colors cursor-pointer whitespace-nowrap ${
                    statusFilter === 'all'
                      ? 'border-[var(--color-primary)] text-[var(--color-primary)] bg-[var(--color-primary)]/10'
                      : 'border-[var(--border-color)] text-[var(--text-muted)] hover:border-[var(--text-secondary)]'
                  }`}>All</button>
                {statuses.slice(0, 5).map(s => (
                  <button key={s} onClick={() => { setStatusFilter(s); setPage(0); }}
                    className={`px-2.5 py-1 text-xs rounded-full border transition-colors cursor-pointer whitespace-nowrap capitalize ${
                      statusFilter === s
                        ? 'border-[var(--color-primary)] text-[var(--color-primary)] bg-[var(--color-primary)]/10'
                        : 'border-[var(--border-color)] text-[var(--text-muted)] hover:border-[var(--text-secondary)]'
                    }`}>{s.replace(/_/g, ' ')}</button>
                ))}
              </div>
            )}
            {/* Search */}
            <div className="relative">
              <input
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(0); }}
                placeholder="Search..."
                className="border border-[var(--border-color)] rounded-lg px-3 py-1.5 pl-8 text-sm w-48
                  bg-[var(--bg-primary)] text-[var(--text-primary)] focus:ring-2 focus:ring-[var(--border-focus)] focus:outline-none"
              />
              <span className="absolute left-2.5 top-2 text-[var(--text-muted)]"><IconSearch width={14} height={14} /></span>
            </div>
            {/* Export */}
            <button onClick={() => exportCSV(currentData, config.allColumns || [], config.entityName)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border border-[var(--border-color)]
                text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] cursor-pointer transition-colors"
              title="Export CSV">
              <IconDownload width={13} height={13} /> Export
            </button>
            {/* Create */}
            <button
              onClick={() => setShowCreate(true)}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium text-white cursor-pointer
                hover:opacity-90 transition-opacity whitespace-nowrap"
              style={{ background: 'var(--color-primary)' }}
            >
              <IconPlus width={14} height={14} /> New
            </button>
          </div>
        </div>

        {/* Data table — smart columns */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-[var(--border-color)]">
            <thead className="bg-[var(--bg-tertiary)]">
              <tr>
                {displayCols.map((col: string) => (
                  <th key={col} onClick={() => toggleSort(col)}
                    className="px-4 py-2.5 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider
                      cursor-pointer hover:text-[var(--text-primary)] select-none whitespace-nowrap">
                    <span className="inline-flex items-center gap-1">
                      {(config.headers?.[col] || col.replace(/_/g, ' ')).replace(/\b\w/g, (c: string) => c.toUpperCase())}
                      {sortCol === col && (
                        <span className="text-[var(--color-primary)]">{sortAsc ? '▲' : '▼'}</span>
                      )}
                    </span>
                  </th>
                ))}
                <th className="px-4 py-2.5 text-right text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-color)]">
              {paginated.map((item: any) => (
                <tr key={item.id} className="hover:bg-[var(--bg-tertiary)] transition-colors group">
                  {displayCols.map((col: string) => (
                    <td key={col} className="px-4 py-2.5 text-sm text-[var(--text-primary)]">
                      {col === 'id' ? (
                        <Link to={`/detail/${item.id}?type=${activeTab}`}
                          className="font-mono text-xs hover:underline" style={{ color: 'var(--color-primary)' }}>
                          {item.id?.slice(0, 8)}...
                        </Link>
                      ) : (
                        <RenderCell col={col} value={item[col]} fieldType={config.fieldMeta?.[col] || 'text'} />
                      )}
                    </td>
                  ))}
                  <td className="px-4 py-2.5 text-sm text-right">
                    <div className="flex gap-1 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                      {config.actions.slice(0, 3).map((action: string) => (
                        <button key={action} onClick={() => handleAction(action, item.id)}
                          className="px-2 py-1 text-xs rounded-md bg-[var(--bg-tertiary)] hover:bg-[var(--border-color)]
                            text-[var(--text-secondary)] capitalize cursor-pointer transition-colors whitespace-nowrap">
                          {action.replace(/_/g, ' ')}
                        </button>
                      ))}
                      <button onClick={() => setDeleteTarget(item.id)}
                        className="p-1 text-xs rounded-md text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20
                          cursor-pointer transition-colors" title="Delete">
                        <IconTrash width={13} height={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {paginated.length === 0 && (
                <tr>
                  <td colSpan={displayCols.length + 1} className="px-4 py-12 text-center">
                    <IconSearch width={32} height={32} className="mx-auto text-[var(--text-muted)] mb-3 opacity-40" />
                    <p className="text-[var(--text-muted)] font-medium">No {config.label.toLowerCase()} found</p>
                    <p className="text-xs text-[var(--text-muted)] mt-1">Try adjusting your search or filters</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--border-color)] bg-[var(--bg-tertiary)]">
            <p className="text-xs text-[var(--text-muted)]">
              {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, sorted.length)} of {sorted.length}
            </p>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(0)} disabled={page === 0}
                className="px-2 py-1 text-xs rounded border border-[var(--border-color)] disabled:opacity-30
                  hover:bg-[var(--surface-card)] cursor-pointer disabled:cursor-not-allowed transition-colors">
                First
              </button>
              <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
                className="p-1 rounded border border-[var(--border-color)] disabled:opacity-30
                  hover:bg-[var(--surface-card)] cursor-pointer disabled:cursor-not-allowed transition-colors">
                <IconChevronLeft width={14} height={14} />
              </button>
              <span className="px-3 py-1 text-xs font-medium text-[var(--text-secondary)]">
                {page + 1} / {totalPages}
              </span>
              <button onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page >= totalPages - 1}
                className="p-1 rounded border border-[var(--border-color)] disabled:opacity-30
                  hover:bg-[var(--surface-card)] cursor-pointer disabled:cursor-not-allowed transition-colors">
                <IconChevronRight width={14} height={14} />
              </button>
              <button onClick={() => setPage(totalPages - 1)} disabled={page >= totalPages - 1}
                className="px-2 py-1 text-xs rounded border border-[var(--border-color)] disabled:opacity-30
                  hover:bg-[var(--surface-card)] cursor-pointer disabled:cursor-not-allowed transition-colors">
                Last
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Create Modal ── */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
             onClick={() => setShowCreate(false)}>
          <div className="bg-[var(--surface-modal)] rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] overflow-hidden"
               onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-[var(--border-color)] flex items-center justify-between">
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Create {config.entityName}</h2>
              <button onClick={() => { setShowCreate(false); setFormData({}); }}
                className="p-1 rounded-lg hover:bg-[var(--bg-tertiary)] cursor-pointer text-[var(--text-muted)]">✕</button>
            </div>
            <div className="px-6 py-4 overflow-y-auto max-h-[60vh] space-y-3">
              {createFields.map((field: string) => {
                const ft = config.fieldMeta?.[field] || 'text';
                const inputType = ft === 'date' ? 'date' : ft === 'number' || ft === 'pct' || ft === 'currency' ? 'number' : ft === 'email' ? 'email' : ft === 'url' ? 'url' : 'text';
                const isTextarea = field === 'description' || field.endsWith('_notes') || field.endsWith('_text');
                return (
                  <div key={field}>
                    <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1 capitalize">
                      {field.replace(/_/g, ' ')}
                    </label>
                    {ft === 'bool' ? (
                      <select value={formData[field] || ''} onChange={e => setFormData(prev => ({ ...prev, [field]: e.target.value }))}
                        className="w-full border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm
                          bg-[var(--bg-primary)] text-[var(--text-primary)]
                          focus:ring-2 focus:ring-[var(--border-focus)] focus:outline-none">
                        <option value="">Select...</option>
                        <option value="true">Yes</option>
                        <option value="false">No</option>
                      </select>
                    ) : isTextarea ? (
                      <textarea
                        value={formData[field] || ''}
                        onChange={e => setFormData(prev => ({ ...prev, [field]: e.target.value }))}
                        rows={3}
                        className="w-full border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm
                          bg-[var(--bg-primary)] text-[var(--text-primary)]
                          focus:ring-2 focus:ring-[var(--border-focus)] focus:outline-none resize-none"
                        placeholder={`Enter ${field.replace(/_/g, ' ')}`}
                      />
                    ) : (
                      <input
                        type={inputType}
                        value={formData[field] || ''}
                        onChange={e => setFormData(prev => ({ ...prev, [field]: e.target.value }))}
                        className="w-full border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm
                          bg-[var(--bg-primary)] text-[var(--text-primary)]
                          focus:ring-2 focus:ring-[var(--border-focus)] focus:outline-none"
                        placeholder={`Enter ${field.replace(/_/g, ' ')}`}
                        step={ft === 'currency' || ft === 'pct' ? '0.01' : undefined}
                      />
                    )}
                  </div>
                );
              })}
            </div>
            <div className="px-6 py-4 border-t border-[var(--border-color)] flex justify-end gap-3 bg-[var(--bg-tertiary)]">
              <button onClick={() => { setShowCreate(false); setFormData({}); }}
                className="px-4 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer rounded-lg
                  border border-[var(--border-color)] hover:bg-[var(--surface-card)] transition-colors">
                Cancel
              </button>
              <button onClick={handleCreate}
                className="px-5 py-2 rounded-lg text-sm font-medium text-white cursor-pointer hover:opacity-90 transition-opacity"
                style={{ background: 'var(--color-primary)' }}>
                Create {config.entityName}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Delete Confirmation Modal ── */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
             onClick={() => setDeleteTarget(null)}>
          <div className="bg-[var(--surface-modal)] rounded-2xl shadow-2xl p-6 w-full max-w-sm"
               onClick={e => e.stopPropagation()}>
            <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
              <IconTrash width={20} height={20} className="text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-lg font-bold text-center text-[var(--text-primary)] mb-1">Delete {config.entityName}</h2>
            <p className="text-sm text-center text-[var(--text-secondary)] mb-6">
              This action cannot be undone. This will permanently delete the record.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setDeleteTarget(null)}
                className="flex-1 px-4 py-2 text-sm font-medium rounded-lg cursor-pointer
                  border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors">
                Cancel
              </button>
              <button onClick={() => handleDelete(deleteTarget)}
                className="flex-1 px-4 py-2 rounded-lg text-sm font-medium bg-red-600 text-white hover:bg-red-700 cursor-pointer transition-colors">
                Delete
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

// -- Field section grouping --
function groupFields(columns: string[], fieldMeta: Record<string, string>): { title: string; fields: string[] }[] {
  const groups: { title: string; fields: string[] }[] = [];
  const core: string[] = [];
  const location: string[] = [];
  const ai: string[] = [];
  const metrics: string[] = [];
  const refs: string[] = [];
  const dates: string[] = [];
  const rest: string[] = [];

  for (const col of columns) {
    if (col === 'id' || col === 'status') continue;
    const ft = fieldMeta[col] || 'text';
    if (col === 'latitude' || col === 'longitude' || col.includes('location') || col.includes('zone') || col.includes('address'))
      location.push(col);
    else if (col.startsWith('ai_') || col.includes('_ai_') || col.includes('rag_') || col.includes('content_safety') || col.includes('model_'))
      ai.push(col);
    else if (ft === 'pct' || ft === 'currency' || ft === 'number')
      metrics.push(col);
    else if (ft === 'id_ref')
      refs.push(col);
    else if (ft === 'date')
      dates.push(col);
    else if (col === 'name' || col === 'title' || col === 'username' || col === 'display_name' ||
             col === 'description' || col === 'email' || col === 'body' || col === 'type' ||
             col === 'category' || col === 'role' || col === 'department' || col === 'channel' ||
             col === 'severity' || col === 'priority' || col === 'phone')
      core.push(col);
    else
      rest.push(col);
  }

  if (core.length) groups.push({ title: 'General', fields: core });
  if (metrics.length) groups.push({ title: 'Metrics & Costs', fields: metrics });
  if (location.length) groups.push({ title: 'Location', fields: location });
  if (ai.length) groups.push({ title: 'AI & Intelligence', fields: ai });
  if (refs.length) groups.push({ title: 'References', fields: refs });
  if (dates.length) groups.push({ title: 'Dates & Timestamps', fields: dates });
  if (rest.length) groups.push({ title: 'Additional Details', fields: rest });
  return groups;
}

// -- Type-aware detail value renderer --
function DetailValue({ col, value, fieldMeta }: { col: string; value: any; fieldMeta: Record<string, string> }) {
  if (value == null || value === '') return <span className="text-[var(--text-muted)]">—</span>;
  const ft = fieldMeta[col] || 'text';
  switch (ft) {
    case 'badge':
      return <StatusBadge status={String(value)} />;
    case 'date':
      try { return <span className="inline-flex items-center gap-1.5 text-[var(--text-primary)]"><IconClock width={13} height={13} className="text-[var(--text-muted)]" />{new Date(value).toLocaleString()}</span>; }
      catch { return <span>{String(value)}</span>; }
    case 'bool':
      return value === true || value === 'true'
        ? <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400 font-medium"><IconCheck width={14} height={14} /> Yes</span>
        : <span className="text-[var(--text-muted)]">No</span>;
    case 'pct':
      return <ProgressBar value={Number(value)} />;
    case 'currency':
      return <span className="font-semibold tabular-nums">${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>;
    case 'url':
      return <a href={String(value)} target="_blank" rel="noopener noreferrer"
        className="inline-flex items-center gap-1 hover:underline break-all" style={{ color: 'var(--color-primary)' }}>
        <IconExternalLink width={12} height={12} /> {String(value).replace(/https?:\/\//, '').slice(0, 40)}</a>;
    case 'email':
      return <a href={`mailto:${value}`} className="hover:underline" style={{ color: 'var(--color-primary)' }}>{String(value)}</a>;
    case 'number':
      return <span className="font-medium tabular-nums">{Number(value).toLocaleString()}</span>;
    case 'id_ref':
      return <span className="font-mono text-xs px-2 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-secondary)]">{String(value)}</span>;
    default:
      return <span className="text-[var(--text-primary)] break-words">{String(value)}</span>;
  }
}

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [item, setItem] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showDelete, setShowDelete] = useState(false);
  const { addToast } = useToast();

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
    try {
      await fetch(`${API_BASE}/${entityType}/${id}/${action}`, { method: 'POST' });
      const updated = await fetch(`${API_BASE}/${entityType}/${id}`).then(r => r.json());
      setItem(updated);
      addToast(`Action "${action}" executed`, 'success');
    } catch { addToast(`Action "${action}" failed`, 'error'); }
  };

  const handleDelete = async () => {
    try {
      await fetch(`${API_BASE}/${entityType}/${id}`, { method: 'DELETE' });
      addToast(`${config?.entityName || 'Item'} deleted`, 'success');
      setTimeout(() => navigate('/'), 500);
    } catch { addToast('Delete failed', 'error'); }
  };

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-4 w-32" />
      <CardSkeleton />
      <CardSkeleton />
    </div>
  );
  if (!item) return (
    <div className="text-center py-16">
      <div className="w-16 h-16 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center mx-auto mb-4">
        <IconChevronLeft width={24} height={24} className="text-[var(--text-muted)]" />
      </div>
      <p className="text-[var(--text-primary)] font-medium mb-2">Item not found</p>
      <p className="text-[var(--text-muted)] text-sm mb-4">The requested record does not exist or was deleted.</p>
      <button onClick={() => navigate('/')}
        className="px-4 py-2 rounded-lg text-sm font-medium text-white hover:opacity-90"
        style={{ background: 'var(--color-primary)' }}>
        Back to Dashboard
      </button>
    </div>
  );

  const fieldGroups = groupFields(config?.allColumns || [], config?.fieldMeta || {});

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
        <button onClick={() => navigate('/')} className="hover:text-[var(--text-primary)] cursor-pointer transition-colors">
          Dashboard
        </button>
        <IconChevronRight width={12} height={12} />
        <span className="text-[var(--text-secondary)]">{config?.label}</span>
        <IconChevronRight width={12} height={12} />
        <span className="text-[var(--text-primary)] font-medium truncate max-w-[200px]">
          {item.name || item.title || item.username || item.id?.slice(0, 12)}
        </span>
      </div>

      {/* Header card */}
      <div className="bg-[var(--surface-card)] rounded-2xl border border-[var(--border-color)] shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-[var(--border-color)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              {item.name || item.title || item.username || `${config?.entityName || 'Item'} Detail`}
            </h1>
            <p className="text-xs font-mono text-[var(--text-muted)] mt-0.5">ID: {item.id}</p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            {item.status && <StatusBadge status={item.status} />}
            {item.priority && item.priority !== item.status && <StatusBadge status={item.priority} />}
            {item.severity && item.severity !== item.status && <StatusBadge status={item.severity} />}
            <button onClick={() => setShowDelete(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg text-red-600 border border-red-200
                hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-900/20 cursor-pointer transition-colors">
              <IconTrash width={12} height={12} /> Delete
            </button>
          </div>
        </div>

        {/* Actions bar */}
        {config?.actions?.length > 0 && (
          <div className="px-6 py-3 bg-[var(--bg-tertiary)] border-b border-[var(--border-color)] flex flex-wrap gap-2">
            {config.actions.map((action: string) => (
              <button key={action} onClick={() => handleAction(action)}
                className="px-3 py-1.5 text-xs font-medium rounded-lg text-white hover:opacity-90 capitalize cursor-pointer transition-opacity"
                style={{ background: 'var(--color-primary)' }}>
                {action.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Grouped field sections */}
      {fieldGroups.map(group => (
        <div key={group.title} className="bg-[var(--surface-card)] rounded-2xl border border-[var(--border-color)] shadow-sm overflow-hidden">
          <div className="px-6 py-3 border-b border-[var(--border-color)] bg-[var(--bg-tertiary)]">
            <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider">{group.title}</h3>
          </div>
          <dl className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 divide-[var(--border-color)]">
            {group.fields.map((col: string, idx: number) => (
              <div key={col} className={`px-6 py-3 ${idx % 2 === 0 ? 'sm:border-r sm:border-[var(--border-color)]' : ''} ${idx >= 2 ? 'border-t border-[var(--border-color)]' : ''}`}>
                <dt className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide mb-1">
                  {col.replace(/_/g, ' ')}
                </dt>
                <dd className="text-sm">
                  <DetailValue col={col} value={item[col]} fieldMeta={config?.fieldMeta || {}} />
                </dd>
              </div>
            ))}
          </dl>
        </div>
      ))}

      {/* Delete Confirmation */}
      {showDelete && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
             onClick={() => setShowDelete(false)}>
          <div className="bg-[var(--surface-modal)] rounded-2xl shadow-2xl p-6 w-full max-w-sm"
               onClick={e => e.stopPropagation()}>
            <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
              <IconTrash width={20} height={20} className="text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-lg font-bold text-center text-[var(--text-primary)] mb-1">Delete {config?.entityName || 'Item'}</h2>
            <p className="text-sm text-center text-[var(--text-secondary)] mb-6">
              This action is permanent and cannot be undone.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setShowDelete(false)}
                className="flex-1 px-4 py-2 text-sm font-medium rounded-lg cursor-pointer
                  border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors">
                Cancel
              </button>
              <button onClick={handleDelete}
                className="flex-1 px-4 py-2 rounded-lg text-sm font-medium bg-red-600 text-white hover:bg-red-700 cursor-pointer transition-colors">
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
"""
