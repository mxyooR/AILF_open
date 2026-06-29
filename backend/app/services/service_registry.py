"""
Service registry and plugin loader for custom_function handler.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


PLUGIN_ROOT = Path("uploads/service_packages")
PLUGIN_ROOT.mkdir(parents=True, exist_ok=True)


@dataclass
class ServiceMeta:
    name: str
    display_name: str
    origin: str
    version: Optional[str] = None
    description: Optional[str] = None
    package_path: Optional[str] = None
    methods: List[str] = field(default_factory=list)


class ServiceRegistry:
    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}
        self._meta: Dict[str, ServiceMeta] = {}

    def register(
        self,
        name: str,
        service: Any,
        *,
        display_name: Optional[str] = None,
        origin: str = "builtin",
        version: Optional[str] = None,
        description: Optional[str] = None,
        package_path: Optional[str] = None,
    ) -> None:
        display = display_name or name
        methods = self._introspect_methods(service)
        self._services[name] = service
        self._meta[name] = ServiceMeta(
            name=name,
            display_name=display,
            origin=origin,
            version=version,
            description=description,
            package_path=package_path,
            methods=methods,
        )

    def unregister(self, name: str) -> None:
        self._services.pop(name, None)
        self._meta.pop(name, None)

    def get(self, name: str) -> Optional[Any]:
        return self._services.get(name)

    def list_services(self) -> List[Dict[str, Any]]:
        services = []
        for meta in self._meta.values():
            services.append({
                "name": meta.name,
                "display_name": meta.display_name,
                "origin": meta.origin,
                "version": meta.version,
                "description": meta.description,
                "package_path": meta.package_path,
                "methods": meta.methods,
            })
        services.sort(key=lambda item: (item.get("origin", ""), item.get("name", "")))
        return services

    def refresh_methods(self, name: str) -> None:
        service = self._services.get(name)
        meta = self._meta.get(name)
        if service and meta:
            meta.methods = self._introspect_methods(service)

    def load_package(self, package_path: Path) -> Dict[str, Any]:
        package_dir = self._prepare_package_dir(package_path)
        manifest_path = package_dir / "service_manifest.json"
        if not manifest_path.exists():
            raise ValueError("service_manifest.json not found in package")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        service_name = manifest.get("service_name") or manifest.get("name")
        if not service_name:
            raise ValueError("manifest missing service_name")

        entrypoint = manifest.get("entrypoint", "service.py")
        module_path = (package_dir / entrypoint).resolve()
        if not module_path.exists():
            raise ValueError(f"entrypoint not found: {entrypoint}")

        module = self._load_module_from_path(module_path)
        service = self._resolve_service_from_module(module, manifest)
        display_name = manifest.get("display_name") or service_name
        version = manifest.get("version")
        description = manifest.get("description")

        self.register(
            service_name,
            service,
            display_name=display_name,
            origin="plugin",
            version=version,
            description=description,
            package_path=str(package_dir),
        )
        return {
            "service_name": service_name,
            "display_name": display_name,
            "version": version,
            "description": description,
            "package_path": str(package_dir),
        }

    def _prepare_package_dir(self, package_path: Path) -> Path:
        timestamp = int(time.time())
        unique_id = uuid.uuid4().hex[:8]
        target_dir = PLUGIN_ROOT / f"{package_path.stem}_{timestamp}_{unique_id}"
        target_dir.mkdir(parents=True, exist_ok=True)

        if package_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(package_path, "r") as zf:
                zf.extractall(target_dir)
        else:
            # Treat as single python file package
            target_file = target_dir / package_path.name
            target_file.write_bytes(package_path.read_bytes())
        return target_dir

    def _load_module_from_path(self, module_path: Path):
        module_name = f"service_pkg_{module_path.stem}_{uuid.uuid4().hex[:8]}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Failed to load module: {module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _resolve_service_from_module(self, module: Any, manifest: Dict[str, Any]) -> Any:
        class_name = manifest.get("class_name")
        factory = manifest.get("factory")
        if class_name:
            cls = getattr(module, class_name, None)
            if not cls:
                raise ValueError(f"class not found: {class_name}")
            return cls()
        if factory:
            fn = getattr(module, factory, None)
            if not callable(fn):
                raise ValueError(f"factory not found: {factory}")
            return fn()
        if hasattr(module, "get_service") and callable(getattr(module, "get_service")):
            return module.get_service()
        if hasattr(module, "Service"):
            cls = getattr(module, "Service")
            if callable(cls):
                return cls()
        if hasattr(module, "service"):
            return getattr(module, "service")
        raise ValueError("No service entrypoint found")

    def _introspect_methods(self, service: Any) -> List[str]:
        methods: List[str] = []
        for name in dir(service):
            if name.startswith("_"):
                continue
            value = getattr(service, name)
            if callable(value):
                methods.append(name)
        methods.sort()
        return methods


service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    return service_registry
