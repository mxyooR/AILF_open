"""
Service package registry APIs.
"""
from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, Depends
from pathlib import Path
import time
import uuid

from app.core.auth import verify_developer_token
from app.core.response import UnifiedResponse
from app.services.service_registry import get_service_registry, PLUGIN_ROOT
from app.services import service_dispatcher as _builtin_services  # noqa: F401


router = APIRouter(prefix="/service-packages", tags=["Service Packages"])


@router.get("")
async def list_service_packages(_: dict = Depends(verify_developer_token)):
    registry = get_service_registry()
    return UnifiedResponse.success(
        message="Service packages fetched",
        data={"services": registry.list_services()},
    )


@router.post("/upload")
async def upload_service_package(
    file: UploadFile = File(...),
    auto_register: bool = True,
    _: dict = Depends(verify_developer_token),
):
    if not file.filename:
        raise UnifiedResponse.bad_request(message="Missing file")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".zip", ".py"}:
        raise UnifiedResponse.bad_request(
            message="Unsupported file type",
            details={"allowed": [".zip", ".py"]},
        )

    PLUGIN_ROOT.mkdir(parents=True, exist_ok=True)
    filename = f"{Path(file.filename).stem}_{int(time.time())}_{uuid.uuid4().hex[:8]}{suffix}"
    target_path = PLUGIN_ROOT / filename

    contents = await file.read()
    target_path.write_bytes(contents)

    registry = get_service_registry()
    if auto_register:
        info = registry.load_package(target_path)
        return UnifiedResponse.created(message="Service package uploaded", data=info)

    return UnifiedResponse.created(
        message="Service package uploaded",
        data={"file": str(target_path)},
    )
