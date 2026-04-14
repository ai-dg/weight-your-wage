import fastapi
from fastapi import FastAPI, BackgroundTasks
from fastapi import Request
from fastapi import HTTPException
import pandas as pd
from fastapi.responses import JSONResponse
import uuid
import datetime
import logging


logger = logging.getLogger("app_api")
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

	def _run_upload_minio_task(job_id: str):
		import sys
		sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None
		sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, "reconfigure") else None
		try:
			from srcs.services.minio.minio_file_uploader import run_csv_import_minio
			run_csv_import_minio()
			jobs[job_id]["status"] = "done"
			print("[upload minio file] Importation completed.", flush=True)
		except HTTPException as e:
			jobs[job_id]["status"] = "failed"
			jobs[job_id]["error"] = e.detail
			logger.error(f"Job {job_id} failed with HTTP error: {e.detail}")
		except Exception as e:
			jobs[job_id]["status"] = "failed"
			print(f"[upload minio file] Error: {e}", flush=True)
			logger.exception(f"Critical failure in background job {job_id}")
		finally:
			sys.stdout.flush()
			sys.stderr.flush()

	def _run_import_minio_postgresql_task(job_id: str):
		import sys
		sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None
		sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, "reconfigure") else None
		try:
			from srcs.services.postgresql.main_import import run_minio_import_postgresql
			run_minio_import_postgresql()
			jobs[job_id]["status"] = "done"
			print("[import postgresql] Importation completed.", flush=True)
		except HTTPException as e:
			jobs[job_id]["status"] = "failed"
			jobs[job_id]["error"] = e.detail
			logger.error(f"Job {job_id} failed with HTTP error: {e.detail}")
		except Exception as e:
			jobs[job_id]["status"] = "failed"
			print(f"[import postgresql] Error: {e}", flush=True)
			logger.exception(f"Critical failure in background job {job_id}")
		finally:
			sys.stdout.flush()
			sys.stderr.flush()

	def _run_clean_data_task(job_id: str):
		import sys
		sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None
		sys.stderr.reconfigure(line_uffering=True) if hasattr(sys.stderr, "reconfigure") else None
		try:
			from srcs.services.postgresql.clean_data import run_clean_data
			run_clean_data()
			jobs[job_id]["status"] = "done"
			print("[clean data] Data cleaned.", flush=True)
		except HTTPException as e:
			jobs[job_id]["status"] = "failed"
			jobs[job_id]["error"] = e.detail
			logger.error(f"Job {job_id} failed with HTTP error: {e.detail}")
		except Exception as e:
			jobs[job_id]["status"] = "failed"
			print(f"[clean data] Error: {e}", flush=True)
			logger.exception(f"Critical failure in background job {job_id}")
		finally:
			sys.stdout.flush()
			sys.stderr.flush()

	def _run_setup_metabase_task(job_id: str):
		import sys
		sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None
		sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, "reconfigure") else None
		try:
			from srcs.services.metabase.setup_metabase import run_setup_metabase
			run_setup_metabase()
			jobs[job_id]["status"] = "done"
			print("[setup metabase] Metabase set up.", flush=True)
		except HTTPException as e:
			jobs[job_id]["status"] = "failed"
			jobs[job_id]["error"] = e.detail
			logger.error(f"Job {job_id} failed with HTTP error: {e.detail}")
		except Exception as e:
			jobs[job_id]["status"] = "failed"
			print(f"[setup metabase] Error: {e}", flush=True)
			logger.exception(f"Critical failure in background job {job_id}")
		finally:
			sys.stdout.flush()
			sys.stderr.flush()

	def _run_data_visualization_metabase_task(job_id: str):
		import sys
		sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None
		sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, "reconfigure") else None
		try:
			from srcs.services.metabase.data_visualization_metabase import run_data_visualization_metabase
			run_data_visualization_metabase()
			jobs[job_id]["status"] = "done"
			print("[data visualization metabase] Metabase set up.", flush=True)
		except HTTPException as e:
			jobs[job_id]["status"] = "failed"
			jobs[job_id]["error"] = e.detail
			logger.error(f"Job {job_id} failed with HTTP error: {e.detail}")
		except Exception as e:
			jobs[job_id]["status"] = "failed"
			print(f"[data visualization metabase] Error: {e}", flush=True)
			logger.exception(f"Critical failure in background job {job_id}")
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

	@app.post("/jobs/upload_minio")
	def upload_minio(background_tasks: BackgroundTasks):
		job_id = str(uuid.uuid4())
		jobs[job_id] = {
			"task": "upload minio",
			"status": "pending",
			"created_at": str(datetime.datetime.now())
		}
		background_tasks.add_task(_run_upload_minio_task, job_id=job_id)
		return {
			"status": "uploading started",
			"job_id": job_id,
			"message": "Uploading is running in the background."
		}

	@app.post("/jobs/import_postgresql")
	def import_postgresql(background_tasks: BackgroundTasks):
		job_id = str(uuid.uuid4())
		jobs[job_id] = {
			"task": "import posgresql",
			"status": "pending",
			"created_at": str(datetime.datetime.now())
		}
		background_tasks.add_task(_run_import_minio_postgresql_task, job_id=job_id)
		return {
			"status": "importation started",
			"job_id": job_id,
			"message": "Importation is running in the background."
		}

	@app.post("/jobs/clean_data")
	def clean_data(background_tasks: BackgroundTasks):
		job_id = str(uuid.uuid4())
		jobs[job_id] = {
			"task": "clean_data",
			"status": "pending",
			"created_at": str(datetime.datetime.now())
		}
		background_tasks.add_task(_run_clean_data_task, job_id=job_id)
		return {
			"status": "uploading started",
			"job_id": job_id,
			"message": "Cleaning data is running in the background."
		}

	@app.post("/jobs/setup_metabase")
	def setup_metabase(background_tasks: BackgroundTasks):
		job_id = str(uuid.uuid4())
		jobs[job_id] = {
			"task": "setup metabase",
			"status": "pending",
			"created_at": str(datetime.datetime.now())
		}
		background_tasks.add_task(_run_setup_metabase_task, job_id=job_id)
		return {
			"status": "setup started",
			"job_id": job_id,
			"message": "Setup is running in the background."
		}

	@app.post("/jobs/data_visualization")
	def data_visualization(background_tasks: BackgroundTasks):
		job_id = str(uuid.uuid4())
		jobs[job_id] = {
			"task": "data visualization",
			"status": "pending",
			"created_at": str(datetime.datetime.now())
		}
		background_tasks.add_task(_run_data_visualization_metabase_task, job_id=job_id)
		return {
			"status": "daata visualization started",
			"job_id": job_id,
			"message": "Data visualization is running in the background."
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
