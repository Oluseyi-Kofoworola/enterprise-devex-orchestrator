from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Any
import json
from src.orchestrator.intent_schema import IntentSpec

class UIUXProMaxPromptEngine:
    """AST-based Design intelligence engine."""
    
    @staticmethod
    def construct_design_prompt(spec: IntentSpec, target_component: str = "Dashboard") -> str:
        entities = [e.name for e in spec.entities]
        functional_summary = spec.functional_summary or "Standard business operations"
        domain = spec.domain_type.value if hasattr(spec.domain_type, 'value') else str(spec.domain_type)
        
        # Build API context for actual functionality
        api_context = ""
        if spec.entities:
            api_context += "Available REST Endpoints:\\n"
            for entity in spec.entities:
                fields_str = ", ".join(f.name for f in entity.fields[:5])
                api_context += f"- /api/v1/{entity.name} (Fields: {fields_str}...)\\n"

        prompt = f"""You are an elite Frontend Architect AI. 
Instead of writing React code, your job is to output a strictly typed Abstract Syntax Tree (AST) in JSON format that my code generator will compile into functional React code.

### 1. Intent Context
- **Project**: {spec.project_name}
- **Domain**: {spec.description} ({domain})
- **Functional Summary**: {functional_summary}
- **Core Entities Data**: {", ".join(entities) if entities else "User, Settings"}

### 2. Available Endpoints
{api_context}

### 3. The Required AST JSON Schema
You MUST output ONLY valid JSON matching this structure:
{{
  "app_name": "string",
  "theme": "light|dark|system",
  "pages": [
    {{
      "page_name": "{target_component}",
      "layout_type": "BentoGrid|StandardSidebar|Minimal",
      "color_palette": ["#...", "#...", ...], /* 6 colors max */
      "widgets": [
        {{
          "widget_id": "unique-name",
          "widget_type": "DataGrid|KPICard|Sparkline|EntityForm|InteractiveList",
          "title": "Widget Title",
          "bound_entity": {{
             "entity_name": "EntityNameFromContext",
             "display_fields": ["field1", "field2"],
             "primary_key": "id"
          }},
          "actions": [
            {{
              "trigger": "onLoad|onClick|onSubmit",
              "api_endpoint": "/api/v1/EntityName",
              "method": "GET|POST|PUT|DELETE"
            }}
          ],
          "layout_span": "full|half|third|quarter"
        }}
      ]
    }}
  ]
}}

### 4. Constraints
- The response MUST be purely the JSON tree. No markdown formatting (\  \json), no reasoning strings, JUST the raw JSON.
- Create 1 main page for {target_component}.
- Include at least 4 widgets (e.g. 2 KPICards, 1 DataGrid, 1 InteractiveList).
- Bind every widget to the real entity names and endpoints shown above.
"""
        return prompt
