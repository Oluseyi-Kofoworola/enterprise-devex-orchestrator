"""AI Agent -- entity-driven tool-calling agent.

Dynamically provides tools for: Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, AuditLog
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

from core.dependencies import get_repository

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

    Entities: Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, AuditLog
    Each entity gets list, get, search, and count tools.
    """

    @kernel_function(name="list_incidents", description="List all incidents in the system")
    def list_incidents(self) -> str:
        """List all incidents with their details."""
        repo = get_repository("incident")
        items = repo.list_all()
        if not items:
            return "No incidents found."
        return json.dumps(items[:20], indent=2, default=str)

    @kernel_function(name="get_incident", description="Get a specific incident by ID")
    def get_incident(self, entity_id: str) -> str:
        """Get details of a specific incident."""
        repo = get_repository("incident")
        item = repo.get(entity_id)
        if not item:
            return f"No incident found with ID {entity_id}"
        return json.dumps(item, indent=2, default=str)

    @kernel_function(name="search_incidents", description="Search incidents by keyword")
    def search_incidents(self, query: str) -> str:
        """Search incidents by matching any field value."""
        repo = get_repository("incident")
        items = repo.list_all()
        q = query.lower()
        matches = [i for i in items if q in json.dumps(i, default=str).lower()]
        if not matches:
            return f"No incidents matching '{query}'"
        return json.dumps(matches[:10], indent=2, default=str)

    @kernel_function(name="count_incidents", description="Count incidents by status")
    def count_incidents(self) -> str:
        """Count incidents grouped by status."""
        repo = get_repository("incident")
        items = repo.list_all()
        counts: dict[str, int] = {}
        for item in items:
            status = item.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return json.dumps({"total": len(items), "by_status": counts})

    @kernel_function(name="list_assets", description="List all assets in the system")
    def list_assets(self) -> str:
        """List all assets with their details."""
        repo = get_repository("asset")
        items = repo.list_all()
        if not items:
            return "No assets found."
        return json.dumps(items[:20], indent=2, default=str)

    @kernel_function(name="get_asset", description="Get a specific asset by ID")
    def get_asset(self, entity_id: str) -> str:
        """Get details of a specific asset."""
        repo = get_repository("asset")
        item = repo.get(entity_id)
        if not item:
            return f"No asset found with ID {entity_id}"
        return json.dumps(item, indent=2, default=str)

    @kernel_function(name="search_assets", description="Search assets by keyword")
    def search_assets(self, query: str) -> str:
        """Search assets by matching any field value."""
        repo = get_repository("asset")
        items = repo.list_all()
        q = query.lower()
        matches = [i for i in items if q in json.dumps(i, default=str).lower()]
        if not matches:
            return f"No assets matching '{query}'"
        return json.dumps(matches[:10], indent=2, default=str)

    @kernel_function(name="count_assets", description="Count assets by status")
    def count_assets(self) -> str:
        """Count assets grouped by status."""
        repo = get_repository("asset")
        items = repo.list_all()
        counts: dict[str, int] = {}
        for item in items:
            status = item.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return json.dumps({"total": len(items), "by_status": counts})

    @kernel_function(name="list_sensors", description="List all sensors in the system")
    def list_sensors(self) -> str:
        """List all sensors with their details."""
        repo = get_repository("sensor")
        items = repo.list_all()
        if not items:
            return "No sensors found."
        return json.dumps(items[:20], indent=2, default=str)

    @kernel_function(name="get_sensor", description="Get a specific sensor by ID")
    def get_sensor(self, entity_id: str) -> str:
        """Get details of a specific sensor."""
        repo = get_repository("sensor")
        item = repo.get(entity_id)
        if not item:
            return f"No sensor found with ID {entity_id}"
        return json.dumps(item, indent=2, default=str)

    @kernel_function(name="search_sensors", description="Search sensors by keyword")
    def search_sensors(self, query: str) -> str:
        """Search sensors by matching any field value."""
        repo = get_repository("sensor")
        items = repo.list_all()
        q = query.lower()
        matches = [i for i in items if q in json.dumps(i, default=str).lower()]
        if not matches:
            return f"No sensors matching '{query}'"
        return json.dumps(matches[:10], indent=2, default=str)

    @kernel_function(name="count_sensors", description="Count sensors by status")
    def count_sensors(self) -> str:
        """Count sensors grouped by status."""
        repo = get_repository("sensor")
        items = repo.list_all()
        counts: dict[str, int] = {}
        for item in items:
            status = item.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return json.dumps({"total": len(items), "by_status": counts})

    @kernel_function(name="list_service_requests", description="List all servicerequests in the system")
    def list_service_requests(self) -> str:
        """List all servicerequests with their details."""
        repo = get_repository("service_request")
        items = repo.list_all()
        if not items:
            return "No servicerequests found."
        return json.dumps(items[:20], indent=2, default=str)

    @kernel_function(name="get_service_request", description="Get a specific servicerequest by ID")
    def get_service_request(self, entity_id: str) -> str:
        """Get details of a specific servicerequest."""
        repo = get_repository("service_request")
        item = repo.get(entity_id)
        if not item:
            return f"No servicerequest found with ID {entity_id}"
        return json.dumps(item, indent=2, default=str)

    @kernel_function(name="search_service_requests", description="Search servicerequests by keyword")
    def search_service_requests(self, query: str) -> str:
        """Search servicerequests by matching any field value."""
        repo = get_repository("service_request")
        items = repo.list_all()
        q = query.lower()
        matches = [i for i in items if q in json.dumps(i, default=str).lower()]
        if not matches:
            return f"No servicerequests matching '{query}'"
        return json.dumps(matches[:10], indent=2, default=str)

    @kernel_function(name="count_service_requests", description="Count servicerequests by status")
    def count_service_requests(self) -> str:
        """Count servicerequests grouped by status."""
        repo = get_repository("service_request")
        items = repo.list_all()
        counts: dict[str, int] = {}
        for item in items:
            status = item.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return json.dumps({"total": len(items), "by_status": counts})

    @kernel_function(name="list_transit_routes", description="List all transitroutes in the system")
    def list_transit_routes(self) -> str:
        """List all transitroutes with their details."""
        repo = get_repository("transit_route")
        items = repo.list_all()
        if not items:
            return "No transitroutes found."
        return json.dumps(items[:20], indent=2, default=str)

    @kernel_function(name="get_transit_route", description="Get a specific transitroute by ID")
    def get_transit_route(self, entity_id: str) -> str:
        """Get details of a specific transitroute."""
        repo = get_repository("transit_route")
        item = repo.get(entity_id)
        if not item:
            return f"No transitroute found with ID {entity_id}"
        return json.dumps(item, indent=2, default=str)

    @kernel_function(name="search_transit_routes", description="Search transitroutes by keyword")
    def search_transit_routes(self, query: str) -> str:
        """Search transitroutes by matching any field value."""
        repo = get_repository("transit_route")
        items = repo.list_all()
        q = query.lower()
        matches = [i for i in items if q in json.dumps(i, default=str).lower()]
        if not matches:
            return f"No transitroutes matching '{query}'"
        return json.dumps(matches[:10], indent=2, default=str)

    @kernel_function(name="count_transit_routes", description="Count transitroutes by status")
    def count_transit_routes(self) -> str:
        """Count transitroutes grouped by status."""
        repo = get_repository("transit_route")
        items = repo.list_all()
        counts: dict[str, int] = {}
        for item in items:
            status = item.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return json.dumps({"total": len(items), "by_status": counts})

    @kernel_function(name="list_vehicles", description="List all vehicles in the system")
    def list_vehicles(self) -> str:
        """List all vehicles with their details."""
        repo = get_repository("vehicle")
        items = repo.list_all()
        if not items:
            return "No vehicles found."
        return json.dumps(items[:20], indent=2, default=str)

    @kernel_function(name="get_vehicle", description="Get a specific vehicle by ID")
    def get_vehicle(self, entity_id: str) -> str:
        """Get details of a specific vehicle."""
        repo = get_repository("vehicle")
        item = repo.get(entity_id)
        if not item:
            return f"No vehicle found with ID {entity_id}"
        return json.dumps(item, indent=2, default=str)

    @kernel_function(name="search_vehicles", description="Search vehicles by keyword")
    def search_vehicles(self, query: str) -> str:
        """Search vehicles by matching any field value."""
        repo = get_repository("vehicle")
        items = repo.list_all()
        q = query.lower()
        matches = [i for i in items if q in json.dumps(i, default=str).lower()]
        if not matches:
            return f"No vehicles matching '{query}'"
        return json.dumps(matches[:10], indent=2, default=str)

    @kernel_function(name="count_vehicles", description="Count vehicles by status")
    def count_vehicles(self) -> str:
        """Count vehicles grouped by status."""
        repo = get_repository("vehicle")
        items = repo.list_all()
        counts: dict[str, int] = {}
        for item in items:
            status = item.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return json.dumps({"total": len(items), "by_status": counts})

    @kernel_function(name="list_zones", description="List all zones in the system")
    def list_zones(self) -> str:
        """List all zones with their details."""
        repo = get_repository("zone")
        items = repo.list_all()
        if not items:
            return "No zones found."
        return json.dumps(items[:20], indent=2, default=str)

    @kernel_function(name="get_zone", description="Get a specific zone by ID")
    def get_zone(self, entity_id: str) -> str:
        """Get details of a specific zone."""
        repo = get_repository("zone")
        item = repo.get(entity_id)
        if not item:
            return f"No zone found with ID {entity_id}"
        return json.dumps(item, indent=2, default=str)

    @kernel_function(name="search_zones", description="Search zones by keyword")
    def search_zones(self, query: str) -> str:
        """Search zones by matching any field value."""
        repo = get_repository("zone")
        items = repo.list_all()
        q = query.lower()
        matches = [i for i in items if q in json.dumps(i, default=str).lower()]
        if not matches:
            return f"No zones matching '{query}'"
        return json.dumps(matches[:10], indent=2, default=str)

    @kernel_function(name="count_zones", description="Count zones by status")
    def count_zones(self) -> str:
        """Count zones grouped by status."""
        repo = get_repository("zone")
        items = repo.list_all()
        counts: dict[str, int] = {}
        for item in items:
            status = item.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return json.dumps({"total": len(items), "by_status": counts})

    @kernel_function(name="list_work_orders", description="List all workorders in the system")
    def list_work_orders(self) -> str:
        """List all workorders with their details."""
        repo = get_repository("work_order")
        items = repo.list_all()
        if not items:
            return "No workorders found."
        return json.dumps(items[:20], indent=2, default=str)

    @kernel_function(name="get_work_order", description="Get a specific workorder by ID")
    def get_work_order(self, entity_id: str) -> str:
        """Get details of a specific workorder."""
        repo = get_repository("work_order")
        item = repo.get(entity_id)
        if not item:
            return f"No workorder found with ID {entity_id}"
        return json.dumps(item, indent=2, default=str)

    @kernel_function(name="search_work_orders", description="Search workorders by keyword")
    def search_work_orders(self, query: str) -> str:
        """Search workorders by matching any field value."""
        repo = get_repository("work_order")
        items = repo.list_all()
        q = query.lower()
        matches = [i for i in items if q in json.dumps(i, default=str).lower()]
        if not matches:
            return f"No workorders matching '{query}'"
        return json.dumps(matches[:10], indent=2, default=str)

    @kernel_function(name="count_work_orders", description="Count workorders by status")
    def count_work_orders(self) -> str:
        """Count workorders grouped by status."""
        repo = get_repository("work_order")
        items = repo.list_all()
        counts: dict[str, int] = {}
        for item in items:
            status = item.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return json.dumps({"total": len(items), "by_status": counts})

    @kernel_function(name="list_audit_logs", description="List all auditlogs in the system")
    def list_audit_logs(self) -> str:
        """List all auditlogs with their details."""
        repo = get_repository("audit_log")
        items = repo.list_all()
        if not items:
            return "No auditlogs found."
        return json.dumps(items[:20], indent=2, default=str)

    @kernel_function(name="get_audit_log", description="Get a specific auditlog by ID")
    def get_audit_log(self, entity_id: str) -> str:
        """Get details of a specific auditlog."""
        repo = get_repository("audit_log")
        item = repo.get(entity_id)
        if not item:
            return f"No auditlog found with ID {entity_id}"
        return json.dumps(item, indent=2, default=str)

    @kernel_function(name="search_audit_logs", description="Search auditlogs by keyword")
    def search_audit_logs(self, query: str) -> str:
        """Search auditlogs by matching any field value."""
        repo = get_repository("audit_log")
        items = repo.list_all()
        q = query.lower()
        matches = [i for i in items if q in json.dumps(i, default=str).lower()]
        if not matches:
            return f"No auditlogs matching '{query}'"
        return json.dumps(matches[:10], indent=2, default=str)

    @kernel_function(name="count_audit_logs", description="Count auditlogs by status")
    def count_audit_logs(self) -> str:
        """Count auditlogs grouped by status."""
        repo = get_repository("audit_log")
        items = repo.list_all()
        counts: dict[str, int] = {}
        for item in items:
            status = item.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return json.dumps({"total": len(items), "by_status": counts})

    @kernel_function(name="get_system_summary", description="Get a summary of all data in the system")
    def get_system_summary(self) -> str:
        """Return a summary of all entities and their counts."""
        summary = {}
        entity_repos = [["Incident", "incident"], ["Asset", "asset"], ["Sensor", "sensor"], ["ServiceRequest", "service_request"], ["TransitRoute", "transit_route"], ["Vehicle", "vehicle"], ["Zone", "zone"], ["WorkOrder", "work_order"], ["AuditLog", "audit_log"]]
        for name, snake in entity_repos:
            try:
                from core import dependencies
                repo = getattr(dependencies, f"get_{snake}_repo")()
                items = repo.list_all()
                status_counts = {}
                for item in items:
                    s = item.get("status", "unknown")
                    status_counts[s] = status_counts.get(s, 0) + 1
                summary[name] = {"total": len(items), "by_status": status_counts}
            except Exception:
                summary[name] = {"total": 0, "error": "unavailable"}
        return json.dumps(summary, indent=2)


async def run_agent(user_message: str, history: list[dict] | None = None) -> str:
    """Run the AI agent with entity-aware tool-calling capabilities."""
    kernel = create_kernel()
    kernel.add_plugin(DomainTools(), plugin_name="domain")

    chat_history = ChatHistory()
    chat_history.add_system_message(
        "You are an AI agent for smart-city-ai-operations-platform-extre. "
        "You have access to tools that can query and analyze the application's data. "
        "Use these tools to answer questions accurately. "
        "Available entities: Incident, Asset, Sensor, ServiceRequest, TransitRoute, Vehicle, Zone, WorkOrder, AuditLog. "
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
        prompt="{{$chat_history}}",
        chat_history=chat_history,
        settings=settings,
    )

    return str(result)
