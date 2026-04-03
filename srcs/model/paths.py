"""Chemins stables (ne dépendent pas du répertoire de travail du processus)."""
from pathlib import Path

MODEL_ROOT = Path(__file__).resolve().parent


def datasets_file(name: str) -> str:
	return str(MODEL_ROOT / "datasets" / name)


def model_file(name: str) -> str:
	"""Fichier à la racine du package model (ex. inference.csv)."""
	return str(MODEL_ROOT / name)
