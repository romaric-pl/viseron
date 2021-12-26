"""Base MQTT Home Assistant entity."""
from __future__ import annotations

import json
from abc import ABC

from viseron import Viseron
from viseron.components.mqtt.const import (
    COMPONENT as MQTT_COMPONENT,
    CONFIG_CLIENT_ID,
    CONFIG_DISCOVERY_PREFIX,
    CONFIG_HOME_ASSISTANT,
    CONFIG_LAST_WILL_TOPIC,
    CONFIG_RETAIN_CONFIG,
    MQTT_CLIENT_CONNECTION_OFFLINE,
    MQTT_CLIENT_CONNECTION_ONLINE,
    MQTT_CLIENT_CONNECTION_TOPIC,
)
from viseron.components.mqtt.helpers import PublishPayload
from viseron.helpers.entity import Entity


class HassMQTTEntity(ABC):
    """Base class for all Home Assistant MQTT entities."""

    domain: str = NotImplemented

    def __init__(self, vis: Viseron, config, entity: Entity):
        self._vis = vis
        self._config = config
        self._entity = entity

        self._mqtt = vis.data[MQTT_COMPONENT]

    @property
    def availability(self):
        """Return availability."""
        if self._entity.availability:
            return self._entity.availability

        return [
            {
                "topic": self._config[CONFIG_LAST_WILL_TOPIC],
                "payload_available": "alive",
                "payload_not_available": "dead",
            },
            {
                "topic": MQTT_CLIENT_CONNECTION_TOPIC.format(
                    client_id=self._config[CONFIG_CLIENT_ID]
                ),
                "payload_available": MQTT_CLIENT_CONNECTION_ONLINE,
                "payload_not_available": MQTT_CLIENT_CONNECTION_OFFLINE,
            },
        ]

    @property
    def device_name(self):
        """Return device name."""
        return self._entity.device_name

    @property
    def device_identifiers(self):
        """Return device identifiers."""
        return self._entity.device_identifiers

    @property
    def device(self):
        """Return device."""
        device = {}
        if self.device_identifiers:
            device["identifiers"] = self.device_identifiers
        if self.device_name:
            device["name"] = self.device_name
        device["manufacturer"] = "Viseron"
        return device

    @property
    def enabled_by_default(self):
        """Return if entity is enabled by default."""
        return self._entity.enabled_by_default

    @property
    def entity_category(self):
        """Return the category of the entity."""
        return self._entity.entity_category

    @property
    def name(self):
        """Return name."""
        return self._entity.name

    @property
    def unique_id(self):
        """Return unique ID."""
        return self._entity.entity_id

    @property
    def object_id(self):
        """Return unique ID."""
        return self._entity.object_id

    @property
    def state_topic(self):
        """Return state topic."""
        return f"{self._config[CONFIG_CLIENT_ID]}/{self.domain}/{self.object_id}/state"

    @property
    def config_topic(self):
        """Return config topic."""
        return (
            f"{self._config[CONFIG_HOME_ASSISTANT][CONFIG_DISCOVERY_PREFIX]}/"
            f"{self.domain}/{self.object_id}/config"
        )

    @property
    def config_payload(self):
        """Return config payload."""
        payload = {}
        payload["availability"] = self.availability
        payload["enabled_by_default"] = self.enabled_by_default
        payload["name"] = self.name
        payload["object_id"] = self.object_id  # last part of Home Assistant entity_id
        payload["unique_id"] = self.unique_id
        payload["state_topic"] = self.state_topic
        payload["value_template"] = "{{ value_json.state }}"
        payload["json_attributes_topic"] = self.state_topic
        payload["json_attributes_template"] = "{{ value_json.attributes | tojson }}"

        if self.entity_category:
            payload["entity_category"] = self.entity_category

        if self.device_name and self.device_identifiers:
            payload["device"] = self.device

        return payload

    def create(self):
        """Create config in Home Assistant."""
        self._mqtt.publish(
            PublishPayload(
                self.config_topic,
                json.dumps(self.config_payload),
                retain=self._config[CONFIG_HOME_ASSISTANT][CONFIG_RETAIN_CONFIG],
            )
        )

        payload = {}
        payload["state"] = self._entity.state
        payload["attributes"] = self._entity.attributes
        self._mqtt.publish(
            PublishPayload(
                self.state_topic,
                json.dumps(payload),
                retain=True,
            )
        )
