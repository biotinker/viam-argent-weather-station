"""
This file registers the model with the Python SDK.
"""

from viam.components.sensor import Sensor
from viam.resource.registry import Registry, ResourceCreatorRegistration

from .argent import ARGENT

Registry.register_resource_creator(Sensor.SUBTYPE, ARGENT.MODEL, ResourceCreatorRegistration(ARGENT.new, ARGENT.validate))
