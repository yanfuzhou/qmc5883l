import math
import logging
from smbus2 import SMBus


"""Driver for the QMC5883l 3-Axis Magnetic Sensor
Datasheet: https://github.com/e-Gizmo/QMC5883L-GY-271-Compass-module/blob/master/QMC5883L%20Datasheet%201.0%20.pdf 
# noqa
"""

__author__ = "Yanfu Zhou"
__email__ = "yanfu.zhou@outlook.com"
__license__ = 'MIT'
__version__ = '1.2.6'

"""HISTORY
1.0.0 - First
"""
RATES = {
    10: 0,
    50: 1,
    100: 2,
    200: 3,
}

OSR = {
    64: 3,
    128: 2,
    256: 1,
    512: 0,
}

REG_OUT_X_LSB = 0x00
REG_OUT_X_MSB = 0x01
REG_OUT_Y_LSB = 0x02
REG_OUT_Y_MSB = 0x03
REG_OUT_Z_LSB = 0x04
REG_OUT_Z_MSB = 0x05
REG_STATUS = 0x06
REG_TEMP_LSB = 0x07
REG_TEMP_MSB = 0x08
REG_CONF_1 = 0x09
REG_CONF_2 = 0x0a
REG_RST_PERIOD = 0x0b
REG_CHIP_ID = 0x0d


class QMC5883L(object):
    """ Driver for the QMC5883l 3-Axis Magnetic Sensor """
    def __init__(self,
                 adress=13,
                 busnum=1,
                 cont_mode=True,
                 rate=10,
                 full_scale=False,
                 over_sampling_rate=512,
                 interupt=True,
                 pointer_roll=False,
                 restore=False
                 ):

        if over_sampling_rate in OSR:
            self.over_sampling_rate = OSR.get(over_sampling_rate)
        else:
            raise ValueError('oversampling rate is not a allowed value')
        if rate in RATES:
            self.rate = RATES.get(rate)
        else:
            raise ValueError('rate is not a allowed value')

        self.bus = SMBus(busnum)
        self.adress = adress
        self.full_scale = full_scale
        self.interupt = interupt
        self.pointer_roll = pointer_roll
        self.restore = restore
        self.cont_mode = cont_mode
        self.cntrl_reg1 = 0
        self.cntrl_reg2 = 0

        self._declination = 0.0
        self._calibration = [[1.0, 0.0, 0.0],
                             [0.0, 1.0, 0.0],
                             [0.0, 0.0, 1.0]]

        chip_id = self.bus.read_byte_data(self.adress, REG_CHIP_ID)
        if chip_id != 0xff:
            msg = "Chip ID returned 0x%x instead of 0xff; is the wrong chip?"
            logging.warning(msg, chip_id)
        self.mode_continuous()

    def __del__(self):
        self.mode_standby()

    def mode_continuous(self):
        self.bus.write_i2c_block_data(self.adress, REG_CONF_1, [
            (int(self.cont_mode) | int(self.rate) * (2 ** 2) | int(self.full_scale) * (2 ** 4) |
             int(self.over_sampling_rate) * (2 ** 6)),
            (int(self.interupt) | int(self.pointer_roll) * (2 ** 6) | int(not self.restore) * (2 ** 7)),
            1
        ])
        self.bus.write_i2c_block_data(self.adress, REG_CONF_1, [
            (int(self.cont_mode) | int(self.rate) * (2 ** 2) | int(self.full_scale) * (2 ** 4) |
             int(self.over_sampling_rate) * (2 ** 6)),
            (int(self.interupt) | int(self.pointer_roll) * (2 ** 6) | int(self.restore) * (2 ** 7)),
            1
        ])

    def mode_standby(self):
        self.bus.write_i2c_block_data(self.adress, REG_CONF_1, [
            (int(not self.cont_mode) | int(self.rate) * (2 ** 2) | int(self.full_scale) * (2 ** 4) |
             int(OSR.get(64)) * (2 ** 6)),
            (int(self.interupt) | int(self.pointer_roll) * (2 ** 6) | int(not self.restore) * (2 ** 7)),
            1
        ])
        self.bus.write_i2c_block_data(self.adress, REG_CONF_1, [
            (int(not self.cont_mode) | int(self.rate) * (2 ** 2) | int(self.full_scale) * (2 ** 4) |
             int(OSR.get(64)) * (2 ** 6)),
            (int(self.interupt) | int(self.pointer_roll) * (2 ** 6) | int(self.restore) * (2 ** 7)),
            1
        ])

    def get_temp(self):
        data = self.bus.read_i2c_block_data(self.adress, REG_TEMP_LSB, 2)
        t = self._convert_data(data, REG_TEMP_LSB)
        return t

    @staticmethod
    def _convert_data(data, offset):
        if offset == REG_TEMP_LSB:
            val = (data[0] | (data[1] << 8))
        else:
            val = (data[offset] | (data[offset + 1] << 8))
        if val >= 2 ** 15:
            return val - 2 ** 16
        else:
            return val

    def get_magnet_raw(self):
        data = self.bus.read_i2c_block_data(self.adress, REG_OUT_X_LSB, 6)
        x = self._convert_data(data, REG_OUT_X_LSB)
        y = self._convert_data(data, REG_OUT_Y_LSB)
        z = self._convert_data(data, REG_OUT_Z_LSB)
        return [x, y, z]

    def get_magnet(self):
        """Return the horizontal magnetic sensor vector with (x, y) calibration applied."""
        [x, y, z] = self.get_magnet_raw()
        if x is None or y is None:
            [x1, y1] = [x, y]
        else:
            c = self._calibration
            x1 = x * c[0][0] + y * c[0][1] + c[0][2]
            y1 = x * c[1][0] + y * c[1][1] + c[1][2]
        return [x1, y1, z]

    def get_bearing_raw(self):
        """Horizontal bearing (in degrees) from magnetic value X and Y."""
        [x, y, z] = self.get_magnet_raw()
        if x is None or y is None:
            return None
        else:
            b = math.degrees(math.atan2(y, x))
            if b < 0:
                b += 360.0
            return b

    def get_bearing(self):
        """Horizontal bearing, adjusted by calibration and declination."""
        [x, y, z] = self.get_magnet()
        if x is None or y is None:
            return None
        else:
            b = math.degrees(math.atan2(y, x))
            if b < 0:
                b += 360.0
            b += self._declination
            if b < 0.0:
                b += 360.0
            elif b >= 360.0:
                b -= 360.0
        return b

    def set_declination(self, value):
        """Set the magnetic declination, in degrees."""
        if type(value) is int or type(value) is float:
            d = float(value)
            if d < -180.0 or d > 180.0:
                logging.error(u'Declination must be >= -180 and <= 180.')
            else:
                self._declination = d
        else:
            logging.error(u'Declination must be a float value.')

    def get_declination(self):
        """Return the current set value of magnetic declination."""
        return self._declination

    def set_calibration(self, value):
        """Set the 3x3 matrix for horizontal (x, y) magnetic vector calibration."""
        c = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        if len(c) == len(c[0]) == len(c[1]) == len(c[2]) == 3:
            for i in range(0, 3):
                for j in range(0, 3):
                    c[i][j] = float(value[i][j])
            self._calibration = c
        else:
            logging.error(u'Calibration must be a 3x3 float matrix.')

    def get_calibration(self):
        """Return the current set value of the calibration matrix."""
        return self._calibration

    declination = property(fget=get_declination,
                           fset=set_declination,
                           doc=u'Magnetic declination to adjust bearing.')

    calibration = property(fget=get_calibration,
                           fset=set_calibration,
                           doc=u'Transformation matrix to adjust (x, y) magnetic vector.')
