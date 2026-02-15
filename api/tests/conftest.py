"""Configuration pytest et fixtures partagées."""
import os
import sys
from pathlib import Path

# Permettre l'import du package app depuis la racine api/
_api_root = Path(__file__).resolve().parent.parent
if str(_api_root) not in sys.path:
    sys.path.insert(0, str(_api_root))

# Éviter de charger un .env qui pourrait surcharger les tests
os.environ.setdefault("OPENAI_API_KEY", "")
