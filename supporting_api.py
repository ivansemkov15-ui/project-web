import hashlib

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel


app = FastAPI(title="Phonebook Supporting Service")
router = APIRouter()


class GroupCount(BaseModel):
    name: str
    count: int


class Statistics(BaseModel):
    total_contacts: int
    groups: list[GroupCount]
    without_group: int


@router.get("/health")
def health():
    return {"status": "ok", "service": "supporting"}


@router.get("/api/hash/{value:path}")
def hash_string(value: str):
    result = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return {"request": value, "result": result}


@router.post("/api/summary")
def summary(data: Statistics):
    return {
        "total_contacts": data.total_contacts,
        "groups": [group.model_dump() for group in data.groups],
        "without_group": data.without_group,
        "groups_count": len(data.groups),
    }


app.include_router(router)
