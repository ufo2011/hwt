from hdl_toolkit.hdlObjects.types.defs import INT, BOOL, STR, BIT
from hdl_toolkit.hdlObjects.types.bits import Bits
from hdl_toolkit.hdlObjects.types.typeCast import toHVal

def fromPyValToValueFn(pyT, hdlT):
    def fn(val):
        """create hdl value from hdl Value or Param or python value"""
        return toHVal(val)._convert(hdlT)
    return fn

hInt = fromPyValToValueFn(int, INT)

# create hdl boolean value (for example boolean value in vhdl)
hBool = fromPyValToValueFn(bool, BOOL)

# create hdl string value (for example string value in vhdl)
hStr = fromPyValToValueFn(str, STR)

# create hdl bit value (for example STD_LOGIC value in vhdl)
hBit = fromPyValToValueFn(int, BIT)

def mkRange(width):
    """Make hdl range (for example 1 downto 0 in vhdl)
       @return: (width -1, 0) 
    """
    to = toHVal(width)
    to = to - 1
    return to._downto(0)

def vecT(width, signed=None):
    """Make contrained vector type for example std_logic_vector(width-1 downto 0) in vhdl"""
    return Bits(widthConstr=mkRange(width), signed=signed, forceVector=True)

def vec(val, width):
    """create hdl vector value"""
    assert(val < 2 ** width)
    return vecT(width).fromPy(val)

def hRange(upper, lower):
    upper = toHVal(upper)
    return upper._downto(lower)