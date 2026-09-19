from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_vercel_entrypoint_exists_and_exposes_flask_app():
    source = (ROOT / "api" / "index.py").read_text(encoding="utf-8")
    assert "from wsgi import app" in source
    assert '__all__ = ["app"]' in source


def test_vercel_config_targets_python_entrypoint():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert config["builds"][0]["src"] == "api/index.py"
    assert config["builds"][0]["use"] == "@vercel/python"
    assert config["routes"][0]["dest"] == "api/index.py"
