"""ToGrill main module"""

from bleak.uuids import register_uuids

from .const import MainService
from .parse import Service

register_uuids(
    {service.uuid: f"ToGrill {service.__name__}" for service in Service.registry.values()}
)

register_uuids(
    {
        char.uuid: f"ToGrill {service.__name__} {char.name}"
        for service in Service.registry.values()
        for char in service.characteristics()
    }
)

__all__ = (  # noqa: F405
    MainService
)
