"""
╔══════════════════════════════════════════════════════════════════╗
║        Job Shop Scheduler — API Blueprint Registry              ║
╠══════════════════════════════════════════════════════════════════╣
║  This module registers all Flask Blueprints on the app.         ║
║  It is imported once inside create_app() in app.py.             ║
║                                                                  ║
║  Blueprint map                                                   ║
║  ─────────────                                                   ║
║  /api/jobs            →  app.py  (inline routes)                ║
║  /api/machines        →  app.py  (inline routes)                ║
║  /api/operations      →  app.py  (inline routes)                ║
║  /api/schedule        →  app.py  (inline routes)                ║
║  /api/plannings       →  app.py  (inline routes)                ║
║  /api/kpis            →  app.py  (inline routes)                ║
║  /api/alerts          →  app.py  (inline routes)                ║
║  /api/contraintes     →  app.py  (inline routes)                ║
║  /api/import          →  app.py  (inline routes)                ║
║  /api/export/excel    →  app.py  (inline routes)                ║
║  /api/export/pdf      →  app.py  (inline routes)                ║
║  /api/whatif          →  app.py  (inline routes)                ║
║  /api/compare         →  app.py  (inline routes)                ║
║  /api/health          →  app.py  (inline routes)                ║
║  /api/reset           →  app.py  (inline routes)                ║
╚══════════════════════════════════════════════════════════════════╝

NOTE
────
All routes are defined directly in app.py using the Flask application
factory pattern (create_app).  This file exists as the *public* import
surface so that future refactoring can extract individual blueprints
here without touching app.py.

Usage in app.py
───────────────
    from api import register_blueprints
    register_blueprints(app)          # no-op for now; hook for future use
"""

from __future__ import annotations

import logging
from flask import Flask

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# BLUEPRINT REGISTRY (extensible)
# ══════════════════════════════════════════════════════════════════

def register_blueprints(app: Flask) -> None:
    """
    Register all API Blueprints on *app*.

    Currently all routes live in app.py (inline factory pattern).
    When a blueprint is extracted to its own module, add it here:

        from routes.jobs import jobs_bp
        app.register_blueprint(jobs_bp, url_prefix="/api/jobs")

    This function is called at the end of create_app() so the hook
    is always available without touching app.py.
    """
    # ── Placeholder — routes are registered inline in create_app() ─
    log.debug("register_blueprints() called — no external blueprints yet.")


# ══════════════════════════════════════════════════════════════════
# ROUTE SUMMARY (documentation only)
# ══════════════════════════════════════════════════════════════════

ROUTE_MAP: dict[str, list[str]] = {
    # Jobs
    "GET    /api/jobs"                  : ["List all jobs (paginated, filterable by statut)"],
    "POST   /api/jobs"                  : ["Create a new job"],
    "GET    /api/jobs/<id>"             : ["Get a single job with all operations"],
    "PUT    /api/jobs/<id>"             : ["Update a job"],
    "DELETE /api/jobs/<id>"             : ["Delete a job + cascade its operations"],

    # Machines
    "GET    /api/machines"              : ["List all machines"],
    "POST   /api/machines"             : ["Create a new machine"],
    "GET    /api/machines/<id>"         : ["Get a single machine"],
    "PUT    /api/machines/<id>"         : ["Update a machine"],
    "DELETE /api/machines/<id>"         : ["Delete a machine"],

    # Operations
    "GET    /api/operations"            : ["List all operations (filterable)"],
    "POST   /api/operations"            : ["Create a new operation"],
    "GET    /api/operations/<id>"       : ["Get a single operation"],
    "PUT    /api/operations/<id>"       : ["Update an operation"],
    "DELETE /api/operations/<id>"       : ["Delete an operation"],

    # Scheduling
    "POST   /api/schedule"             : ["Run scheduler (SPT/LPT/EDD/WSPT/GENETIC)"],
    "POST   /api/compare"              : ["Run all algorithms + compare KPIs"],

    # Plannings
    "GET    /api/plannings"             : ["List all planning history"],
    "GET    /api/plannings/<id>"        : ["Get a single planning with Gantt entries"],
    "DELETE /api/plannings/<id>"        : ["Delete a planning"],

    # KPIs
    "GET    /api/kpis"                  : ["Get all current KPIs"],

    # Alerts
    "GET    /api/alerts"               : ["List all unread alerts"],
    "GET    /api/alerts/all"           : ["List all alerts (read + unread)"],
    "GET    /api/alerts/summary"       : ["Get badge counts (unread/critical/warning)"],
    "POST   /api/alerts/<id>/read"     : ["Mark an alert as read"],
    "POST   /api/alerts/trigger"       : ["Manually trigger alert engine"],

    # Contraintes
    "GET    /api/contraintes"           : ["List all scheduling constraints"],
    "POST   /api/contraintes"          : ["Create a new constraint"],
    "PUT    /api/contraintes/<id>"      : ["Update a constraint"],
    "DELETE /api/contraintes/<id>"      : ["Delete a constraint"],

    # Import / Export
    "POST   /api/import"               : ["Import jobs from CSV file"],
    "GET    /api/export/excel"          : ["Export full data as Excel (.xlsx)"],
    "GET    /api/export/pdf"            : ["Export production report as PDF"],
    "GET    /api/export/csv"            : ["Export jobs as raw CSV"],

    # What-If
    "POST   /api/whatif"               : ["Run a what-if simulation (no DB write)"],

    # Utility
    "GET    /api/health"               : ["Health probe — returns {status: ok}"],
    "POST   /api/reset"                : ["Dev reset — drops + recreates all tables"],
}


def print_routes() -> None:
    """Pretty-print the full route map. Call from a Flask CLI command."""
    print("\n" + "─" * 66)
    print(f"  {'ROUTE':<42}  DESCRIPTION")
    print("─" * 66)
    for route, desc in ROUTE_MAP.items():
        print(f"  {route:<42}  {desc[0]}")
    print("─" * 66 + "\n")


__all__ = ["register_blueprints", "ROUTE_MAP", "print_routes"]
