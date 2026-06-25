from fastapi import APIRouter


router = APIRouter(prefix="/models", tags=["models"])


@router.get("/registry")
def registry_placeholder() -> dict[str, str]:
    return {"status": "registry router ready"}

