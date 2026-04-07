import json
import logging
from typing import Any
from src.orchestrator.generators.ui_schema import UIAppSpec, UIPageSpec, UIWidget

logger = logging.getLogger(__name__)

class DeterministicReactHydrator:
    """Compiles LLM-generated UI AST (JSON) into raw React TSX files."""
    
    def __init__(self):
        self._imports = set([
            "import { useEffect, useState } from 'react';",
            "import { useToast } from '../components/Toast';",
            "import { CardSkeleton, TableSkeleton } from '../components/Skeleton';",
            "import { Plus, Trash, Eye, Activity } from 'lucide-react';"
        ])
    
    def compile_page(self, ast_json: str) -> str:
        """Takes raw JSON from the LLM, validates via Pydantic, and compiles to TSX."""
        try:
            # Strip potential LLM markdown artifacts
            if ast_json.startswith("`"):
                ast_json = "\n".join(ast_json.split("\n")[1:-1])
            
            data = json.loads(ast_json)
            # Support both if the LLM returned the whole app or just the page
            if "pages" in data:
                page_data = data["pages"][0]
            else:
                page_data = data
                
            page_spec = UIPageSpec(**page_data)
        except Exception as e:
            logger.error(f"Failed to parse or validate LLM JSON AST: {e}")
            # Fallback to a safe error component
            return self._generate_error_fallback(str(e))
            
        return self._render_tsx(page_spec)
        
    def _render_tsx(self, page: UIPageSpec) -> str:
        components_code = []
        
        # Determine layout wrapper
        grid_class = "grid grid-cols-1 md:grid-cols-4 gap-6" if page.layout_type == "BentoGrid" else "flex flex-col space-y-6"
        
        # Pre-compute state variables based on widgets
        state_hooks = []
        fetch_hooks = []
        
        for idx, widget in enumerate(page.widgets):
            var_name = f"data_{widget.widget_id.replace('-', '_')}_{idx}"
            state_hooks.append(f"  const [{var_name}, set{var_name.capitalize()}] = useState<any>(null);")
            
            # Setup fetch logic for onLoad actions
            onload_actions = [a for a in widget.actions if a.trigger == "onLoad"]
            if onload_actions and widget.bound_entity:
                action = onload_actions[0]
                fetch_hooks.append(f"    fetch(`{action.api_endpoint}`)")
                fetch_hooks.append(f"      .then(res => res.json())")
                fetch_hooks.append(f"      .then(data => set{var_name.capitalize()}(data))")
                fetch_hooks.append(f"      .catch(err => console.error(err));")
            
            # Render individual widgets
            widget_code = self._render_widget(widget, var_name)
            components_code.append(widget_code)

        # Build final TSX
        imports_block = "\n".join(sorted(list(self._imports)))
        state_block = "\n".join(state_hooks)
        effect_block = "  useEffect(() => {\n" + "\n".join(fetch_hooks) + "\n  }, []);" if fetch_hooks else ""
        widgets_block = "\n".join(components_code)
        
        return f"""{imports_block}

export default function {page.page_name}() {{
{state_block}

{effect_block}

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">{page.page_name}</h1>
      </header>
      
      <div className="{grid_class}">
{widgets_block}
      </div>
    </div>
  );
}}
"""
        
    def _render_widget(self, w: UIWidget, var_name: str) -> str:
        span_classes = {
            "quarter": "col-span-1",
            "third": "col-span-1 md:col-span-1",
            "half": "col-span-1 md:col-span-2",
            "full": "col-span-1 md:col-span-4"
        }
        span = span_classes.get(w.layout_span, "col-span-1 md:col-span-4")
        
        if w.widget_type == "KPICard":
            return f"""        
        <div key="{w.widget_id}" className="{span} bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">{w.title}</h3>
            <Activity className="w-4 h-4 text-blue-500" />
          </div>
          <div className="mt-4 flex items-baseline text-3xl font-semibold">
            {{ {var_name} !== null ? (Array.isArray({var_name}) ? {var_name}.length : {var_name}.count || 0) : <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" /> }}
          </div>
        </div>"""
            
        if w.widget_type == "DataGrid":
            headers = [f"<th>{f}</th>" for f in w.bound_entity.display_fields] if w.bound_entity else ["<th>ID</th>"]
            cells = [f"<td>{{item.{f}}}</td>" for f in w.bound_entity.display_fields] if w.bound_entity else ["<td>{{item.id}}</td>"]
            
            return f"""        
        <div key="{w.widget_id}" className="{span} bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <h3 className="text-lg font-semibold">{w.title}</h3>
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors">
              <Plus className="w-4 h-4" /> Add Record
            </button>
          </div>
          <div className="overflow-x-auto">
            {{!{var_name} ? (
              <div className="p-6"><TableSkeleton columns={{4}} rows={{5}} /></div>
            ) : (
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-500 uppercase bg-gray-50 dark:bg-gray-700/50 dark:text-gray-400">
                  <tr>
                    {' '.join(headers)}
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {{Array.isArray({var_name}) ? {var_name}.slice(0, 10).map((item: any, i: number) => (
                    <tr key={{i}} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      {' '.join(cells)}
                      <td className="p-4 text-right flex justify-end gap-2">
                        <button className="p-1 text-gray-500 hover:text-blue-600"><Eye className="w-4 h-4" /></button>
                        <button className="p-1 text-gray-500 hover:text-red-600"><Trash className="w-4 h-4" /></button>
                      </td>
                    </tr>
                  )) : (
                     <tr><td colSpan={{10}} className="p-4 text-center text-gray-500">Array expected but got {{typeof {var_name}}}</td></tr>
                  )}}
                </tbody>
              </table>
            )}}
          </div>
        </div>"""
        
        # Default fallback
        return f"""        <div className="{span} p-6 border border-dashed border-gray-300 rounded-xl text-center text-gray-500">
          [{w.widget_type}] {w.title} (Rendering pending...)
        </div>"""

    def _generate_error_fallback(self, error_msg: str) -> str:
        # Sanitize error message to prevent JSX injection
        safe_msg = (
            error_msg
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("{", "&#123;")
            .replace("}", "&#125;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )[:500]
        return f"""import React from 'react';
export default function ErrorFallback() {{
  return (
    <div className="p-8 max-w-2xl mx-auto mt-20 bg-red-50 dark:bg-red-900/20 text-red-600 rounded-lg border border-red-200">
      <h2 className="text-xl font-bold mb-4">AST Compilation Error</h2>
      <p className="text-sm font-mono whitespace-pre-wrap">{safe_msg}</p>
    </div>
  );
}}
"""
