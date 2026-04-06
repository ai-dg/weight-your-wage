import fastapi
from fastapi import FastAPI, BackgroundTasks
from fastapi import Request
import pandas as pd
from fastapi.responses import JSONResponse
import uuid
import datetime
from loguru import logger
import json


jobs = {}


def main():
	app = FastAPI()
	app.include_router(fastapi.APIRouter())
	app.get("/")(lambda: {"message": "Hello World"})

	def _run_test(job_id: str, version:str | None):
		import sys
		import logging
		sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None
		sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, "reconfigure") else None
		logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)
		for name in ("lightning", "pytorch_lightning", "model"):
			logging.getLogger(name).setLevel(logging.INFO)
			for h in logging.getLogger(name).handlers:
				h.setStream(sys.stdout)
		print("[test] Starting testing...")
		try:
			from srcs.model.test import GeneralTester
			GeneralTester(version=version)
			jobs[job_id]["status"] = "done"
			print("[test] Testing completed.")
		except Exception as e:
			jobs[job_id]["status"] = "failed"
			print(f"[test] Error: {e}")
			import traceback
			traceback.print_exc()

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

	def _run_inference(job_id: str, data: dict | None):
		try:
			from srcs.model.predict import GeneralInferencer
			salary = GeneralInferencer(data)
			jobs[job_id]["status"] = "done"
			jobs[job_id]["salary"] = salary
			print("[predict] Inference completed.", flush=True)
		except Exception as e:
			jobs[job_id]["status"] = "failed"
			print(f"[predict] Error: {e}", flush=True)
			import traceback
			traceback.print_exc()

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

	@app.post("/jobs/test/")
	@app.post("/jobs/test/{version}")
	def test(background_tasks: BackgroundTasks, version: str | None=None):
		job_id = str(uuid.uuid4())
		jobs[job_id] = {
			"task": "test",
			"status": "pending",
			"created_at": str(datetime.datetime.now())
		}
		background_tasks.add_task(_run_test, version=version,job_id=job_id)
		return {
			"status": "test started",
			"job_id": job_id,
			"message": "Test is running in the background."
		}

	@app.post("/jobs/predict")
	async def predict(background_tasks: BackgroundTasks, request: Request):
		try:
			data = await request.json()
		except JSONDecodeError:
			return JSONResponse(
				status_code=400,
				content={
					"error": "Bad JSOn formnatting",
					"status_code": 400
				}
			)

		job_id = str(uuid.uuid4())
		jobs[job_id] = {
			"task": "predict",
			"status": "pending",
			"created_at": str(datetime.datetime.now())
		}
		background_tasks.add_task(_run_inference, data=data, job_id=job_id)
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
		
		return {
			"message": "prediction started",
			"received": body,
		}

	
	return app


app = main()
