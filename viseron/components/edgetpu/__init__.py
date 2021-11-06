"""EdgeTPU object detection."""
import logging
import re

import voluptuous as vol

from viseron import Viseron
from viseron.domains import setup_domain
from viseron.domains.object_detector import BASE_CONFIG_SCHEMA

from .const import (
    COMPONENT,
    CONFIG_DEVICE,
    CONFIG_LABEL_PATH,
    CONFIG_MODEL_PATH,
    CONFIG_OBJECT_DETECTOR,
    DEFAULT_DEVICE,
    DEFAULT_LABEL_PATH,
    DEFAULT_MODEL_PATH,
)

LOGGER = logging.getLogger(__name__)


DEVICE_REGEXES = [
    re.compile(r"^:[0-9]$"),  # match ':<N>'
    re.compile(r"^(usb|pci|cpu)$"),  # match 'usb', 'pci' and 'cpu'
    re.compile(r"^(usb|pci):[0-9]$"),  # match 'usb:<N>' and 'pci:<N>'
]


def edgetpu_device_validator(device):
    """Check for valid EdgeTPU device name.

    Valid values are:
        ":<N>" : Use N-th Edge TPU
        "usb" : Use any USB Edge TPU
        "usb:<N>" : Use N-th USB Edge TPU
        "pci" : Use any PCIe Edge TPU
        "pci:<N>" : Use N-th PCIe Edge TPU
        "cpu" : Run on the CPU
    """
    for regex in DEVICE_REGEXES:
        if regex.match(device):
            return device
    raise vol.Invalid(
        f"EdgeTPU device {device} is invalid. Please check your configuration"
    )


CONFIG_SCHEMA = vol.Schema(
    {
        COMPONENT: vol.Schema(
            {
                vol.Required(CONFIG_OBJECT_DETECTOR): BASE_CONFIG_SCHEMA.extend(
                    {
                        vol.Optional(
                            CONFIG_MODEL_PATH, default=DEFAULT_MODEL_PATH
                        ): str,
                        vol.Optional(
                            CONFIG_LABEL_PATH, default=DEFAULT_LABEL_PATH
                        ): str,
                        vol.Optional(CONFIG_DEVICE, default=DEFAULT_DEVICE): vol.All(
                            str, edgetpu_device_validator
                        ),
                    }
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(vis: Viseron, config):
    """Set up the edgetpu component."""
    config = config[COMPONENT]
    for domain in config.keys():
        setup_domain(vis, config, COMPONENT, domain)

    return True
