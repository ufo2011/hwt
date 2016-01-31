from vhdl_toolkit.synthetisator.interfaceLevel.unit import Unit, UnitWithSource
from vhdl_toolkit.synthetisator.interfaceLevel.interfaces.std import Ap_clk, \
    Ap_rst_n
from vhdl_toolkit.synthetisator.interfaceLevel.interfaces.amba import  AxiLite
from vhdl_toolkit.formater import formatVhdl
from vhdl_toolkit.synthetisator.param import Param


class AxiLiteBasicSlave(UnitWithSource):
    _origin = "vhdl/axiLite_basic_slave.vhd"
    
class AxiLiteSlaveContainer(Unit):
    ADDR_WIDTH = Param(8)
    DATA_WIDTH = Param(8)
    slv = AxiLiteBasicSlave()
    clk = Ap_clk(slv.S_AXI_ACLK, isExtern=True)
    rst_n = Ap_rst_n(slv.S_AXI_ARESETN, isExtern=True)
    axi = AxiLite(slv.S_AXI, isExtern=True)
    slv.c_s_axi_addr_width.inherit(ADDR_WIDTH)
    slv.c_s_axi_data_width.inherit(DATA_WIDTH)

if __name__ == "__main__":

    u = AxiLiteSlaveContainer()
    print(formatVhdl(
                     "\n".join([ str(x) for x in u._synthesise()])
                     ))
