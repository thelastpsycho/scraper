"""Smoke-check moved modules and the stable Flask API contract."""
import importlib

from app import create_app


def test_moved_modules_import():
    for module in [
        "app.integrations.pms.inventory_scraper",
        "app.integrations.pms.allotment_updater",
        "app.integrations.pms.other_room_allotment_updater",
        "app.integrations.dedge.inventory_scraper",
        "app.integrations.dedge.bar_updater",
        "app.inventory.pms_processor",
        "app.inventory.channel_manager_processor",
        "app.inventory.inventory_combiner",
        "app.revenue.yield_engine",
        "app.pipeline.runner",
    ]:
        assert importlib.import_module(module)


def test_api_routes_preserved():
    app = create_app()
    paths = {rule.rule for rule in app.url_map.iter_rules()}
    assert {"/api/scrape", "/api/scrape-cm", "/api/combine-inventory",
            "/api/custom-yield", "/api/update-allotment", "/api/update-bar",
            "/api/pipeline/start", "/api/pipeline/status", "/api/pipeline/stream",
            "/api/auth/login"}.issubset(paths)
