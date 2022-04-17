import qmc5883l

sensor = qmc5883l.QMC5883L()
sensor.declination = -1.6
sensor.calibration = [[1.3471032168031547, 0.12711917401460765, 7934.688352225846],
                      [0.1271191740146076, 1.0465546950298654, 2401.429978299175],
                      [0.0, 0.0, 1.0]]
[x, y, z] = sensor.get_magnet()
bearing = sensor.get_bearing()
