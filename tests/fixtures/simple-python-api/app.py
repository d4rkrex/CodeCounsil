# Simple FastAPI app for testing
from fastapi import FastAPI
from sqlalchemy import create_engine

app = FastAPI()
engine = create_engine("sqlite:///./test.db")


@app.get("/users/{user_id}")
def get_user(user_id: int):
    # Missing authorization check
    return {"user_id": user_id}
