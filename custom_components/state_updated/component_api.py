"""Component api."""

from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ATTRIBUTE,
    CONF_ENTITY_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, TemplateError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity import get_unit_of_measurement
from homeassistant.helpers.template import Template
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CLEAR_UPDATES_AFTER_HOURS,
    CONF_LAST_UPDATED,
    CONF_NEW_VALUE,
    CONF_OLD_VALUE,
    CONF_TEXT_TEMPLATE,
    CONF_UPDATED,
    DOMAIN,
    DOMAIN_NAME,
    TRANSLATION_KEY_MISSING_ENTITY,
)


# ------------------------------------------------------------------
# ------------------------------------------------------------------
# @dataclass
class ComponentApi:
    """State updated interface."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Component api."""
        self.hass = hass
        self.entry: ConfigEntry = entry
        self.coordinator: DataUpdateCoordinator

        self.updated: bool = entry.options.get(CONF_UPDATED, False)
        self.last_updated: datetime = datetime.fromisoformat(
            entry.options.get(CONF_LAST_UPDATED, datetime.now(UTC).isoformat)
        )

        self.uom: str = self.get_uom()
        self.text: str = ""
        self.supress_update_listener: bool = False

        self.new_value: Any = entry.options.get(CONF_NEW_VALUE, "")
        self.old_value: Any = entry.options.get(CONF_OLD_VALUE, "")
        self.create_text_from_template()

    # ------------------------------------------------------------------
    async def async_reset(self) -> None:
        """Reset."""

        self.updated = False
        self.text = ""

        self.update_config()
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    def update_state(self, new_value: Any, old_value: Any) -> None:
        """Update state."""

        if old_value in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            if self.new_value not in ("", new_value):
                self.old_value = self.new_value
                self.new_value = new_value
            else:
                return

        else:
            self.new_value = new_value
            self.old_value = old_value

        if self.new_value != self.old_value:
            self.updated = True
            self.last_updated = datetime.now(UTC)
            self.create_text_from_template()

            self.update_config()

        self.uom = self.get_uom()

    # ------------------------------------------------------------------
    def update_config(self) -> None:
        """Update config."""

        tmp_options: dict[str, Any] = self.entry.options.copy()
        tmp_options[CONF_NEW_VALUE] = self.new_value
        tmp_options[CONF_OLD_VALUE] = self.old_value
        tmp_options[CONF_UPDATED] = self.updated
        tmp_options[CONF_LAST_UPDATED] = self.last_updated.isoformat()

        self.supress_update_listener = True

        self.hass.config_entries.async_update_entry(
            self.entry, data=tmp_options, options=tmp_options
        )

    # ------------------------------------------------------------------
    async def async_update(self) -> None:
        """Update."""

        if self.updated and (
            self.last_updated
            + timedelta(hours=self.entry.options[CONF_CLEAR_UPDATES_AFTER_HOURS])
        ) < datetime.now(UTC):
            self.updated = False
            self.text = ""

            self.update_config()
            await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def async_config_entry_refresh(self) -> None:
        """Config entry hass been updated."""
        await self.async_update()

    # ------------------------------------------------------------------
    def get_uom(self) -> str:
        """Get uom."""

        if self.entry.options.get(CONF_ENTITY_ID, "") != "":
            try:
                tmp_uom: str = get_unit_of_measurement(
                    self.hass,
                    self.entry.options.get(CONF_ENTITY_ID),
                )

                if tmp_uom is not None:
                    if tmp_uom == "%":
                        return tmp_uom

                    return " " + tmp_uom
            except HomeAssistantError:
                pass

        return ""

    # ------------------------------------------------------------------
    def create_text_from_template(self) -> None:
        """Create text from template."""

        if self.updated and self.entry.options.get(CONF_TEXT_TEMPLATE, ""):
            values: dict[str, Any] = {
                CONF_ENTITY_ID: self.entry.options.get(CONF_ENTITY_ID, ""),
                CONF_ATTRIBUTE: self.entry.options.get(CONF_ATTRIBUTE, ""),
                CONF_NEW_VALUE: self.new_value + self.uom,
                CONF_OLD_VALUE: self.old_value + self.uom,
                CONF_LAST_UPDATED: self.last_updated.isoformat(),
            }

            try:
                value_template: Template | None = Template(
                    str(self.entry.options.get(CONF_TEXT_TEMPLATE)), self.hass
                )

                self.text = value_template.async_render(values)
            except (TypeError, TemplateError) as e:
                self.create_issue_template(
                    str(e),
                    value_template.template,
                    TRANSLATION_KEY_MISSING_ENTITY,
                )

        else:
            self.text = ""

    # ------------------------------------------------------------------
    def create_issue_template(
        self,
        error_txt: str,
        template: str,
        translation_key: str,
    ) -> None:
        """Create issue on entity."""

        if (
            self.last_error_template != template
            or error_txt != self.last_error_txt_template
        ):
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                DOMAIN_NAME + datetime.now().isoformat(),
                issue_domain=DOMAIN,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=translation_key,
                translation_placeholders={
                    "error_txt": error_txt,
                    "template": template,
                },
            )
            self.last_error_template = template
            self.last_error_txt_template = error_txt
