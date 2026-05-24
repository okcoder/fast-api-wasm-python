from pydantic import BaseModel
from fastapi import FastAPI

from app.native_wasm_checker import check_email_native_wasm

app = FastAPI(title="fast-api-wasm-python")


class CheckRequest(BaseModel):
    email: str
    code: str


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello from FastAPI in devcontainer"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/domains")
def read_domains() -> list[str]:
    return ["a.com", "b.com", "c.com"]


@app.post("/check")
def check_email(request: CheckRequest) -> dict[str, str]:
    return {"result": check_email_native_wasm(request.email, request.code).result}
