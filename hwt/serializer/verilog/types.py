from hdlConvertorAst.hdlAst._expr import HdlTypeAuto, HdlValueId, HdlOp, \
    HdlOpType
from hdlConvertorAst.translate.common.name_scope import LanguageKeyword
from hdlConvertorAst.translate.verilog_to_basic_hdl_sim_model.utils import hdl_index, \
    hdl_downto
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import INT, FLOAT64
from hwt.hdl.types.float import HFloat
from hwt.hdl.types.hdlType import HdlType, MethodNotOverloaded
from hwt.serializer.verilog.utils import SIGNAL_TYPE
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


class ToHdlAstVerilog_types():
    INT = HdlValueId("int", obj=int)
    REG = HdlValueId("reg", obj=LanguageKeyword())
    WIRE = HdlValueId("wire", obj=LanguageKeyword())

    def does_type_requires_extra_def(self, t: HdlType, other_types: list):
        try:
            return t._as_hdl_requires_def(self, other_types)
        except MethodNotOverloaded:
            pass
        return False

    def as_hdl_HdlType_bits(self, typ: HBits, declaration=False):
        isVector = typ.force_vector or typ.bit_length() > 1
        sigType = self.signalType

        if typ == INT:
            t = self.INT
        elif sigType is SIGNAL_TYPE.PORT_WIRE:
            t = HdlTypeAuto
        elif sigType is SIGNAL_TYPE.REG or sigType is SIGNAL_TYPE.PORT_REG:
            t = self.REG
        elif sigType is SIGNAL_TYPE.WIRE:
            t = self.WIRE
        else:
            raise ValueError(sigType)

        if typ.signed is None or typ.signed == False:
            # [yosys] do not produce unsigned type as yosys support is limited
            is_signed = None
        else:
            is_signed = self.as_hdl_int(int(typ.signed))

        if isVector:
            w = typ.bit_length()
            assert isinstance(w, int) or (isinstance(w, RtlSignal) and w._const), w
            w = hdl_downto(self.as_hdl(w - 1),
                           self.as_hdl_int(0))
        else:
            w = None

        return HdlOp(HdlOpType.PARAMETRIZATION, [t, w, is_signed])

    def as_hdl_HdlType_array(self, typ: HArray, declaration=False):
        if declaration:
            raise NotImplementedError()
        else:
            _int = self.as_hdl_int
            size = HdlOp(HdlOpType.DOWNTO, [_int(0),
                                                 _int(int(typ.size) - 1)])
            return hdl_index(self.as_hdl_HdlType(typ.element_t), size)

    def as_hdl_HdlType_enum(self, typ, declaration=False):
        if declaration:
            raise TypeError(
                "Target language does not use enum types, this library should uses HBits instead"
                " (this should not be required because it should have been filtered before)")
        else:
            valueCnt = len(typ._allValues)
            return self.as_hdl_HdlType_bits(HBits(valueCnt.bit_length()),
                                            declaration=declaration)

    def as_hdl_HdlType_float(self, typ: HFloat, declaration=False):
        if typ == FLOAT64:
            return HdlValueId("real")
        else:
            raise NotImplementedError(typ)
