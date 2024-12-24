from typing import ClassVar, Mapping, Sequence, Any, Dict, Optional, cast
from typing_extensions import Self

from viam.module.types import Reconfigurable
from viam.proto.common import ResourceName
from viam.proto.app.robot import ComponentConfig
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily

from viam.components.board import Board
from viam.components.sensor import Sensor
from viam.components.generic import Generic
from viam.logging import getLogger
from viam.utils import struct_to_dict, dict_to_struct, ValueTypes

import statistics
import asyncio
import time

LOGGER = getLogger(__name__)


hour = 60*60
day = 60*60*24
week = 60*60*24*7

class ARGENT(Sensor, Reconfigurable):
    MODEL: ClassVar[Model] = Model(ModelFamily("biotinker", "sensor"), "argent")

    # Constructor
    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        sensor = cls(config.name)
        sensor.reconfigure(config, dependencies)
        return sensor

    # Validates JSON Configuration
    @classmethod
    def validate(cls, config: ComponentConfig):
        board = config.attributes.fields["board"].string_value
        adc = config.attributes.fields["adc"].string_value
        if board == "":
            raise Exception("A board must be defined")
        if adc == "":
            raise Exception("A adc must be defined")
        return

    # Handles attribute reconfiguration
    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        board_name = config.attributes.fields["board"].string_value
        board = dependencies[Board.get_resource_name(board_name)]
        adc_name = config.attributes.fields["adc"].string_value
        adc = dependencies[Sensor.get_resource_name(adc_name)]
        self.board = board
        self.adc = adc
        
        self.hour_time = time.time()
        self.day_time = time.time()
        self.week_time = time.time()
        
        self.hour_hits = 0
        self.day_hits = 0
        self.week_hits = 0
        
        return

    """ Implement the methods the Viam RDK defines for the sensor API (rdk:component:sensor) """
    async def get_readings(self, extra: Optional[Dict[str, Any]] = None, **kwargs):
        wind_dir_analog = await self.adc.get_readings()
        rain = await self.board.digital_interrupt_by_name("rain_gauge")
        ameno = await self.board.digital_interrupt_by_name("amenometer")
        
        dir_mov_avg = []
        wind_mph = 0
        
        rain_hits = await rain.value()

        ameno_ticks = await read_freq(ameno)
        wind_mph = ameno_ticks * 1.492 # Magic number to convert amenometer ticks to mph

        rain_hits = await rain.value()
        cur_dir = wind_dir_analog["wind_dir"]

        return_value: Dict[str, Any] = dict()
        return_value["wind_dir_degrees"] = closest_dir(cur_dir)
        return_value["wind_mph"] = wind_mph
        
        return_value["rain_inches_last_hour"] = (rain_hits - self.hour_hits) * 0.011 # magic number to convert rain ticks to inches. Use 0.2794 for mm
        return_value["rain_inches_last_day"] = (rain_hits - self.day_hits) * 0.011 # magic number to convert rain ticks to inches. Use 0.2794 for mm
        return_value["rain_inches_last_week"] = (rain_hits - self.week_hits) * 0.011 # magic number to convert rain ticks to inches. Use 0.2794 for mm
        
        now = time.time()
        if now - self.hour_time > hour:
            self.hour_hits = rain_hits
            self.hour_time = now
        if now - self.day_time > day:
            self.day_hits = rain_hits
            self.day_time = now
        if now - self.week_time > week:
            self.week_hits = rain_hits
            self.week_time = now
        
        return return_value

def closest_dir(my_dir):
    # Wind deg ADC readings with 1kohm resistor and 3.3v
    wind_degs = {995: 0,
                 880: 22.5,
                 905: 45,
                 468:67.5,
                 497:90,
                 405:112.5,
                 692:135,
                 585:157.5,
                 813:180,
                 765:202.5,
                 960:225,
                 953: 247.5,
                 1015: 270,
                 997: 292.5,
                 1007: 315,
                 975: 337.5
    }

    closest = 99999
    for key in wind_degs.keys():
        if abs(my_dir - key) < abs(my_dir - closest):
            closest = key
    return wind_degs[closest]

# reads ticks per second
async def read_freq(ameno_interrupt):
    time.sleep(0.1)
    ameno_val_before = await ameno_interrupt.value()
    start = time.time()
    time.sleep(0.5)
    ameno_val_after = await ameno_interrupt.value()
    end = time.time()
    ticks = ameno_val_after - ameno_val_before
    elapsed = end - start
    freq = (ticks/2)/elapsed
    return freq
