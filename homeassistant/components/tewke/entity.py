"""TewkeEntity base class."""

from collections.abc import Generator
from contextlib import contextmanager

from pytewke.error import (
    PyTewkeCoapError,
    PyTewkeInvalidRequestError,
    PyTewkeInvalidResponseError,
    PyTewkeInvalidWallDockError,
    PyTewkeUnknownError,
)

from homeassistant.const import CONF_NAME
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TewkeCoordinator


@contextmanager
def tewke_error_handler(action: str, identifier: str) -> Generator[None]:
    """Catch PyTewke errors and raise HomeAssistantError."""
    try:
        yield
    except PyTewkeInvalidWallDockError as e:
        msg = f"Attempted to set {identifier.capitalize()} while not connected to Wall Dock"
        raise HomeAssistantError(msg) from e
    except (PyTewkeInvalidRequestError, RuntimeError) as e:
        msg = f"Internal error {action} Tewke {identifier}: {e}"
        raise HomeAssistantError(msg) from e
    except (
        PyTewkeCoapError,
        PyTewkeInvalidResponseError,
        PyTewkeUnknownError,
        TimeoutError,
    ) as e:
        msg = f"Error {action} Tewke {identifier}: {e}"
        raise HomeAssistantError(msg) from e


class TewkeEntity(CoordinatorEntity[TewkeCoordinator]):
    """Base class for Tewke entities.

    Each subclass represents a single scene or target output exposed as a HA
    platform entity (switch, light, fan). State is fetched via the shared
    coordinator.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: TewkeCoordinator) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        tap = entry.runtime_data.tap
        wall_dock_id = tap.wall_dock_id

        assert wall_dock_id is not None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, wall_dock_id)},
            name=entry.data.get(CONF_NAME, "Tewke"),
            manufacturer="Tewke",
            model="Tap",
            sw_version=tap.tewke_os_version,
            suggested_area=entry.data.get("room_name"),
        )
