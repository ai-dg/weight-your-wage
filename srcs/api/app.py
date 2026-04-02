import fastapi
from fastapi import FastAPI, BackgroundTasks
from fastapi import Request
import pandas as pd
from model.paths import datasets_file, model_file
from fastapi.responses import JSONResponse
import uuid
import datetime


jobs = {}


def main():
	app = FastAPI()
	app.include_router(fastapi.APIRouter())
	app.get("/")(lambda: {"message": "Hello World"})

	def _run_test(job_id: str):
		pass

	def _run_training(job_id: str):
		import sys
		import logging
		sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None
		sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, "reconfigure") else None
		logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)
		for name in ("lightning", "pytorch_lightning", "model"):
			logging.getLogger(name).setLevel(logging.INFO)
			for h in logging.getLogger(name).handlers:
				h.setStream(sys.stdout)
		print("[train] Starting training...", flush=True)
		try:
			from srcs.model.train import GeneralTrainer
			GeneralTrainer()
			jobs[job_id]["status"] = "done"
			print("[train] Training completed.", flush=True)
		except Exception as e:
			jobs[job_id]["status"] = "failed"
			print(f"[train] Error: {e}", flush=True)
			import traceback
			traceback.print_exc()
		finally:
			sys.stdout.flush()
			sys.stderr.flush()

	def _run_inference(job_id: str):
		import sys
		sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None
		sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, "reconfigure") else None
		try:
			from srcs.model.predict import GeneralInferencer
			salary = GeneralInferencer(datasets_file("inference.csv"))
			jobs[job_id]["status"] = "done"
			jobs[job_id]["salary"] = salary
			print("[predict] Inference completed.", flush=True)
		except Exception as e:
			jobs[job_id]["status"] = "failed"
			print(f"[predict] Error: {e}", flush=True)
			import traceback
			traceback.print_exc()
		finally:
			sys.stdout.flush()
			sys.stderr.flush()
		

	@app.post("/jobs/train")
	def train(background_tasks: BackgroundTasks):
		job_id = str(uuid.uuid4())
		jobs[job_id] = {
			"task": "train",
			"status": "pending",
			"created_at": str(datetime.datetime.now())
		}
		background_tasks.add_task(_run_training, job_id=job_id)
		return {
			"status": "training started",
			"job_id": job_id,
			"message": "Training is running in the background."
		}

	@app.post("/jobs/test")
	def test(background_tasks: BackgroundTasks):
		job_id = str(uuid.uuid4())
		jobs[job_id] = {
			"task": "train",
			"status": "pending",
			"created_at": str(datetime.datetime.now())
		}
		background_tasks.add_task(_run_test, job_id=job_id)
		return {
			"status": "test started",
			"job_id": job_id,
			"message": "Test is running in the background."
		}

	@app.post("/jobs/predict")
	def predict(background_tasks: BackgroundTasks):
		job_id = str(uuid.uuid4())
		jobs[job_id] = {
			"task": "predict",
			"status": "pending",
			"created_at": str(datetime.datetime.now())
		}
		background_tasks.add_task(_run_inference, job_id=job_id)
		return {
			"status": "inference started",
			"job_id": job_id,
			"message": "Inference is running in the background."
		}

	@app.get("/jobs/{job_id}")
	def get_job(job_id: str):
		if not job_id in jobs:
			return JSONResponse(
				status_code=404,
				content={
					"error": "Job not found",
					"job_id": job_id,
					"status_code": 404
				}
			)
		return jobs[job_id]
	

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
		df = pd.DataFrame([body])
		df.to_csv(model_file("inference.csv"))
		return {
			"message": "prediction started",
			"received": body,
		}


	return app


app = main()
