import fastapi
# from model import SalaryModel

from fastapi import FastAPI


def test():

	message = "Hello"

	numero = 100


	return { numero : message }


def main():
	app = FastAPI()

	app.include_router(fastapi.APIRouter())
	app.get("/")(lambda: {"message": "Hello World"})
	app.post("/predict")(lambda: test())

	return app


app = main()
