import importlib
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_database_models_import_without_eager_db_engine():
    module = importlib.import_module("app.database.models")

    assert module.Base is not None
    assert hasattr(module, "Dispute")
