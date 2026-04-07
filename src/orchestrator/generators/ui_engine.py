"""Advanced UI Component Engine -- dynamic, capability-driven UI generation.

Inspired by UI agent marketplace patterns (GitHub Marketplace UI agents),
this engine generates advanced, interactive React components beyond the
base CRUD dashboard. It produces:

    - Interactive data visualization (charts, graphs, heatmaps)
    - Real-time status indicators with WebSocket-ready patterns
    - Drag-and-drop Kanban boards for workflow entities
    - Timeline/activity feed components
    - Advanced form builders with multi-step wizards
    - Command palette (Cmd+K) for power-user navigation
    - Notification center with categorized alerts
    - Data export/import panels
    - Metric comparison cards with trend arrows
    - Responsive data grids with inline editing
    - Keyboard shortcuts system
    - Empty state illustrations
    - Onboarding tour overlay
    - Breadcrumb navigation
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from src.orchestrator.intent_schema import EntitySpec, IntentSpec
from src.orchestrator.generators.design_system import DesignSystem, DesignTokens
from src.orchestrator.generators.component_intelligence import DetectedCapabilities
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UICapabilityProfile:
    """Extended UI capability profile beyond basic DetectedCapabilities."""

    has_kanban: bool = False
    has_timeline: bool = False
    has_charts: bool = False
    has_command_palette: bool = False
    has_multi_step_form: bool = False
    has_notification_center: bool = False
    has_data_export: bool = False
    has_metric_comparison: bool = False
    has_inline_editing: bool = False
    has_keyboard_shortcuts: bool = False
    has_empty_states: bool = False
    has_breadcrumbs: bool = True  # always useful
    has_map_view: bool = False
    has_real_time: bool = False

    # Which entities drive which features
    kanban_entity: str = ""
    timeline_entity: str = ""
    chart_entities: list[str] = field(default_factory=list)
    map_entity: str = ""


# ────────────────────────────────────────────────────────────────────
# Capability detection: analyze entities to decide which advanced
# components to generate
# ────────────────────────────────────────────────────────────────────

_KANBAN_SIGNALS = {
    "fields": {"status", "priority", "assigned_to", "stage", "column", "lane"},
    "entities": {"task", "ticket", "issue", "story", "card", "work_order", "case"},
    "threshold": 2,
}

_TIMELINE_SIGNALS = {
    "fields": {"created_at", "updated_at", "timestamp", "event_date", "occurred_at", "logged_at"},
    "entities": {"event", "activity", "log", "audit", "history", "incident", "alert"},
    "threshold": 2,
}

_CHART_SIGNALS = {
    "fields": {
        "count", "total", "amount", "score", "rate", "percentage",
        "cost", "revenue", "budget", "price", "quantity", "volume",
        "progress", "utilization", "efficiency",
    },
    "threshold": 2,
}

_MAP_SIGNALS = {
    "fields": {"latitude", "longitude", "lat", "lng", "location", "coordinates", "address", "geo_point"},
    "threshold": 2,
}

_REALTIME_SIGNALS = {
    "fields": {"temperature", "sensor_value", "reading", "telemetry", "signal_strength", "heartbeat"},
    "entities": {"sensor", "device", "monitor", "telemetry", "reading", "gateway"},
    "threshold": 2,
}


def detect_ui_capabilities(spec: IntentSpec) -> UICapabilityProfile:
    """Analyze entities to determine what advanced UI components to generate."""
    profile = UICapabilityProfile()

    for entity in spec.entities:
        field_names = {f.name for f in entity.fields}
        ename_lower = entity.name.lower()
        numeric_fields = [f for f in entity.fields if f.type in ("int", "float")]

        # Kanban detection
        kanban_score = len(field_names & _KANBAN_SIGNALS["fields"])
        if ename_lower in _KANBAN_SIGNALS["entities"]:
            kanban_score += 2
        if kanban_score >= _KANBAN_SIGNALS["threshold"]:
            profile.has_kanban = True
            profile.kanban_entity = entity.name

        # Timeline detection
        timeline_score = len(field_names & _TIMELINE_SIGNALS["fields"])
        if ename_lower in _TIMELINE_SIGNALS["entities"]:
            timeline_score += 2
        if timeline_score >= _TIMELINE_SIGNALS["threshold"]:
            profile.has_timeline = True
            profile.timeline_entity = entity.name

        # Chart detection (any entity with numeric fields)
        chart_score = len(field_names & _CHART_SIGNALS["fields"])
        if len(numeric_fields) >= 2:
            chart_score += 1
        if chart_score >= _CHART_SIGNALS["threshold"]:
            profile.has_charts = True
            profile.chart_entities.append(entity.name)

        # Map detection
        map_score = len(field_names & _MAP_SIGNALS["fields"])
        if map_score >= _MAP_SIGNALS["threshold"]:
            profile.has_map_view = True
            profile.map_entity = entity.name

        # Real-time detection
        rt_score = len(field_names & _REALTIME_SIGNALS["fields"])
        if ename_lower in _REALTIME_SIGNALS["entities"]:
            rt_score += 2
        if rt_score >= _REALTIME_SIGNALS["threshold"]:
            profile.has_real_time = True

    # Always enable these for 3+ entities
    if len(spec.entities) >= 3:
        profile.has_command_palette = True
        profile.has_keyboard_shortcuts = True
        profile.has_notification_center = True

    # Multi-step form for entities with 8+ fields
    for entity in spec.entities:
        if len(entity.fields) >= 8:
            profile.has_multi_step_form = True
            break

    # Charts always on if any numeric data
    if any(f.type in ("int", "float") for e in spec.entities for f in e.fields):
        profile.has_charts = True

    # Data export always available
    profile.has_data_export = True
    profile.has_empty_states = True
    profile.has_metric_comparison = len(spec.entities) >= 2

    return profile


# ────────────────────────────────────────────────────────────────────
# Component generators
# ────────────────────────────────────────────────────────────────────

class AdvancedUIEngine:
    """Generates advanced React components based on capability detection."""

    def __init__(self, tokens: DesignTokens | None = None):
        self._tokens = tokens

    def generate(
        self,
        spec: IntentSpec,
        profile: UICapabilityProfile,
    ) -> dict[str, str]:
        """Generate advanced UI component files."""
        files: dict[str, str] = {}

        if profile.has_command_palette:
            files["frontend/src/components/CommandPalette.tsx"] = self._command_palette(spec)

        if profile.has_kanban:
            files["frontend/src/pages/KanbanPage.tsx"] = self._kanban_board(spec, profile)

        if profile.has_timeline:
            files["frontend/src/components/ActivityTimeline.tsx"] = self._activity_timeline()
            files["frontend/src/pages/TimelinePage.tsx"] = self._timeline_page(spec, profile)

        if profile.has_charts:
            files["frontend/src/components/Charts.tsx"] = self._chart_components()
            files["frontend/src/pages/InsightsPage.tsx"] = self._insights_page(spec, profile)

        if profile.has_notification_center:
            files["frontend/src/components/NotificationCenter.tsx"] = self._notification_center()

        if profile.has_keyboard_shortcuts:
            files["frontend/src/hooks/useKeyboardShortcuts.ts"] = self._keyboard_shortcuts()

        if profile.has_empty_states:
            files["frontend/src/components/EmptyState.tsx"] = self._empty_state()

        if profile.has_breadcrumbs:
            files["frontend/src/components/Breadcrumbs.tsx"] = self._breadcrumbs()

        if profile.has_metric_comparison:
            files["frontend/src/components/MetricCard.tsx"] = self._metric_card()

        if profile.has_multi_step_form:
            files["frontend/src/components/MultiStepForm.tsx"] = self._multi_step_form(spec)

        if profile.has_data_export:
            files["frontend/src/components/DataExportPanel.tsx"] = self._data_export_panel(spec)

        # -- Real-time visualization components --
        files["frontend/src/components/GaugeChart.tsx"] = self._gauge_chart()
        files["frontend/src/components/HeatmapGrid.tsx"] = self._heatmap_grid()
        files["frontend/src/components/GeoMap.tsx"] = self._geo_map()
        files["frontend/src/components/LiveFeed.tsx"] = self._live_feed()
        files["frontend/src/components/SparklineGrid.tsx"] = self._sparkline_grid()
        files["frontend/src/components/TreemapChart.tsx"] = self._treemap_chart()
        files["frontend/src/components/RadarChart.tsx"] = self._radar_chart()
        files["frontend/src/hooks/useEventStream.ts"] = self._use_event_stream()

        # -- Real-time monitoring page --
        files["frontend/src/pages/RealtimePage.tsx"] = self._realtime_page(spec)

        # -- Conversational UI builder --
        files["frontend/src/pages/DynamicBuilderPage.tsx"] = self._dynamic_builder_page(spec)

        # -- Advanced analytics page --
        files["frontend/src/pages/AdvancedAnalyticsPage.tsx"] = self._advanced_analytics_page(spec)

        logger.info("AdvancedUIEngine produced %d component files", len(files))
        return files

    # ── Command Palette (Cmd+K) ─────────────────────────────────────

    def _command_palette(self, spec: IntentSpec) -> str:
        # Build route entries from entities
        routes: list[str] = ['    { label: "Dashboard", path: "/", icon: "home" },']
        for ent in spec.entities:
            slug = ent.name.lower().replace(" ", "_")
            plural = slug + "s" if not slug.endswith("s") else slug
            routes.append(
                f'    {{ label: "{ent.name} List", path: "/?tab={plural}", icon: "list" }},'
            )
        routes_str = "\n".join(routes)

        return f"""import {{ useState, useEffect, useRef, useCallback }} from 'react';
import {{ useNavigate }} from 'react-router-dom';
import {{ IconSearch }} from './Icons';

interface Command {{
  label: string;
  path: string;
  icon: string;
}}

const commands: Command[] = [
{routes_str}
    {{ label: "Settings", path: "/settings", icon: "settings" }},
];

export default function CommandPalette() {{
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const filtered = query
    ? commands.filter(c => c.label.toLowerCase().includes(query.toLowerCase()))
    : commands;

  const handleKeyDown = useCallback((e: KeyboardEvent) => {{
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {{
      e.preventDefault();
      setOpen(prev => !prev);
      setQuery('');
      setSelected(0);
    }}
    if (e.key === 'Escape') setOpen(false);
  }}, []);

  useEffect(() => {{
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }}, [handleKeyDown]);

  useEffect(() => {{
    if (open) inputRef.current?.focus();
  }}, [open]);

  const execute = (cmd: Command) => {{
    navigate(cmd.path);
    setOpen(false);
  }};

  const handleInputKey = (e: React.KeyboardEvent) => {{
    if (e.key === 'ArrowDown') {{
      e.preventDefault();
      setSelected(s => Math.min(s + 1, filtered.length - 1));
    }} else if (e.key === 'ArrowUp') {{
      e.preventDefault();
      setSelected(s => Math.max(s - 1, 0));
    }} else if (e.key === 'Enter' && filtered[selected]) {{
      execute(filtered[selected]);
    }}
  }};

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
         onClick={{() => setOpen(false)}}>
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
      <div className="relative w-full max-w-lg bg-[var(--surface-card)] rounded-xl shadow-2xl
                      border border-[var(--border-color)] overflow-hidden"
           onClick={{e => e.stopPropagation()}}>
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border-color)]">
          <IconSearch width={{18}} height={{18}} />
          <input
            ref={{inputRef}}
            type="text"
            value={{query}}
            onChange={{e => {{ setQuery(e.target.value); setSelected(0); }}}}
            onKeyDown={{handleInputKey}}
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent outline-none text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
          />
          <kbd className="text-xs px-2 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)]">ESC</kbd>
        </div>
        <ul className="max-h-64 overflow-y-auto py-1">
          {{filtered.map((cmd, i) => (
            <li
              key={{cmd.path}}
              className={{`px-4 py-2.5 cursor-pointer flex items-center gap-3 text-sm
                ${{i === selected
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'}}`}}
              onClick={{() => execute(cmd)}}
              onMouseEnter={{() => setSelected(i)}}
            >
              <span className="text-xs opacity-60">{{cmd.icon === 'home' ? '🏠' : cmd.icon === 'list' ? '📋' : '⚙️'}}</span>
              {{cmd.label}}
            </li>
          ))}}
          {{filtered.length === 0 && (
            <li className="px-4 py-6 text-center text-sm text-[var(--text-muted)]">
              No commands found
            </li>
          )}}
        </ul>
        <div className="px-4 py-2 border-t border-[var(--border-color)] flex gap-4 text-xs text-[var(--text-muted)]">
          <span>↑↓ Navigate</span>
          <span>↵ Select</span>
          <span>esc Close</span>
        </div>
      </div>
    </div>
  );
}}
"""

    # ── Kanban Board ────────────────────────────────────────────────

    def _kanban_board(self, spec: IntentSpec, profile: UICapabilityProfile) -> str:
        entity_name = profile.kanban_entity or (spec.entities[0].name if spec.entities else "Item")
        slug = entity_name.lower().replace(" ", "_")
        plural = slug + "s" if not slug.endswith("s") else slug

        return f"""import {{ useState, useEffect }} from 'react';
import StatusBadge from '../components/StatusBadge';
import {{ useToast }} from '../components/Toast';
import {{ IconRefresh }} from '../components/Icons';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const COLUMNS = ['pending', 'in_progress', 'completed', 'resolved'];
const COLUMN_LABELS: Record<string, string> = {{
  pending: '📋 Pending',
  in_progress: '🔄 In Progress',
  completed: '✅ Completed',
  resolved: '🏁 Resolved',
}};

const COLUMN_COLORS: Record<string, string> = {{
  pending: 'border-t-amber-400',
  in_progress: 'border-t-blue-500',
  completed: 'border-t-green-500',
  resolved: 'border-t-gray-400',
}};

interface KanbanItem {{
  id: string;
  status: string;
  [key: string]: any;
}}

export default function KanbanPage() {{
  const [items, setItems] = useState<KanbanItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [dragItem, setDragItem] = useState<string | null>(null);
  const {{ addToast }} = useToast();

  const fetchItems = () => {{
    setLoading(true);
    fetch(`${{API_BASE}}/{plural}`)
      .then(r => r.json())
      .then(data => setItems(Array.isArray(data) ? data : []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }};

  useEffect(() => {{ fetchItems(); }}, []);

  const moveItem = async (itemId: string, newStatus: string) => {{
    try {{
      await fetch(`${{API_BASE}}/{plural}/${{itemId}}`, {{
        method: 'PUT',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ status: newStatus }}),
      }});
      setItems(prev =>
        prev.map(item =>
          item.id === itemId ? {{ ...item, status: newStatus }} : item
        )
      );
      addToast(`Moved to ${{newStatus.replace('_', ' ')}}`, 'success');
    }} catch {{
      addToast('Failed to move item', 'error');
    }}
  }};

  const handleDragStart = (e: React.DragEvent, itemId: string) => {{
    setDragItem(itemId);
    e.dataTransfer.effectAllowed = 'move';
  }};

  const handleDrop = (e: React.DragEvent, status: string) => {{
    e.preventDefault();
    if (dragItem) {{
      moveItem(dragItem, status);
      setDragItem(null);
    }}
  }};

  const handleDragOver = (e: React.DragEvent) => {{
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }};

  const getDisplayField = (item: KanbanItem): string => {{
    return item.name || item.title || item.label || item.description?.slice(0, 50) || item.id;
  }};

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-[var(--color-primary)] border-t-transparent" />
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          {entity_name} Board
        </h1>
        <button onClick={{fetchItems}}
          className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg
                     border border-[var(--border-color)] hover:bg-[var(--bg-tertiary)]
                     text-[var(--text-secondary)]">
          <IconRefresh width={{14}} height={{14}} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 min-h-[60vh]">
        {{COLUMNS.map(col => {{
          const colItems = items.filter(i =>
            (i.status || '').toLowerCase().replace(/\\s+/g, '_') === col
          );
          return (
            <div
              key={{col}}
              className={{`bg-[var(--bg-tertiary)] rounded-xl p-3 border-t-4 ${{COLUMN_COLORS[col] || 'border-t-gray-300'}}
                          ${{dragItem ? 'ring-2 ring-[var(--color-primary)]/20' : ''}}`}}
              onDragOver={{handleDragOver}}
              onDrop={{e => handleDrop(e, col)}}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  {{COLUMN_LABELS[col] || col}}
                </h3>
                <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--surface-card)]
                              text-[var(--text-muted)]">
                  {{colItems.length}}
                </span>
              </div>
              <div className="space-y-2 min-h-[100px]">
                {{colItems.map(item => (
                  <div
                    key={{item.id}}
                    draggable
                    onDragStart={{e => handleDragStart(e, item.id)}}
                    className="bg-[var(--surface-card)] rounded-lg p-3 shadow-sm border border-[var(--border-color)]
                               cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow"
                  >
                    <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                      {{getDisplayField(item)}}
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-[var(--text-muted)] font-mono">{{item.id}}</span>
                      {{item.priority && <StatusBadge status={{item.priority}} />}}
                    </div>
                  </div>
                ))}}
                {{colItems.length === 0 && (
                  <div className="text-center py-8 text-xs text-[var(--text-muted)]">
                    Drop items here
                  </div>
                )}}
              </div>
            </div>
          );
        }})}}
      </div>
    </div>
  );
}}
"""

    # ── Activity Timeline ───────────────────────────────────────────

    def _activity_timeline(self) -> str:
        return """import { ReactNode } from 'react';

interface TimelineItem {
  id: string;
  title: string;
  description?: string;
  timestamp: string;
  type?: 'created' | 'updated' | 'deleted' | 'info' | 'warning' | 'error';
  icon?: ReactNode;
}

const typeColors: Record<string, string> = {
  created: 'bg-green-500',
  updated: 'bg-blue-500',
  deleted: 'bg-red-500',
  info: 'bg-gray-400',
  warning: 'bg-amber-500',
  error: 'bg-red-600',
};

export default function ActivityTimeline({ items }: { items: TimelineItem[] }) {
  return (
    <div className="relative pl-6">
      {/* Vertical line */}
      <div className="absolute left-2.5 top-0 bottom-0 w-0.5 bg-[var(--border-color)]" />

      {items.map((item, i) => (
        <div key={item.id} className="relative pb-6 last:pb-0">
          {/* Dot */}
          <div className={`absolute -left-3.5 mt-1.5 w-3 h-3 rounded-full ring-2 ring-[var(--bg-primary)]
                          ${typeColors[item.type || 'info']}`} />

          <div className="ml-4">
            <div className="flex items-baseline gap-2">
              <p className="text-sm font-medium text-[var(--text-primary)]">{item.title}</p>
              <span className="text-xs text-[var(--text-muted)] whitespace-nowrap">
                {new Date(item.timestamp).toLocaleString(undefined, {
                  month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                })}
              </span>
            </div>
            {item.description && (
              <p className="text-xs text-[var(--text-secondary)] mt-0.5">{item.description}</p>
            )}
          </div>
        </div>
      ))}

      {items.length === 0 && (
        <div className="text-center py-8 text-sm text-[var(--text-muted)]">
          No activity yet
        </div>
      )}
    </div>
  );
}
"""

    def _timeline_page(self, spec: IntentSpec, profile: UICapabilityProfile) -> str:
        entity = profile.timeline_entity or (spec.entities[0].name if spec.entities else "Event")
        slug = entity.lower().replace(" ", "_")
        plural = slug + "s" if not slug.endswith("s") else slug

        return f"""import {{ useState, useEffect }} from 'react';
import ActivityTimeline from '../components/ActivityTimeline';
import {{ IconRefresh }} from '../components/Icons';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export default function TimelinePage() {{
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {{
    fetch(`${{API_BASE}}/{plural}`)
      .then(r => r.json())
      .then(data => setItems(Array.isArray(data) ? data : []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }}, []);

  const timelineItems = items
    .sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
    .map(item => ({{
      id: item.id,
      title: item.name || item.title || item.description?.slice(0, 60) || item.id,
      description: item.description || item.notes || item.summary || '',
      timestamp: item.created_at || item.updated_at || new Date().toISOString(),
      type: (item.status === 'completed' ? 'created'
           : item.status === 'critical' ? 'error'
           : item.status === 'in_progress' ? 'updated'
           : 'info') as 'created' | 'updated' | 'error' | 'info',
    }}));

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-[var(--color-primary)] border-t-transparent" />
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-[var(--text-primary)]">{entity} Timeline</h1>
      <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-6">
        <ActivityTimeline items={{timelineItems}} />
      </div>
    </div>
  );
}}
"""

    # ── Chart Components ────────────────────────────────────────────

    def _chart_components(self) -> str:
        return """import { useMemo } from 'react';

interface BarChartProps {
  data: { label: string; value: number; color?: string }[];
  height?: number;
  showValues?: boolean;
}

const CHART_COLORS = [
  'var(--color-primary)', 'var(--color-secondary, #7c3aed)',
  'var(--color-accent, #06b6d4)', 'var(--color-success, #10b981)',
  '#f59e0b', '#ef4444', '#ec4899', '#8b5cf6',
];

export function BarChart({ data, height = 200, showValues = true }: BarChartProps) {
  const maxVal = Math.max(...data.map(d => d.value), 1);

  return (
    <div className="flex items-end gap-2" style={{ height }}>
      {data.map((d, i) => {
        const barH = (d.value / maxVal) * (height - 30);
        const color = d.color || CHART_COLORS[i % CHART_COLORS.length];
        return (
          <div key={d.label} className="flex-1 flex flex-col items-center gap-1">
            {showValues && (
              <span className="text-xs text-[var(--text-muted)] tabular-nums">
                {d.value.toLocaleString()}
              </span>
            )}
            <div
              className="w-full rounded-t-md transition-all duration-500 hover:opacity-80"
              style={{ height: barH, background: color, minHeight: 4 }}
              title={`${d.label}: ${d.value}`}
            />
            <span className="text-[10px] text-[var(--text-muted)] truncate max-w-full text-center">
              {d.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

interface LineChartProps {
  data: { label: string; value: number }[];
  height?: number;
  color?: string;
}

export function LineChart({ data, height = 160, color = 'var(--color-primary)' }: LineChartProps) {
  const maxVal = Math.max(...data.map(d => d.value), 1);
  const minVal = Math.min(...data.map(d => d.value), 0);
  const range = maxVal - minVal || 1;
  const w = 100;
  const h = height - 20;

  const points = useMemo(() => {
    return data.map((d, i) => ({
      x: (i / Math.max(data.length - 1, 1)) * w,
      y: h - ((d.value - minVal) / range) * h,
    }));
  }, [data, h, w, minVal, range]);

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaD = pathD + ` L ${w} ${h} L 0 ${h} Z`;

  return (
    <svg viewBox={`0 0 ${w} ${height}`} className="w-full" style={{ height }}>
      <defs>
        <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaD} fill="url(#lineGrad)" />
      <path d={pathD} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="2" fill={color}>
          <title>{data[i].label}: {data[i].value}</title>
        </circle>
      ))}
    </svg>
  );
}

interface PieChartProps {
  data: { label: string; value: number; color?: string }[];
  size?: number;
}

export function PieChart({ data, size = 160 }: PieChartProps) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  const r = size / 2 - 8;
  const cx = size / 2;
  const cy = size / 2;

  let current = -Math.PI / 2;
  const slices = data.map((d, i) => {
    const angle = (d.value / total) * 2 * Math.PI;
    const x1 = cx + r * Math.cos(current);
    const y1 = cy + r * Math.sin(current);
    current += angle;
    const x2 = cx + r * Math.cos(current);
    const y2 = cy + r * Math.sin(current);
    const large = angle > Math.PI ? 1 : 0;
    const color = d.color || CHART_COLORS[i % CHART_COLORS.length];
    return { d: `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`, color, label: d.label, value: d.value };
  });

  return (
    <div className="flex items-center gap-4">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {slices.map((s, i) => (
          <path key={i} d={s.d} fill={s.color} stroke="var(--bg-primary)" strokeWidth="1.5"
                className="hover:opacity-80 transition-opacity">
            <title>{s.label}: {s.value} ({((s.value / total) * 100).toFixed(0)}%)</title>
          </path>
        ))}
      </svg>
      <div className="flex flex-col gap-1.5">
        {data.map((d, i) => (
          <div key={d.label} className="flex items-center gap-2 text-xs">
            <span className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ background: d.color || CHART_COLORS[i % CHART_COLORS.length] }} />
            <span className="text-[var(--text-secondary)]">{d.label}</span>
            <span className="text-[var(--text-muted)] ml-auto tabular-nums">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
"""

    def _insights_page(self, spec: IntentSpec, profile: UICapabilityProfile) -> str:
        # Build fetch calls for chart entities
        fetch_entities = []
        for ent in spec.entities[:4]:  # max 4 for readability
            snake = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", ent.name)
            snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", snake).lower()
            plural = snake + "s" if not snake.endswith("s") else snake
            fetch_entities.append((ent.name, plural))

        fetch_calls = ",\n      ".join(
            f'fetch(`${{API_BASE}}/{p}`).then(r => r.json()).catch(() => [])'
            for _, p in fetch_entities
        )
        assign_lines = "\n      ".join(
            f'd["{p}"] = Array.isArray(results[{i}]) ? results[{i}] : [];'
            for i, (_, p) in enumerate(fetch_entities)
        )
        entity_keys = [p for _, p in fetch_entities]

        return f"""import {{ useState, useEffect, useMemo }} from 'react';
import {{ BarChart, LineChart, PieChart }} from '../components/Charts';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export default function InsightsPage() {{
  const [data, setData] = useState<Record<string, any[]>>({{}}); 
  const [loading, setLoading] = useState(true);

  useEffect(() => {{
    Promise.all([
      {fetch_calls}
    ]).then(results => {{
      const d: Record<string, any[]> = {{}};
      {assign_lines}
      setData(d);
    }}).finally(() => setLoading(false));
  }}, []);

  // Status distribution across all entities
  const statusDistribution = useMemo(() => {{
    const counts: Record<string, number> = {{}};
    Object.values(data).flat().forEach(item => {{
      const s = String(item.status || 'unknown');
      counts[s] = (counts[s] || 0) + 1;
    }});
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([label, value]) => ({{ label, value }}));
  }}, [data]);

  // Records per entity
  const entityCounts = useMemo(() => {{
    return Object.entries(data).map(([key, items]) => ({{
      label: key.replace(/_/g, ' '),
      value: items.length,
    }}));
  }}, [data]);

  // Timeline: records created per week
  const timelineTrend = useMemo(() => {{
    const weeks: Record<string, number> = {{}};
    Object.values(data).flat().forEach(item => {{
      if (item.created_at) {{
        const d = new Date(item.created_at);
        const week = `${{d.getMonth() + 1}}/${{Math.ceil(d.getDate() / 7)}}`;
        weeks[week] = (weeks[week] || 0) + 1;
      }}
    }});
    return Object.entries(weeks)
      .sort()
      .slice(-8)
      .map(([label, value]) => ({{ label, value }}));
  }}, [data]);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-[var(--color-primary)] border-t-transparent" />
    </div>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[var(--text-primary)]">Insights &amp; Analytics</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {{/* Status Distribution */}}
        <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-6">
          <h2 className="text-lg font-semibold mb-4 text-[var(--text-primary)]">Status Distribution</h2>
          <PieChart data={{statusDistribution}} />
        </div>

        {{/* Records per Entity */}}
        <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-6">
          <h2 className="text-lg font-semibold mb-4 text-[var(--text-primary)]">Records by Entity</h2>
          <BarChart data={{entityCounts}} />
        </div>

        {{/* Creation Trend */}}
        <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4 text-[var(--text-primary)]">Creation Trend</h2>
          <LineChart data={{timelineTrend}} height={{200}} />
        </div>
      </div>
    </div>
  );
}}
"""

    # ── Notification Center ─────────────────────────────────────────

    def _notification_center(self) -> str:
        return """import { useState } from 'react';
import { IconX } from './Icons';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: string;
  read: boolean;
}

const typeIcons: Record<string, string> = {
  info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌',
};
const typeBg: Record<string, string> = {
  info: 'bg-blue-50 dark:bg-blue-900/20',
  success: 'bg-green-50 dark:bg-green-900/20',
  warning: 'bg-amber-50 dark:bg-amber-900/20',
  error: 'bg-red-50 dark:bg-red-900/20',
};

export default function NotificationCenter({
  notifications,
  onDismiss,
  onMarkRead,
}: {
  notifications: Notification[];
  onDismiss: (id: string) => void;
  onMarkRead: (id: string) => void;
}) {
  const [filter, setFilter] = useState<string>('all');

  const filtered = filter === 'all'
    ? notifications
    : filter === 'unread'
      ? notifications.filter(n => !n.read)
      : notifications.filter(n => n.type === filter);

  return (
    <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--border-color)] flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">
          Notifications ({notifications.filter(n => !n.read).length} unread)
        </h3>
        <div className="flex gap-1">
          {['all', 'unread', 'error', 'warning'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs px-2 py-0.5 rounded-full capitalize transition-colors
                ${filter === f
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)]'}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>
      <div className="max-h-80 overflow-y-auto">
        {filtered.map(n => (
          <div
            key={n.id}
            className={`px-4 py-3 border-b border-[var(--border-color)] ${typeBg[n.type]}
                        ${!n.read ? 'font-medium' : 'opacity-75'}`}
            onClick={() => onMarkRead(n.id)}
          >
            <div className="flex items-start gap-2">
              <span className="text-sm mt-0.5">{typeIcons[n.type]}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-[var(--text-primary)]">{n.title}</p>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5 truncate">{n.message}</p>
                <span className="text-[10px] text-[var(--text-muted)]">
                  {new Date(n.timestamp).toLocaleString()}
                </span>
              </div>
              <button
                onClick={e => { e.stopPropagation(); onDismiss(n.id); }}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                <IconX width={14} height={14} />
              </button>
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="py-8 text-center text-sm text-[var(--text-muted)]">
            No notifications
          </div>
        )}
      </div>
    </div>
  );
}
"""

    # ── Keyboard Shortcuts ──────────────────────────────────────────

    def _keyboard_shortcuts(self) -> str:
        return """import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

interface ShortcutMap {
  [key: string]: { handler: () => void; description: string };
}

export function useKeyboardShortcuts() {
  const navigate = useNavigate();

  const shortcuts: ShortcutMap = {
    'g+d': { handler: () => navigate('/'), description: 'Go to Dashboard' },
    'g+i': { handler: () => navigate('/insights'), description: 'Go to Insights' },
    '?': { handler: () => {
      // Show shortcuts modal could be implemented here
      console.log('Keyboard shortcuts:', Object.entries(shortcuts).map(
        ([k, v]) => `${k}: ${v.description}`
      ).join('\\n'));
    }, description: 'Show shortcuts' },
  };

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Ignore if typing in input
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) return;

    const key = e.key.toLowerCase();

    // Single key shortcuts
    if (shortcuts[key]) {
      e.preventDefault();
      shortcuts[key].handler();
    }
  }, [navigate]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return shortcuts;
}
"""

    # ── Empty State ─────────────────────────────────────────────────

    def _empty_state(self) -> str:
        return """interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: string;
  action?: { label: string; onClick: () => void };
}

export default function EmptyState({ title, description, icon = '📭', action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="text-5xl mb-4" aria-hidden="true">{icon}</div>
      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-[var(--text-muted)] max-w-sm text-center">{description}</p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 px-4 py-2 rounded-lg text-sm font-medium
                     bg-[var(--color-primary)] text-white hover:opacity-90 transition-opacity"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
"""

    # ── Breadcrumbs ─────────────────────────────────────────────────

    def _breadcrumbs(self) -> str:
        return """import { Link, useLocation } from 'react-router-dom';

export default function Breadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split('/').filter(Boolean);

  if (segments.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className="mb-4">
      <ol className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
        <li>
          <Link to="/" className="hover:text-[var(--color-primary)] transition-colors">
            Home
          </Link>
        </li>
        {segments.map((seg, i) => {
          const path = '/' + segments.slice(0, i + 1).join('/');
          const isLast = i === segments.length - 1;
          const label = decodeURIComponent(seg).replace(/[-_]/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase());

          return (
            <li key={path} className="flex items-center gap-1.5">
              <span className="text-[var(--border-color)]">/</span>
              {isLast ? (
                <span className="text-[var(--text-primary)] font-medium">{label}</span>
              ) : (
                <Link to={path} className="hover:text-[var(--color-primary)] transition-colors">
                  {label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
"""

    # ── Metric Comparison Card ──────────────────────────────────────

    def _metric_card(self) -> str:
        return """interface MetricCardProps {
  title: string;
  value: number | string;
  previousValue?: number;
  format?: 'number' | 'currency' | 'percent';
  icon?: string;
}

export default function MetricCard({ title, value, previousValue, format = 'number', icon }: MetricCardProps) {
  const numValue = typeof value === 'number' ? value : parseFloat(value) || 0;
  const trend = previousValue != null ? numValue - previousValue : null;
  const trendPct = previousValue ? ((numValue - previousValue) / previousValue) * 100 : null;

  const formatValue = (v: number) => {
    switch (format) {
      case 'currency': return `$${v.toLocaleString(undefined, { minimumFractionDigits: 0 })}`;
      case 'percent': return `${v.toFixed(1)}%`;
      default: return v.toLocaleString();
    }
  };

  return (
    <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4
                    hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider font-medium">
          {title}
        </span>
        {icon && <span className="text-lg">{icon}</span>}
      </div>
      <div className="text-2xl font-bold text-[var(--text-primary)] tabular-nums">
        {typeof value === 'number' ? formatValue(value) : value}
      </div>
      {trend != null && trendPct != null && (
        <div className={`flex items-center gap-1 mt-1.5 text-xs font-medium
                        ${trend >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
          <span>{trend >= 0 ? '↑' : '↓'}</span>
          <span>{Math.abs(trendPct).toFixed(1)}%</span>
          <span className="text-[var(--text-muted)] font-normal ml-1">vs previous</span>
        </div>
      )}
    </div>
  );
}
"""

    # ── Multi-Step Form ─────────────────────────────────────────────

    def _multi_step_form(self, spec: IntentSpec) -> str:
        # Find entity with most fields
        target = max(spec.entities, key=lambda e: len(e.fields)) if spec.entities else None
        if not target:
            return "// No entities found\nexport {};\n"

        fields = target.fields
        # Split into steps of 3-4 fields
        step_size = max(3, min(4, len(fields) // 3 + 1))
        steps = []
        for i in range(0, len(fields), step_size):
            chunk = fields[i:i + step_size]
            steps.append(chunk)
        if not steps:
            steps = [fields]

        step_labels = [f"Step {i + 1}" for i in range(len(steps))]

        return f"""import {{ useState }} from 'react';
import {{ useToast }} from './Toast';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const STEPS = {step_labels};

interface MultiStepFormProps {{
  entitySlug: string;
  fields: {{ name: string; type: string; required: boolean }}[];
  onComplete: () => void;
  onCancel: () => void;
}}

export default function MultiStepForm({{ entitySlug, fields, onComplete, onCancel }}: MultiStepFormProps) {{
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState<Record<string, string>>({{}}); 
  const [submitting, setSubmitting] = useState(false);
  const {{ addToast }} = useToast();

  const stepSize = Math.ceil(fields.length / STEPS.length);
  const currentFields = fields.slice(step * stepSize, (step + 1) * stepSize);

  const getInputType = (fieldType: string): string => {{
    const map: Record<string, string> = {{
      str: 'text', int: 'number', float: 'number', bool: 'checkbox',
      datetime: 'datetime-local', email: 'email',
    }};
    return map[fieldType] || 'text';
  }};

  const handleSubmit = async () => {{
    setSubmitting(true);
    try {{
      await fetch(`${{API_BASE}}/${{entitySlug}}`, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(formData),
      }});
      addToast('Created successfully', 'success');
      onComplete();
    }} catch {{
      addToast('Failed to create', 'error');
    }} finally {{
      setSubmitting(false);
    }}
  }};

  const isLastStep = step === STEPS.length - 1;

  return (
    <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-6 max-w-lg mx-auto">
      {{/* Progress bar */}}
      <div className="flex items-center gap-2 mb-6">
        {{STEPS.map((label, i) => (
          <div key={{i}} className="flex-1">
            <div className={{`h-1.5 rounded-full ${{
              i < step ? 'bg-[var(--color-primary)]'
              : i === step ? 'bg-[var(--color-primary)]/60'
              : 'bg-[var(--bg-tertiary)]'
            }}`}} />
            <span className={{`text-[10px] mt-1 block text-center ${{
              i <= step ? 'text-[var(--color-primary)]' : 'text-[var(--text-muted)]'
            }}`}}>
              {{label}}
            </span>
          </div>
        ))}}
      </div>

      {{/* Fields */}}
      <div className="space-y-4">
        {{currentFields.map(f => (
          <div key={{f.name}}>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
              {{f.name.replace(/_/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase())}}
              {{f.required && <span className="text-red-500 ml-0.5">*</span>}}
            </label>
            <input
              type={{getInputType(f.type)}}
              value={{formData[f.name] || ''}}
              onChange={{e => setFormData(prev => ({{ ...prev, [f.name]: e.target.value }}))}}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)]
                         bg-[var(--bg-primary)] text-[var(--text-primary)]
                         focus:ring-2 focus:ring-[var(--color-primary)] focus:outline-none text-sm"
              placeholder={{`Enter ${{f.name.replace(/_/g, ' ')}}`}}
            />
          </div>
        ))}}
      </div>

      {{/* Navigation */}}
      <div className="flex justify-between mt-6 pt-4 border-t border-[var(--border-color)]">
        <button
          onClick={{step > 0 ? () => setStep(s => s - 1) : onCancel}}
          className="px-4 py-2 text-sm rounded-lg border border-[var(--border-color)]
                     text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"
        >
          {{step > 0 ? 'Back' : 'Cancel'}}
        </button>
        <button
          onClick={{isLastStep ? handleSubmit : () => setStep(s => s + 1)}}
          disabled={{submitting}}
          className="px-4 py-2 text-sm rounded-lg bg-[var(--color-primary)] text-white
                     hover:opacity-90 disabled:opacity-50"
        >
          {{submitting ? 'Saving...' : isLastStep ? 'Create' : 'Next →'}}
        </button>
      </div>
    </div>
  );
}}
"""

    # ── Data Export Panel ───────────────────────────────────────────

    def _data_export_panel(self, spec: IntentSpec) -> str:
        entity_options = "\n".join(
            f'      {{ label: "{ent.name}", value: "{ent.name.lower().replace(" ", "_")}s" }},'
            for ent in spec.entities
        )

        return f"""import {{ useState }} from 'react';
import {{ IconDownload }} from './Icons';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const ENTITIES = [
{entity_options}
];

const FORMATS = [
  {{ label: 'CSV', value: 'csv' }},
  {{ label: 'JSON', value: 'json' }},
];

export default function DataExportPanel() {{
  const [entity, setEntity] = useState(ENTITIES[0]?.value || '');
  const [format, setFormat] = useState('csv');
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {{
    setExporting(true);
    try {{
      const res = await fetch(`${{API_BASE}}/${{entity}}`);
      const data = await res.json();
      const items = Array.isArray(data) ? data : [];

      let content: string;
      let mediaType: string;
      let ext: string;

      if (format === 'csv') {{
        const cols = items.length > 0 ? Object.keys(items[0]) : [];
        const header = cols.join(',');
        const rows = items.map(item =>
          cols.map(c => {{
            const v = String(item[c] ?? '').replace(/"/g, '""');
            return `"${{v}}"`;
          }}).join(',')
        );
        content = [header, ...rows].join('\\n');
        mediaType = 'text/csv';
        ext = 'csv';
      }} else {{
        content = JSON.stringify(items, null, 2);
        mediaType = 'application/json';
        ext = 'json';
      }}

      const blob = new Blob([content], {{ type: mediaType }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${{entity}}.${{ext}}`;
      a.click();
      URL.revokeObjectURL(url);
    }} catch (err) {{
      console.error('Export failed:', err);
    }} finally {{
      setExporting(false);
    }}
  }};

  return (
    <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4">
      <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Export Data</h3>
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-[var(--text-muted)] mb-1">Entity</label>
          <select
            value={{entity}}
            onChange={{e => setEntity(e.target.value)}}
            className="px-3 py-1.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)]
                       text-[var(--text-primary)] text-sm"
          >
            {{ENTITIES.map(e => <option key={{e.value}} value={{e.value}}>{{e.label}}</option>)}}
          </select>
        </div>
        <div>
          <label className="block text-xs text-[var(--text-muted)] mb-1">Format</label>
          <select
            value={{format}}
            onChange={{e => setFormat(e.target.value)}}
            className="px-3 py-1.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)]
                       text-[var(--text-primary)] text-sm"
          >
            {{FORMATS.map(f => <option key={{f.value}} value={{f.value}}>{{f.label}}</option>)}}
          </select>
        </div>
        <button
          onClick={{handleExport}}
          disabled={{exporting}}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
                     bg-[var(--color-primary)] text-white hover:opacity-90 disabled:opacity-50"
        >
          <IconDownload width={{14}} height={{14}} />
          {{exporting ? 'Exporting...' : 'Export'}}
        </button>
      </div>
    </div>
  );
}}
"""

    # ── Real-Time Visualization Components ────────────────────────────

    def _gauge_chart(self) -> str:
        return """import { useEffect, useRef } from 'react';

interface GaugeChartProps {
  value: number;
  max?: number;
  label: string;
  unit?: string;
  color?: string;
  size?: number;
}

export default function GaugeChart({ value, max = 100, label, unit = '%', color, size = 160 }: GaugeChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const cx = size / 2, cy = size / 2, r = size * 0.38;
    const startAngle = 0.75 * Math.PI;
    const endAngle = 2.25 * Math.PI;
    const pct = Math.min(value / max, 1);
    const fillAngle = startAngle + (endAngle - startAngle) * pct;

    ctx.clearRect(0, 0, size, size);

    // Background arc
    ctx.beginPath();
    ctx.arc(cx, cy, r, startAngle, endAngle);
    ctx.lineWidth = 12;
    ctx.strokeStyle = 'var(--bg-tertiary, #e5e7eb)';
    ctx.lineCap = 'round';
    ctx.stroke();

    // Fill arc
    const gaugeColor = color || (pct > 0.7 ? '#10b981' : pct > 0.4 ? '#f59e0b' : '#ef4444');
    ctx.beginPath();
    ctx.arc(cx, cy, r, startAngle, fillAngle);
    ctx.lineWidth = 12;
    ctx.strokeStyle = gaugeColor;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Center text
    ctx.fillStyle = 'var(--text-primary, #111)';
    ctx.font = `bold ${size * 0.18}px system-ui`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${Math.round(value)}${unit}`, cx, cy - 4);

    ctx.fillStyle = 'var(--text-muted, #666)';
    ctx.font = `${size * 0.085}px system-ui`;
    ctx.fillText(label, cx, cy + size * 0.15);
  }, [value, max, label, unit, color, size]);

  return <canvas ref={canvasRef} style={{ width: size, height: size }} className="mx-auto" />;
}
"""

    def _heatmap_grid(self) -> str:
        return """import { useMemo } from 'react';

interface HeatmapGridProps {
  data: { row: string; col: string; value: number }[];
  title?: string;
  colorScale?: [string, string, string]; // low, mid, high
}

function interpolateColor(low: string, mid: string, high: string, pct: number): string {
  const hex = (c: string) => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const toHex = (n: number) => Math.round(n).toString(16).padStart(2, '0');

  const [lr, lg, lb] = hex(low);
  const [mr, mg, mb] = hex(mid);
  const [hr, hg, hb] = hex(high);

  if (pct <= 0.5) {
    const t = pct * 2;
    return '#' + toHex(lr + (mr - lr) * t) + toHex(lg + (mg - lg) * t) + toHex(lb + (mb - lb) * t);
  }
  const t = (pct - 0.5) * 2;
  return '#' + toHex(mr + (hr - mr) * t) + toHex(mg + (hg - mg) * t) + toHex(mb + (hb - mb) * t);
}

export default function HeatmapGrid({ data, title, colorScale = ['#eff6ff', '#3b82f6', '#1e3a5f'] }: HeatmapGridProps) {
  const { rows, cols, matrix, maxVal } = useMemo(() => {
    const rowSet = [...new Set(data.map(d => d.row))];
    const colSet = [...new Set(data.map(d => d.col))];
    const lookup = new Map(data.map(d => [`${d.row}:${d.col}`, d.value]));
    const mx = Math.max(...data.map(d => d.value), 1);
    return { rows: rowSet, cols: colSet, matrix: lookup, maxVal: mx };
  }, [data]);

  return (
    <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4 overflow-x-auto">
      {title && <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">{title}</h3>}
      <table className="text-xs">
        <thead>
          <tr>
            <th className="p-1" />
            {cols.map(c => <th key={c} className="p-1 text-[var(--text-muted)] font-normal truncate max-w-[80px]">{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r}>
              <td className="p-1 text-[var(--text-muted)] font-medium pr-2 truncate max-w-[100px]">{r}</td>
              {cols.map(c => {
                const val = matrix.get(`${r}:${c}`) ?? 0;
                const bg = interpolateColor(colorScale[0], colorScale[1], colorScale[2], val / maxVal);
                return (
                  <td key={c} className="p-1" title={`${r} × ${c}: ${val}`}>
                    <div className="w-8 h-8 rounded flex items-center justify-center text-[10px] font-medium"
                         style={{ background: bg, color: val / maxVal > 0.5 ? '#fff' : 'var(--text-primary)' }}>
                      {val}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
"""

    def _geo_map(self) -> str:
        return """import { useMemo, useRef, useEffect } from 'react';

interface MapPoint {
  id: string;
  label: string;
  lat: number;
  lng: number;
  value?: number;
  status?: string;
}

interface GeoMapProps {
  points: MapPoint[];
  title?: string;
  width?: number;
  height?: number;
}

function project(lat: number, lng: number, w: number, h: number, bounds: {minLat:number,maxLat:number,minLng:number,maxLng:number}) {
  const x = ((lng - bounds.minLng) / (bounds.maxLng - bounds.minLng)) * w * 0.85 + w * 0.075;
  const y = ((bounds.maxLat - lat) / (bounds.maxLat - bounds.minLat)) * h * 0.85 + h * 0.075;
  return { x, y };
}

export default function GeoMap({ points, title, width = 600, height = 400 }: GeoMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const bounds = useMemo(() => {
    if (!points.length) return { minLat: 0, maxLat: 1, minLng: 0, maxLng: 1 };
    const lats = points.map(p => p.lat);
    const lngs = points.map(p => p.lng);
    const pad = 2;
    return {
      minLat: Math.min(...lats) - pad,
      maxLat: Math.max(...lats) + pad,
      minLng: Math.min(...lngs) - pad,
      maxLng: Math.max(...lngs) + pad,
    };
  }, [points]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    // Grid lines
    ctx.strokeStyle = 'var(--border-color, #e5e7eb)';
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 8; i++) {
      const x = (width / 8) * i;
      const y = (height / 8) * i;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }

    // Points
    const statusColors: Record<string, string> = {
      active: '#10b981', inactive: '#ef4444', pending: '#f59e0b', default: '#3b82f6'
    };

    points.forEach(p => {
      const { x, y } = project(p.lat, p.lng, width, height, bounds);
      const r = p.value ? Math.max(4, Math.min(12, Math.sqrt(p.value) * 1.5)) : 6;
      const color = statusColors[p.status ?? 'default'] ?? statusColors.default;

      // Glow
      ctx.beginPath();
      ctx.arc(x, y, r + 4, 0, Math.PI * 2);
      ctx.fillStyle = color + '30';
      ctx.fill();

      // Point
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }, [points, width, height, bounds]);

  return (
    <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4">
      {title && <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">{title}</h3>}
      <canvas ref={canvasRef} style={{ width, height }} className="w-full rounded-lg" />
      <div className="mt-2 flex gap-4 text-xs text-[var(--text-muted)]">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Active</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" /> Pending</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> Inactive</span>
      </div>
      <div ref={tooltipRef} className="hidden absolute bg-black/80 text-white text-xs px-2 py-1 rounded" />
    </div>
  );
}
"""

    def _live_feed(self) -> str:
        return """import { useState, useEffect, useRef } from 'react';

interface FeedEvent {
  id: string;
  entity: string;
  event_type: string;
  timestamp: string;
  payload?: Record<string, unknown>;
}

interface LiveFeedProps {
  endpoint?: string;
  maxItems?: number;
  title?: string;
}

export default function LiveFeed({ endpoint = '/api/v1/stream', maxItems = 50, title = 'Live Events' }: LiveFeedProps) {
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [paused, setPaused] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (paused) return;
    const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
    const url = `${apiBase.replace(/\\/api\\/v1$/, '')}${endpoint}`;

    let source: EventSource;
    try {
      source = new EventSource(url);
      source.onopen = () => setConnected(true);
      source.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data) as FeedEvent;
          setEvents(prev => [data, ...prev].slice(0, maxItems));
        } catch {}
      };
      source.onerror = () => setConnected(false);
    } catch {
      setConnected(false);
    }
    return () => source?.close();
  }, [endpoint, maxItems, paused]);

  const severityColor = (type: string) => {
    if (type.includes('error') || type.includes('fail')) return 'bg-red-500';
    if (type.includes('warn') || type.includes('status')) return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  return (
    <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--border-color)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">{title}</h3>
          <span className="text-xs text-[var(--text-muted)]">({events.length} events)</span>
        </div>
        <button onClick={() => setPaused(p => !p)}
          className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:text-[var(--text-primary)]">
          {paused ? '▶ Resume' : '⏸ Pause'}
        </button>
      </div>
      <div ref={listRef} className="max-h-96 overflow-y-auto divide-y divide-[var(--border-color)]">
        {events.map(ev => (
          <div key={ev.id} className="px-4 py-2 text-xs flex items-start gap-2 hover:bg-[var(--bg-tertiary)] transition-colors">
            <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${severityColor(ev.event_type)}`} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-[var(--text-primary)]">{ev.entity}</span>
                <span className="text-[var(--text-muted)]">{ev.event_type}</span>
              </div>
              {ev.payload && (
                <div className="text-[var(--text-muted)] truncate mt-0.5">
                  {JSON.stringify(ev.payload).slice(0, 80)}
                </div>
              )}
            </div>
            <time className="text-[var(--text-muted)] whitespace-nowrap">
              {new Date(ev.timestamp).toLocaleTimeString()}
            </time>
          </div>
        ))}
        {events.length === 0 && (
          <div className="px-4 py-8 text-center text-sm text-[var(--text-muted)]">
            {connected ? 'Waiting for events...' : 'Connecting to event stream...'}
          </div>
        )}
      </div>
    </div>
  );
}
"""

    def _sparkline_grid(self) -> str:
        return """import { useRef, useEffect } from 'react';

interface SparklineProps {
  data: number[];
  label: string;
  color?: string;
  width?: number;
  height?: number;
  showValue?: boolean;
}

function Sparkline({ data, label, color = '#3b82f6', width = 140, height = 40, showValue = true }: SparklineProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const current = data[data.length - 1] ?? 0;
  const prev = data[data.length - 2] ?? current;
  const trend = current >= prev ? '↑' : '↓';
  const trendColor = current >= prev ? '#10b981' : '#ef4444';

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const step = width / (data.length - 1 || 1);

    // Fill gradient
    const grad = ctx.createLinearGradient(0, 0, 0, height);
    grad.addColorStop(0, color + '30');
    grad.addColorStop(1, color + '05');

    ctx.beginPath();
    ctx.moveTo(0, height);
    data.forEach((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / range) * (height * 0.8) - height * 0.1;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.lineTo(width, height);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    data.forEach((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / range) * (height * 0.8) - height * 0.1;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }, [data, color, width, height]);

  return (
    <div className="flex items-center gap-3 p-3 bg-[var(--surface-card)] rounded-lg border border-[var(--border-color)]">
      <div className="flex-1 min-w-0">
        <div className="text-xs text-[var(--text-muted)] truncate">{label}</div>
        {showValue && (
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-lg font-semibold text-[var(--text-primary)]">{current.toLocaleString()}</span>
            <span className="text-xs font-medium" style={{ color: trendColor }}>{trend}</span>
          </div>
        )}
      </div>
      <canvas ref={canvasRef} style={{ width, height }} />
    </div>
  );
}

interface SparklineGridProps {
  metrics: { label: string; data: number[]; color?: string }[];
  title?: string;
  columns?: number;
}

export default function SparklineGrid({ metrics, title, columns = 3 }: SparklineGridProps) {
  return (
    <div>
      {title && <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">{title}</h3>}
      <div className={`grid gap-3`} style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {metrics.map(m => <Sparkline key={m.label} {...m} />)}
      </div>
    </div>
  );
}
"""

    def _treemap_chart(self) -> str:
        return """import { useMemo, useRef, useEffect } from 'react';

interface TreemapItem {
  label: string;
  value: number;
  color?: string;
}

interface TreemapChartProps {
  data: TreemapItem[];
  title?: string;
  width?: number;
  height?: number;
}

function squarify(items: TreemapItem[], x: number, y: number, w: number, h: number): { item: TreemapItem; x: number; y: number; w: number; h: number }[] {
  if (!items.length) return [];
  if (items.length === 1) return [{ item: items[0], x, y, w, h }];

  const total = items.reduce((s, i) => s + i.value, 0);
  const half = total / 2;
  let sum = 0, splitIdx = 0;
  for (let i = 0; i < items.length - 1; i++) {
    sum += items[i].value;
    if (sum >= half) { splitIdx = i + 1; break; }
  }
  if (splitIdx === 0) splitIdx = 1;

  const left = items.slice(0, splitIdx);
  const right = items.slice(splitIdx);
  const leftSum = left.reduce((s, i) => s + i.value, 0);
  const ratio = leftSum / total;

  if (w >= h) {
    const lw = w * ratio;
    return [
      ...squarify(left, x, y, lw, h),
      ...squarify(right, x + lw, y, w - lw, h),
    ];
  }
  const lh = h * ratio;
  return [
    ...squarify(left, x, y, w, lh),
    ...squarify(right, x, y + lh, w, h - lh),
  ];
}

const PALETTE = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

export default function TreemapChart({ data, title, width = 500, height = 300 }: TreemapChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sorted = useMemo(() => [...data].sort((a, b) => b.value - a.value), [data]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !sorted.length) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const rects = squarify(sorted, 2, 2, width - 4, height - 4);
    rects.forEach((r, i) => {
      const c = r.item.color || PALETTE[i % PALETTE.length];
      ctx.fillStyle = c;
      ctx.fillRect(r.x + 1, r.y + 1, r.w - 2, r.h - 2);

      if (r.w > 40 && r.h > 24) {
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 11px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText(r.item.label, r.x + r.w / 2, r.y + r.h / 2 - 4, r.w - 8);
        ctx.font = '10px system-ui';
        ctx.fillText(r.item.value.toLocaleString(), r.x + r.w / 2, r.y + r.h / 2 + 10, r.w - 8);
      }
    });
  }, [sorted, width, height]);

  return (
    <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4">
      {title && <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">{title}</h3>}
      <canvas ref={canvasRef} style={{ width, height }} className="w-full rounded-lg" />
    </div>
  );
}
"""

    def _radar_chart(self) -> str:
        return """import { useRef, useEffect } from 'react';

interface RadarChartProps {
  labels: string[];
  datasets: { label: string; values: number[]; color?: string }[];
  title?: string;
  size?: number;
}

export default function RadarChart({ labels, datasets, title, size = 300 }: RadarChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, size, size);

    const cx = size / 2, cy = size / 2, r = size * 0.38;
    const n = labels.length;
    if (n < 3) return;
    const angleStep = (Math.PI * 2) / n;

    // Grid rings
    for (let ring = 1; ring <= 5; ring++) {
      const rr = (r / 5) * ring;
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const a = -Math.PI / 2 + angleStep * i;
        const x = cx + Math.cos(a) * rr;
        const y = cy + Math.sin(a) * rr;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'var(--border-color, #e5e7eb)';
      ctx.lineWidth = 0.5;
      ctx.stroke();
    }

    // Axis lines + labels
    labels.forEach((label, i) => {
      const a = -Math.PI / 2 + angleStep * i;
      const x = cx + Math.cos(a) * r;
      const y = cy + Math.sin(a) * r;
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(x, y);
      ctx.strokeStyle = 'var(--border-color, #e5e7eb)';
      ctx.lineWidth = 0.5;
      ctx.stroke();

      const lx = cx + Math.cos(a) * (r + 16);
      const ly = cy + Math.sin(a) * (r + 16);
      ctx.fillStyle = 'var(--text-muted, #666)';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(label.length > 10 ? label.slice(0, 10) + '…' : label, lx, ly);
    });

    // Datasets
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
    datasets.forEach((ds, dsi) => {
      const maxVal = Math.max(...ds.values, 1);
      const color = ds.color || colors[dsi % colors.length];
      ctx.beginPath();
      ds.values.forEach((v, i) => {
        const a = -Math.PI / 2 + angleStep * i;
        const vr = (v / maxVal) * r;
        const x = cx + Math.cos(a) * vr;
        const y = cy + Math.sin(a) * vr;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = color + '20';
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Dots
      ds.values.forEach((v, i) => {
        const a = -Math.PI / 2 + angleStep * i;
        const vr = (v / maxVal) * r;
        ctx.beginPath();
        ctx.arc(cx + Math.cos(a) * vr, cy + Math.sin(a) * vr, 3, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
      });
    });
  }, [labels, datasets, size]);

  return (
    <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4">
      {title && <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">{title}</h3>}
      <canvas ref={canvasRef} style={{ width: size, height: size }} className="mx-auto" />
      <div className="mt-2 flex justify-center gap-4 text-xs text-[var(--text-muted)]">
        {datasets.map((ds, i) => (
          <span key={ds.label} className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: ds.color || ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'][i % 4] }} />
            {ds.label}
          </span>
        ))}
      </div>
    </div>
  );
}
"""

    def _use_event_stream(self) -> str:
        return """import { useState, useEffect, useCallback, useRef } from 'react';

interface StreamEvent {
  id: string;
  entity: string;
  event_type: string;
  timestamp: string;
  payload?: Record<string, unknown>;
}

interface UseEventStreamOptions {
  endpoint?: string;
  maxEvents?: number;
  autoConnect?: boolean;
}

export function useEventStream(options: UseEventStreamOptions = {}) {
  const { endpoint = '/api/v1/stream', maxEvents = 100, autoConnect = true } = options;
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
    const url = `${apiBase.replace(/\\/api\\/v1$/, '')}${endpoint}`;

    try {
      const source = new EventSource(url);
      sourceRef.current = source;

      source.onopen = () => { setConnected(true); setError(null); };
      source.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data) as StreamEvent;
          setEvents(prev => [data, ...prev].slice(0, maxEvents));
        } catch {}
      };
      source.onerror = () => {
        setConnected(false);
        setError('Connection lost');
        source.close();
        // Auto-reconnect after 3s
        setTimeout(connect, 3000);
      };
    } catch (err) {
      setError('Failed to connect');
    }
  }, [endpoint, maxEvents]);

  const disconnect = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
    setConnected(false);
  }, []);

  useEffect(() => {
    if (autoConnect) connect();
    return disconnect;
  }, [autoConnect, connect, disconnect]);

  return { events, connected, error, connect, disconnect, clear: () => setEvents([]) };
}
"""

    # ── Real-Time Monitoring Page ────────────────────────────────────

    def _realtime_page(self, spec: IntentSpec) -> str:
        entities = spec.entities or []
        entity_names = [e.name for e in entities[:4]]
        entity_labels = ", ".join(f'"{n}"' for n in entity_names)

        metric_items = []
        for e in entities[:6]:
            numeric = [f for f in e.fields if f.type in ("int", "float")]
            if numeric:
                metric_items.append(
                    f'    {{ label: "{e.name} {numeric[0].name}", data: generateMockSeries(), color: COLORS[{len(metric_items) % 6}] }},'
                )
        metrics_str = "\n".join(metric_items) if metric_items else '    { label: "Metric", data: generateMockSeries(), color: "#3b82f6" },'

        return f"""import {{ useState }} from 'react';
import LiveFeed from '../components/LiveFeed';
import SparklineGrid from '../components/SparklineGrid';
import GaugeChart from '../components/GaugeChart';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

function generateMockSeries() {{
  return Array.from({{ length: 20 }}, (_, i) => Math.round(50 + Math.sin(i * 0.5) * 30 + Math.random() * 15));
}}

const GAUGE_ITEMS = [{', '.join(f'{{ label: "{n}", value: {55 + i * 8} }}' for i, n in enumerate(entity_names))}];
const SPARKLINE_METRICS = [
{metrics_str}
];

export default function RealtimePage() {{
  const [activeTab, setActiveTab] = useState<'feed' | 'metrics'>('feed');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Real-Time Monitor</h1>
          <p className="text-sm text-[var(--text-muted)]">Live event stream and system metrics</p>
        </div>
        <div className="flex gap-1 bg-[var(--bg-tertiary)] rounded-lg p-1">
          <button
            onClick={{() => setActiveTab('feed')}}
            className={{`px-3 py-1.5 text-sm rounded-md ${{activeTab === 'feed' ? 'bg-[var(--surface-card)] shadow text-[var(--text-primary)]' : 'text-[var(--text-muted)]'}}`}}>
            Live Feed
          </button>
          <button
            onClick={{() => setActiveTab('metrics')}}
            className={{`px-3 py-1.5 text-sm rounded-md ${{activeTab === 'metrics' ? 'bg-[var(--surface-card)] shadow text-[var(--text-primary)]' : 'text-[var(--text-muted)]'}}`}}>
            Metrics
          </button>
        </div>
      </div>

      {{/* Gauges */}}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {{GAUGE_ITEMS.map(g => (
          <div key={{g.label}} className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-3">
            <GaugeChart value={{g.value}} label={{g.label}} size={{120}} />
          </div>
        ))}}
      </div>

      {{activeTab === 'feed' ? (
        <LiveFeed endpoint="/api/v1/stream" maxItems={{50}} />
      ) : (
        <SparklineGrid metrics={{SPARKLINE_METRICS}} title="System Metrics" columns={{3}} />
      )}}
    </div>
  );
}}
"""

    # ── Conversational UI Builder ────────────────────────────────────

    def _dynamic_builder_page(self, spec: IntentSpec) -> str:
        entities = spec.entities or []

        # Build entity data references
        entity_data_entries = []
        for e in entities:
            sn = e.name.lower().replace(" ", "_")
            plural = sn + "s" if not sn.endswith("s") else sn
            fields_arr = ", ".join(f'"{f.name}"' for f in e.fields[:6])
            numeric_fields_arr = ", ".join(f'"{f.name}"' for f in e.fields if f.type in ("int", "float"))
            status_fields_arr = ", ".join(f'"{f.name}"' for f in e.fields if "status" in f.name.lower())
            entity_data_entries.append(
                f'  "{sn}": {{ name: "{e.name}", endpoint: "/api/v1/{plural}", '
                f'fields: [{fields_arr}], numericFields: [{numeric_fields_arr}], '
                f'statusFields: [{status_fields_arr}] }},'
            )
        entity_data_str = "\n".join(entity_data_entries)

        return f"""import {{ useState, useRef, useEffect }} from 'react';

// Entity metadata for intelligent query interpretation
const ENTITIES: Record<string, {{
  name: string;
  endpoint: string;
  fields: string[];
  numericFields: string[];
  statusFields: string[];
}}> = {{
{entity_data_str}
}};

type WidgetType = 'table' | 'bar_chart' | 'line_chart' | 'pie_chart' | 'stat_card' | 'map';

interface QueryResult {{
  id: string;
  query: string;
  widget: WidgetType;
  entity: string;
  title: string;
  data: Record<string, unknown>[];
  pinned: boolean;
}}

// Simple local intent classifier — no API calls needed
function classifyQuery(input: string): {{ widget: WidgetType; entity: string; title: string }} {{
  const lower = input.toLowerCase();
  const entities = Object.entries(ENTITIES);

  // Find matching entity
  let matchedEntity = entities[0]?.[0] ?? '';
  for (const [key, meta] of entities) {{
    if (lower.includes(key) || lower.includes(meta.name.toLowerCase())) {{
      matchedEntity = key;
      break;
    }}
  }}

  // Classify intent
  if (/trend|over time|timeline|history/.test(lower)) {{
    return {{ widget: 'line_chart', entity: matchedEntity, title: `${{ENTITIES[matchedEntity]?.name ?? matchedEntity}} Trends` }};
  }}
  if (/compare|vs|versus|breakdown|distribution/.test(lower)) {{
    return {{ widget: 'bar_chart', entity: matchedEntity, title: `${{ENTITIES[matchedEntity]?.name ?? matchedEntity}} Comparison` }};
  }}
  if (/pie|proportion|share|percentage/.test(lower)) {{
    return {{ widget: 'pie_chart', entity: matchedEntity, title: `${{ENTITIES[matchedEntity]?.name ?? matchedEntity}} Distribution` }};
  }}
  if (/map|location|geo|where/.test(lower)) {{
    return {{ widget: 'map', entity: matchedEntity, title: `${{ENTITIES[matchedEntity]?.name ?? matchedEntity}} Locations` }};
  }}
  if (/count|how many|total|sum/.test(lower)) {{
    return {{ widget: 'stat_card', entity: matchedEntity, title: `${{ENTITIES[matchedEntity]?.name ?? matchedEntity}} Count` }};
  }}
  if (/show|list|display|find|search/.test(lower)) {{
    return {{ widget: 'table', entity: matchedEntity, title: `${{ENTITIES[matchedEntity]?.name ?? matchedEntity}} Data` }};
  }}
  return {{ widget: 'table', entity: matchedEntity, title: `${{ENTITIES[matchedEntity]?.name ?? matchedEntity}} Results` }};
}}

// Mock data generator for demo
function generateMockData(entity: string, widget: WidgetType): Record<string, unknown>[] {{
  const meta = ENTITIES[entity];
  if (!meta) return [];

  const items = Array.from({{ length: 8 }}, (_, i) => {{
    const record: Record<string, unknown> = {{ id: `${{entity}}-${{i + 1}}` }};
    meta.fields.forEach(f => {{
      if (meta.numericFields.includes(f)) record[f] = Math.round(Math.random() * 100);
      else if (meta.statusFields.includes(f)) record[f] = ['active', 'pending', 'completed'][i % 3];
      else record[f] = `${{f}}-${{i + 1}}`;
    }});
    return record;
  }});
  return items;
}}

// Widget renderers
function TableWidget({{ data, fields }}: {{ data: Record<string, unknown>[]; fields: string[] }}) {{
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--border-color)]">
            {{fields.map(f => <th key={{f}} className="text-left py-2 px-3 text-[var(--text-muted)] font-medium">{{f}}</th>)}}
          </tr>
        </thead>
        <tbody>
          {{data.slice(0, 8).map((row, i) => (
            <tr key={{i}} className="border-b border-[var(--border-color)] hover:bg-[var(--bg-tertiary)]">
              {{fields.map(f => <td key={{f}} className="py-2 px-3 text-[var(--text-primary)]">{{String(row[f] ?? '')}}</td>)}}
            </tr>
          ))}}
        </tbody>
      </table>
    </div>
  );
}}

function BarChartWidget({{ data, field }}: {{ data: Record<string, unknown>[]; field: string }}) {{
  const maxVal = Math.max(...data.map(d => Number(d[field]) || 0), 1);
  return (
    <div className="space-y-2">
      {{data.slice(0, 8).map((d, i) => (
        <div key={{i}} className="flex items-center gap-2">
          <span className="text-xs text-[var(--text-muted)] w-20 truncate">{{String(d.id ?? i)}}</span>
          <div className="flex-1 bg-[var(--bg-tertiary)] rounded-full h-5 overflow-hidden">
            <div className="h-full rounded-full bg-[var(--color-primary)] transition-all"
                 style={{{{ width: `${{(Number(d[field]) / maxVal) * 100}}%` }}}} />
          </div>
          <span className="text-xs font-medium text-[var(--text-primary)] w-12 text-right">{{String(d[field])}}</span>
        </div>
      ))}}
    </div>
  );
}}

function StatWidget({{ entity, count }}: {{ entity: string; count: number }}) {{
  return (
    <div className="text-center py-6">
      <div className="text-4xl font-bold text-[var(--color-primary)]">{{count}}</div>
      <div className="text-sm text-[var(--text-muted)] mt-1">Total {{entity}}</div>
    </div>
  );
}}

function RenderWidget({{ result }}: {{ result: QueryResult }}) {{
  const meta = ENTITIES[result.entity];
  const fields = meta?.fields ?? ['id'];

  switch (result.widget) {{
    case 'table': return <TableWidget data={{result.data}} fields={{fields}} />;
    case 'bar_chart': return <BarChartWidget data={{result.data}} field={{meta?.numericFields[0] ?? 'id'}} />;
    case 'stat_card': return <StatWidget entity={{result.entity}} count={{result.data.length}} />;
    default: return <TableWidget data={{result.data}} fields={{fields}} />;
  }}
}}

// Suggestion chips
const SUGGESTIONS = [
  'Show me all data',
  'Compare metrics',
  'What are the trends?',
  'How many records total?',
  'Show status breakdown',
];

export default function DynamicBuilderPage() {{
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<QueryResult[]>([]);
  const [processing, setProcessing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (q?: string) => {{
    const text = q ?? query;
    if (!text.trim()) return;
    setProcessing(true);

    // Simulate brief processing time
    setTimeout(() => {{
      const classified = classifyQuery(text);
      const data = generateMockData(classified.entity, classified.widget);
      const result: QueryResult = {{
        id: `q-${{Date.now()}}`,
        query: text,
        ...classified,
        data,
        pinned: false,
      }};
      setResults(prev => [result, ...prev]);
      setQuery('');
      setProcessing(false);
    }}, 300);
  }};

  const togglePin = (id: string) => {{
    setResults(prev => prev.map(r => r.id === id ? {{ ...r, pinned: !r.pinned }} : r));
  }};

  const removeResult = (id: string) => {{
    setResults(prev => prev.filter(r => r.id !== id));
  }};

  const pinned = results.filter(r => r.pinned);
  const unpinned = results.filter(r => !r.pinned);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Dynamic Builder</h1>
        <p className="text-sm text-[var(--text-muted)]">
          Describe what you want to see — the system will render the right visualization
        </p>
      </div>

      {{/* Query input */}}
      <div className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4">
        <div className="flex gap-2">
          <input
            ref={{inputRef}}
            type="text"
            value={{query}}
            onChange={{e => setQuery(e.target.value)}}
            onKeyDown={{e => e.key === 'Enter' && handleSubmit()}}
            placeholder="e.g. Show me sales trends, Compare products by revenue..."
            className="flex-1 px-4 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)]
                       text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none
                       focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
          />
          <button
            onClick={{() => handleSubmit()}}
            disabled={{processing || !query.trim()}}
            className="px-5 py-2.5 rounded-lg bg-[var(--color-primary)] text-white font-medium text-sm
                       hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {{processing ? '⏳' : '✨ Generate'}}
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {{SUGGESTIONS.map(s => (
            <button key={{s}} onClick={{() => {{ setQuery(s); handleSubmit(s); }}}}
              className="text-xs px-3 py-1.5 rounded-full bg-[var(--bg-tertiary)] text-[var(--text-muted)]
                         hover:text-[var(--text-primary)] hover:bg-[var(--border-color)] transition-colors">
              {{s}}
            </button>
          ))}}
        </div>
      </div>

      {{/* Pinned results */}}
      {{pinned.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3">📌 Pinned Dashboard</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {{pinned.map(r => (
              <div key={{r.id}} className="bg-[var(--surface-card)] rounded-xl border-2 border-[var(--color-primary)]/30 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">{{r.title}}</h3>
                  <button onClick={{() => togglePin(r.id)}} className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                    Unpin
                  </button>
                </div>
                <RenderWidget result={{r}} />
              </div>
            ))}}
          </div>
        </div>
      )}}

      {{/* Query results */}}
      {{unpinned.map(r => (
        <div key={{r.id}} className="bg-[var(--surface-card)] rounded-xl border border-[var(--border-color)] p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">{{r.title}}</h3>
              <p className="text-xs text-[var(--text-muted)]">Query: "{{r.query}}" → {{r.widget}}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={{() => togglePin(r.id)}}
                className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                📌 Pin
              </button>
              <button onClick={{() => removeResult(r.id)}}
                className="text-xs px-2 py-1 rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:text-red-500">
                ✕
              </button>
            </div>
          </div>
          <RenderWidget result={{r}} />
        </div>
      ))}}

      {{results.length === 0 && (
        <div className="text-center py-16 text-[var(--text-muted)]">
          <div className="text-4xl mb-3">🔮</div>
          <p className="text-lg font-medium">Ask a question to get started</p>
          <p className="text-sm mt-1">Try one of the suggestions above, or type your own query</p>
        </div>
      )}}
    </div>
  );
}}
"""

    # ── Advanced Analytics Page ───────────────────────────────────────

    def _advanced_analytics_page(self, spec: IntentSpec) -> str:
        entities = spec.entities or []

        treemap_items = ", ".join(
            f'{{ label: "{e.name}", value: {50 + i * 15} }}'
            for i, e in enumerate(entities[:8])
        )

        entity_labels = ", ".join(f'"{e.name}"' for e in entities[:6])

        heatmap_entries = []
        for e in entities[:4]:
            for f in e.fields[:3]:
                heatmap_entries.append(
                    f'{{ row: "{e.name}", col: "{f.name}", value: Math.round(Math.random() * 100) }}'
                )
        heatmap_str = ", ".join(heatmap_entries) if heatmap_entries else '{ row: "A", col: "B", value: 50 }'

        radar_values = ", ".join(str(40 + i * 10) for i, _ in enumerate(entities[:6]))

        return f"""import TreemapChart from '../components/TreemapChart';
import RadarChart from '../components/RadarChart';
import HeatmapGrid from '../components/HeatmapGrid';
import SparklineGrid from '../components/SparklineGrid';

const TREEMAP_DATA = [{treemap_items}];
const RADAR_LABELS = [{entity_labels}];
const RADAR_DATA = [
  {{ label: 'Current', values: [{radar_values}], color: '#3b82f6' }},
  {{ label: 'Target', values: [{", ".join(["85"] * min(len(entities), 6))}], color: '#10b981' }},
];
const HEATMAP_DATA = [{heatmap_str}];

function generateSeries() {{
  return Array.from({{ length: 20 }}, () => Math.round(Math.random() * 100));
}}

const SPARKLINES = [{", ".join(f'{{ label: "{e.name}", data: generateSeries(), color: ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4"][{i % 6}] }}' for i, e in enumerate(entities[:6]))}];

export default function AdvancedAnalyticsPage() {{
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Advanced Analytics</h1>
        <p className="text-sm text-[var(--text-muted)]">Deep-dive into cross-entity correlations and metrics</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TreemapChart data={{TREEMAP_DATA}} title="Entity Volume Distribution" />
        <RadarChart labels={{RADAR_LABELS}} datasets={{RADAR_DATA}} title="Multi-Metric Health" />
      </div>

      <HeatmapGrid data={{HEATMAP_DATA}} title="Cross-Entity Field Heatmap" />

      <SparklineGrid metrics={{SPARKLINES}} title="Entity Trend Overview" columns={{3}} />
    </div>
  );
}}
"""
