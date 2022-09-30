from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "This backend was written on FastAPI by Akim Malyschik"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
