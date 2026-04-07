from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Any

class UIAction(BaseModel):
    trigger: Literal["onClick", "onSubmit", "onLoad"] = "onClick"
    api_endpoint: str = Field(description="The relative API path, e.g. /api/v1/customers")
    method: Literal["GET", "POST", "PUT", "DELETE"] = "GET"
    payload_mapping: Optional[dict[str, str]] = Field(default=None, description="Maps state fields to API payload keys")

class UIEntityBinding(BaseModel):
    entity_name: str = Field(description="The canonical name of the backend entity, e.g. Customer")
    display_fields: List[str] = Field(description="The fields to display in a summary view or table")
    primary_key: str = "id"

class UIWidget(BaseModel):
    widget_id: str = Field(description="Unique identifier for this widget instance")
    widget_type: Literal["DataGrid", "KPICard", "Sparkline", "EntityForm", "InteractiveList", "Chart"]
    title: str
    bound_entity: Optional[UIEntityBinding] = None
    actions: List[UIAction] = []
    layout_span: Literal["full", "half", "third", "quarter"] = "full"
    
class UIPageSpec(BaseModel):
    page_name: str
    layout_type: Literal["BentoGrid", "StandardSidebar", "Minimal", "SplitPane"]
    color_palette: List[str] = Field(description="Array of 6 hex colors")
    widgets: List[UIWidget]
    
class UIAppSpec(BaseModel):
    app_name: str
    theme: Literal["light", "dark", "system"] = "system"
    pages: List[UIPageSpec]
