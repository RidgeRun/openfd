
import os, sys
import unittest

sys.path.insert(1, os.path.abspath('..'))

import serial_comm
 
class SerialInstallerTestCase(unittest.TestCase):
    
    def setUp(self):
        inst = serial_comm.SerialInstaller()
        
    def tearDown(self):
        pass
 
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(SerialInstallerTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
