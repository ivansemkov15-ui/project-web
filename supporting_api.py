import hashlib

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Phonebook Supporting Service")


class GroupCount(BaseModel):
    name: str
    count: int


class Statistics(BaseModel):
    total_contacts: int
    groups: list[GroupCount]
    without_group: int


@app.get("/health")
def health():
    return {"status": "ok", "service": "supporting"}


@app.get("/api/hash/{value}")
def hash_string(value: str):
    result = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return {"request": value, "result": result}


@app.post("/api/summary")
def summary(data: Statistics):
    return {
        "total_contacts": data.total_contacts,
        "groups": [group.model_dump() for group in data.groups],
        "without_group": data.without_group,
        "groups_count": len(data.groups),
    }
