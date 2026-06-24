from fastapi import APIRouter

router = APIRouter(tags=["General"])


@router.get("/")
def read_root():
    return {"message": "Hello World"}