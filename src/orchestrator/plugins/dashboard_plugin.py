"""Dashboard Plugins -- domain-specific React TSX widget components.

Each plugin generates a self-contained React component (TypeScript/TSX)
that can be embedded in the generated frontend dashboard.
"""

from __future__ import annotations

from src.orchestrator.intent_schema import IntentSpec
from src.orchestrator.logging import get_logger

logger = get_logger(__name__)


class StatusDistributionWidget:
    """Generates a donut/pie chart showing entity status breakdown."""

    def applies_to(self, spec: IntentSpec) -> bool:
        # Applies when any entity has a status-like field
        for entity in spec.entities:
            if any(f.name.lower() in ("status", "state", "stage", "phase") for f in entity.fields):
                return True
        return len(spec.entities) >= 2

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        entity_names = [e.name for e in spec.entities[:6]]
        tabs = "\n".join(
            f"      {{ label: '{e.replace('_', ' ').title()}', value: '{e}' }},"
            for e in entity_names
        )
        return {
            "frontend/src/components/widgets/StatusDistribution.tsx": f"""\
import {{ useState, useMemo }} from 'react';

interface DataItem {{
  status: string;
  count: number;
  color: string;
}}

const STATUS_COLORS: Record<string, string> = {{
  active: '#22c55e',
  pending: '#f59e0b',
  completed: '#3b82f6',
  inactive: '#94a3b8',
  critical: '#ef4444',
  in_progress: '#8b5cf6',
}};

const ENTITY_TABS = [
{tabs}
];

export default function StatusDistribution({{ data }}: {{ data: Record<string, DataItem[]> }}) {{
  const [activeTab, setActiveTab] = useState(ENTITY_TABS[0]?.value ?? '');

  const items = useMemo(() => data[activeTab] ?? [], [data, activeTab]);
  const total = useMemo(() => items.reduce((s, i) => s + i.count, 0), [items]);

  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm dark:bg-gray-800 dark:border-gray-700">
      <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-3">
        Status Distribution
      </h3>

      {{/* Tab selector */}}
      <div className="flex gap-1 mb-4 flex-wrap">
        {{ENTITY_TABS.map(t => (
          <button
            key={{t.value}}
            onClick={{() => setActiveTab(t.value)}}
            className={{`px-2 py-1 text-xs rounded-md ${{
              activeTab === t.value
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
            }}`}}
          >
            {{t.label}}
          </button>
        ))}}
      </div>

      {{/* Bar chart */}}
      <div className="space-y-2">
        {{items.map(item => (
          <div key={{item.status}} className="flex items-center gap-2">
            <span className="w-24 text-xs text-gray-500 truncate">{{item.status}}</span>
            <div className="flex-1 h-4 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{{{
                  width: total > 0 ? `${{(item.count / total) * 100}}%` : '0%',
                  backgroundColor: item.color || STATUS_COLORS[item.status.toLowerCase()] || '#94a3b8',
                }}}}
              />
            </div>
            <span className="text-xs font-mono text-gray-600 dark:text-gray-400 w-8 text-right">
              {{item.count}}
            </span>
          </div>
        ))}}
      </div>

      <p className="text-xs text-gray-400 mt-3">Total: {{total}}</p>
    </div>
  );
}}
""",
        }


class TimelineWidget:
    """Generates a timeline/activity-feed widget."""

    def applies_to(self, spec: IntentSpec) -> bool:
        for entity in spec.entities:
            if any(f.type in ("datetime", "date") for f in entity.fields):
                return True
        return False

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        return {
            "frontend/src/components/widgets/Timeline.tsx": """\
import { useMemo } from 'react';

interface TimelineEvent {
  id: string;
  title: string;
  description?: string;
  timestamp: string;
  type?: 'info' | 'success' | 'warning' | 'error';
}

const TYPE_STYLES: Record<string, string> = {
  info: 'bg-blue-500',
  success: 'bg-green-500',
  warning: 'bg-amber-500',
  error: 'bg-red-500',
};

export default function Timeline({ events }: { events: TimelineEvent[] }) {
  const sorted = useMemo(
    () => [...events].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()),
    [events],
  );

  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm dark:bg-gray-800 dark:border-gray-700">
      <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-4">
        Activity Timeline
      </h3>

      <div className="relative">
        <div className="absolute left-2 top-0 bottom-0 w-px bg-gray-200 dark:bg-gray-600" />

        <div className="space-y-4">
          {sorted.slice(0, 20).map(event => (
            <div key={event.id} className="flex items-start gap-3 pl-1">
              <div
                className={`w-4 h-4 rounded-full flex-shrink-0 mt-0.5 ${
                  TYPE_STYLES[event.type ?? 'info']
                }`}
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                  {event.title}
                </p>
                {event.description && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {event.description}
                  </p>
                )}
                <time className="text-xs text-gray-400 dark:text-gray-500">
                  {new Date(event.timestamp).toLocaleString()}
                </time>
              </div>
            </div>
          ))}
        </div>
      </div>

      {sorted.length > 20 && (
        <p className="text-xs text-gray-400 mt-3 text-center">
          Showing 20 of {sorted.length} events
        </p>
      )}
    </div>
  );
}
""",
        }


class MetricCardWidget:
    """Generates a KPI metric card component with sparkline."""

    def applies_to(self, spec: IntentSpec) -> bool:
        # Always useful
        return True

    def generate(self, spec: IntentSpec, **kwargs) -> dict[str, str]:
        return {
            "frontend/src/components/widgets/MetricCard.tsx": """\
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  unit?: string;
  sparkline?: number[];
}

function MiniSparkline({ data }: { data: number[] }) {
  if (data.length < 2) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 80;
  const h = 24;
  const points = data
    .map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`)
    .join(' ');
  return (
    <svg width={w} height={h} className="text-blue-500">
      <polyline fill="none" stroke="currentColor" strokeWidth="1.5" points={points} />
    </svg>
  );
}

export default function MetricCard({ title, value, change, unit, sparkline }: MetricCardProps) {
  const changeColor =
    change === undefined ? '' : change >= 0 ? 'text-green-600' : 'text-red-600';
  const arrow = change === undefined ? '' : change >= 0 ? '↑' : '↓';

  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm dark:bg-gray-800 dark:border-gray-700">
      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        {title}
      </p>
      <div className="flex items-end justify-between mt-2">
        <div>
          <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</span>
          {unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}
          {change !== undefined && (
            <span className={`text-xs ml-2 ${changeColor}`}>
              {arrow} {Math.abs(change)}%
            </span>
          )}
        </div>
        {sparkline && <MiniSparkline data={sparkline} />}
      </div>
    </div>
  );
}
""",
        }
