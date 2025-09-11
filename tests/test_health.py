import os
import sys
import pathlib

os.environ.setdefault("NARAMARKET_SERVICE_KEY", "DUMMY")

# Add parent directory (where server.py resides) to path for import regardless of pytest CWD
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import server  # type: ignore  # noqa: E402


def test_health_structure():
    # Access underlying function via .fn (FastMCP wrapper provides .fn attribute)
    fn = getattr(server.healthcheck, "fn", None)
    assert fn is not None, "healthcheck tool missing underlying function"
    hc = fn()
    assert isinstance(hc, dict)
    assert "time" in hc
    assert "env" in hc
    assert "list_ping" in hc
