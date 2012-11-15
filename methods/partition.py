# ==========================================================================
#
# Copyright (C) 2012 Ridgerun (http://www.ridgerun.com).
#
# Representation of a memory partition.
#
# ==========================================================================

"""
Representation of a memory partition.

Copyright (C) 2012 Ridgerun (http://www.ridgerun.com).
"""

# ==========================================================================
# Classes
# ==========================================================================

class Partition:
    """ Class that represents a file system partition. """
    
    def __init__(self, name):
        """
        Constructor.
        """
        
        self.name  = name
        self.start = 0
        self.size  = 0
        
    @classmethod
    def hex_format(self, decimal_value, width=8, upper=True):
        """
        Returns the given decimal value as hex of given width (left zeros
        will be appended). After meeting the width requirement, the
        prefix '0x' will be added.
        
        Use the upper switch to have the hexadecimal value all in upper case.
        
        Example:
        
          Suppose the decimal value 3:
          
            width = 1 -> returns 0x3
            width = 2 -> returns 0x03
            ...
            width = 8 -> returns 0x00000003 
        """
        
        # Get the hex value and remove the '0x' prefix
        hex_value = hex(int(decimal_value))[2:]
        
        # Left fill with zeros 
        hex_value = hex_value.zfill(width)
        
        # Uppercase
        if upper:
            hex_value = hex_value.upper()
       
        return '0x' + hex_value
                    
    def set_start(self, start):
        """
        Sets the partition start address (decimal).
        """
        
        self.start = start
        
    def get_start(self, hex_format=False):
        """
        Gets the partition start address (decimal).
        """
        
        if hex_format:
            return Partition.hex_format(self.start)
        else:
            return self.start
        
    def set_size(self, size):
        """
        Sets the partition size (decimal). Size can be '-' to indicate
        the max size available (where not specified).
        """
        
        self.size = size
        
    def get_size(self, hex_format=False):
        """
        Gets the partition size (decimal).
        
        If hex_format is True, the size will be returned as a hex value,
        padded to 8 digits and with the '0x' prefix.     
        """
    
        if self.size == '-':
            return '-'
        
        if hex_format:
            return Partition.hex_format(self.size)
        else:
            return self.size
    
    def get_name(self):
        """
        Gets the partition name.
        """
        
        return self.name
        
if __name__ == '__main__':
    
    p = Partition('test-partition')
    
    p.set_size(100)
    
    print p.get_size()
    print p.get_size(hex_format=True)
    
    p.set_size('-')
    
    print p.get_size()
    print p.get_size(hex_format=True)
    
    p.set_size(100)
    print p.get_size(hex_format=True)
    
    p.set_start(100)
    print p.get_start()
    print p.get_start(hex_format=True)
    
    