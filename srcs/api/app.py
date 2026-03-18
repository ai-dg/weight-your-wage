import fastapi
from fastapi import FastAPI


def main():
	app = FastAPI()
	app.include_router(fastapi.APIRouter())
	app.get("/")(lambda: {"message": "Hello World"})

	# Import lourd uniquement pour /train
	@app.post("/train")
	def train():
		from model.train import GeneralTrainer
		return GeneralTrainer()

	return app


app = main()
