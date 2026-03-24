import fastapi
from fastapi import FastAPI, BackgroundTasks
from fastapi import Request


def main():
	app = FastAPI()
	app.include_router(fastapi.APIRouter())
	app.get("/")(lambda: {"message": "Hello World"})

	def _run_training():
		import sys
		import logging
		sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None
		sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, "reconfigure") else None
		logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)
		for name in ("lightning", "pytorch_lightning", "model"):
			logging.getLogger(name).setLevel(logging.INFO)
			for h in logging.getLogger(name).handlers:
				h.setStream(sys.stdout)
		print("[train] Démarrage de l'entraînement...", flush=True)
		try:
			from model.train import GeneralTrainer
			GeneralTrainer()
			print("[train] Entraînement terminé.", flush=True)
		except Exception as e:
			print(f"[train] Erreur: {e}", flush=True)
			import traceback
			traceback.print_exc()
		finally:
			sys.stdout.flush()
			sys.stderr.flush()

	@app.post("/train")
	def train(background_tasks: BackgroundTasks):
		background_tasks.add_task(_run_training)
		return {"status": "training started", "message": "L'entraînement tourne en arrière-plan."}

	@app.post("/predict")
	async def predict(request: Request):
		"""POST JSON aligné sur le formulaire / modèle. Ne renvoie pas l’objet Request (non JSON-serializable)."""
		body = None
		try:
			body = await request.json()
		except Exception as exc:
			print(f"[predict] corps JSON invalide ou vide: {exc}", flush=True)
		else:
			if isinstance(body, dict):
				print(f"[predict] reçu {len(body)} champs: {list(body.keys())}", flush=True)
			else:
				print(f"[predict] reçu type={type(body).__name__}", flush=True)
		return {
			"message": "prediction started",
			"received": body,
		}

	return app


app = main()
