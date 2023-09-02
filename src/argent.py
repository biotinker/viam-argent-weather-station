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

LOGGER = getLogger(__name__)

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
        if board == "":
            raise Exception("A board must be defined")
        return

    # Handles attribute reconfiguration
    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        board_name = config.attributes.fields["board"].string_value
        board = dependencies[Board.get_resource_name(board_name)]
        self.board = board
        return

    """ Implement the methods the Viam RDK defines for the sensor API (rdk:component:sensor) """
    async def get_readings(self, extra: Optional[Dict[str, Any]] = None, **kwargs):
        wind_dir_analog = await self.board.analog_reader_by_name("wind_dir")
        rain = await self.board.digital_interrupt_by_name("rain_gauge")
        ameno = await self.board.digital_interrupt_by_name("amenometer")
        ameno_cnt = await self.board.digital_interrupt_by_name("amenometer_count")
        
        dir_mov_avg = []
        wind_mph = 0
        
        ameno_ticks_last = await ameno_cnt.value()
        rain_hits = await rain.value()
        
        # Read the wind dir 20 times and get an average
        for i in range(0, 20):
            await asyncio.sleep(0.05)
            cur_dir = await wind_dir_analog.read()
            dir_mov_avg.append(cur_dir)

        ameno_ticks = await ameno_cnt.value()
        if ameno_ticks_last < ameno_ticks:
            
            ameno_tick_time = await ameno.value()
            wind_mph = (1000000/ameno_tick_time) * 1.492 # Magic number to convert amenometer ticks to mph
            ameno_ticks_last = ameno_ticks
        else:
            wind_mph = 0
        rain_hits = await rain.value()

        return_value: Dict[str, Any] = dict()
        return_value["wind_dir_degrees"] = closest_dir(statistics.fmean(dir_mov_avg))
        return_value["wind_mph"] = wind_mph
        return_value["rain_amt_inches"] = rain_hits * 0.011 # magic number to convert rain ticks to inches. Use 0.2794 for mm
        
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
