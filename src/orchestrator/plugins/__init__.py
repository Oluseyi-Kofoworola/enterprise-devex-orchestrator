"""Plugin system for extending the Enterprise DevEx Orchestrator.

Seven plugin categories allow organizations to inject custom behaviour
into the scaffold generation pipeline without modifying core generators:

    - ResourcePlugin:    Custom Azure resource types (Service Bus, Event Grid, etc.)
    - RoutePlugin:       Custom API endpoint patterns and middleware
    - DashboardPlugin:   Domain-specific React dashboard components
    - CICDPlugin:        Additional CI/CD stages (load testing, canary, etc.)
    - GovernancePlugin:  Organization-specific compliance rules
    - SecurityPlugin:    WAF rules, DDoS controls, network policies
    - DocsPlugin:        Custom documentation sections or formats

Usage::

    from src.orchestrator.plugins import PluginRegistry, create_default_plugins

    registry = create_default_plugins()
    registry.load_from_yaml("plugins.yaml")   # optional external config
    bicep_files = registry.resource.generate_all(spec)
"""

from src.orchestrator.plugins.registry import PluginRegistry, create_default_plugins

__all__ = ["PluginRegistry", "create_default_plugins"]
