from typing import Callable, Union

from hwt.doc_markers import internal
from hwt.hdl.const import HConst
from hwt.hdl.operator import HOperatorNode
from hwt.hdl.operatorDefs import HwtOps, HOperatorDef, CMP_OP_SWAP
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.defs import BOOL
from hwt.hdl.types.typeCast import toHVal
from hwt.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.exceptions import SignalDriverErr
from pyMathBitPrecise.bit_utils import mask
from pyMathBitPrecise.bits3t import bitsCmp__val, bitsBitOp__val, \
    bitsArithOp__val


@internal
def bitsCmp_detect_useless_cmp(op0, op1, op):
    v = int(op1)
    width = op1._dtype.bit_length()
    if op0._dtype.signed:
        min_val = -1 if width == 1 else -mask(width - 1) - 1
        max_val = 0 if width == 1 else mask(width - 1)
    else:
        min_val = 0
        max_val = mask(width)

    if v == min_val:
        # value can not be lower than min_val
        if op == HwtOps.GE:
            # -> always True
            return BOOL.from_py(1, 1)
        elif op == HwtOps.LT:
            # -> always False
            return BOOL.from_py(0, 1)
        elif op == HwtOps.LE:
            # convert <= to == to highlight the real function
            return HwtOps.EQ
    elif v == max_val:
        # value can not be greater than max_val
        if op == HwtOps.GT:
            # always False
            return BOOL.from_py(0, 1)
        elif op == HwtOps.LE:
            # always True
            return BOOL.from_py(1, 1)
        elif op == HwtOps.GE:
            # because value can not be greater than max
            return HwtOps.EQ

AnyHValue = Union[HConst, RtlSignalBase]

@internal
def bitsCmp(self: AnyHValue, other: AnyHValue,
            op: HOperatorDef,
            selfReduceVal: HConst,
            evalFn:Callable[[AnyHValue, AnyHValue], AnyHValue]=None):
    """
    Apply a generic comparison binary operator

    :attention: If other is Bool signal convert this to bool (not ideal,
        due VHDL event operator)
    :ivar self: operand 0
    :ivar other: operand 1
    :ivar op: operator used
    :ivar selfReduceVal: the value which is a result if operands are all same signal (e.g. a==a = 1, b<b=0)
    :ivar evalFn: override of a python operator function (by default one from "op" is used)
    """
    t = self._dtype
    other = toHVal(other, t)
    ot = other._dtype
    if not isinstance(ot, t.__class__):
        raise TypeError(ot)

    if evalFn is None:
        evalFn = op._evalFn

    iamVal = isinstance(self, HConst)
    otherIsVal = isinstance(other, HConst)
    type_compatible = False
    if ot == BOOL:
        self = self._auto_cast(BOOL)
        type_compatible = True
    elif t == ot:
        type_compatible = True
    # lock type width/signed to other type with
    elif not ot.strict_width or not ot.strict_sign:
        type_compatible = True
        other = other._auto_cast(t)
    elif not t.strict_width or not t.strict_sign:
        type_compatible = True
        other = other._auto_cast(ot)

    if iamVal and otherIsVal:
        if type_compatible:
            return bitsCmp__val(self, other, evalFn)
    else:
        if type_compatible:
            # try to reduce useless cmp
            res = None
            if otherIsVal and other._is_full_valid():
                res = bitsCmp_detect_useless_cmp(self, other, op)
            elif iamVal and self._is_full_valid():
                res = bitsCmp_detect_useless_cmp(other, self, CMP_OP_SWAP[op])

            if res is None:
                pass
            elif isinstance(res, HConst):
                return res
            else:
                assert res == HwtOps.EQ, res
                op = res

            if self is other:
                return selfReduceVal
            else:
                return HOperatorNode.withRes(op, [self, other], BOOL)

        elif t.signed != ot.signed:
            if t.signed is None:
                self = self._convSign(ot.signed)
                return bitsCmp(self, other, op, evalFn)
            elif ot.signed is None:
                other = other._convSign(t.signed)
                return bitsCmp(self, other, op, evalFn)
        elif t.force_vector != ot.force_vector:
            if t.force_vector:
                self = self[0]
            else:
                other = other[0]
            return bitsCmp(self, other, op, evalFn)

    raise TypeError(f"Values of types (", self._dtype, other._dtype, ") are not comparable")


@internal
def extractNegation(sig: RtlSignalBase):
    """
    :return: tuple(the signal without negation, True if signal was negated)
    """
    try:
        d = sig.singleDriver()
    except SignalDriverErr:
        return (sig, False)
    
    if isinstance(d, HOperatorNode) and d.operator == HwtOps.NOT:
        return d.operands[0], True
    return sig, False


@internal
def bitsBitOp(self: Union[RtlSignalBase, HConst], other,
              op: HOperatorDef,
              getVldFn: Callable[[HConst, HConst], int],
              reduceValCheckFn: Callable[[RtlSignalBase, HConst], bool],
              reduceSigCheckFn: Callable[[RtlSignalBase,  # op0Original
                                          bool,  # op0Negated
                                          bool  # op1Negated
                                          ], Union[RtlSignalBase, HConst]]):
    """
    Apply a generic bitwise binary operator

    :attention: If other is Bool signal, convert this to bool
        (not ideal, due VHDL event operator)
    :ivar self: operand 0
    :ivar other: operand 1
    :ivar op: operator used
    :ivar getVldFn: function to resolve invalid (X) states
    :ivar reduceValCheckFn: function to reduce useless operators (partially evaluate the expression if possible)
    :ivar reduceSigCheckFn: function to reduce useless operators for signals and its negation flags
        (e.g. a&a = a, a&~a=0, b^b=0)
        function parameters are in format (op0Original:RtlSignalBase, op0Negated: bool, op1Negated:bool) -> Union[RtlSignalBase, HConst]:
        returns result signal if reduction is possible else None
    """
    other = toHVal(other, self._dtype)

    iamVal = isinstance(self, HConst)
    otherIsVal = isinstance(other, HConst)

    if iamVal and otherIsVal:
        other = other._auto_cast(self._dtype)
        return bitsBitOp__val(self, other, op._evalFn, getVldFn)
    else:
        s_t = self._dtype
        o_t = other._dtype
        if not isinstance(o_t, s_t.__class__):
            raise TypeError(o_t)

        if s_t == o_t:
            pass
        elif o_t == BOOL and s_t != BOOL:
            self = self._auto_cast(BOOL)
            return op._evalFn(self, other)
        elif o_t != BOOL and s_t == BOOL:
            other = other._auto_cast(BOOL)
            return op._evalFn(self, other)
        else:
            if s_t.signed is not o_t.signed and bool(s_t.signed) == bool(o_t.signed):
                # automatically cast unsigned to vector
                if s_t.signed == False and o_t.signed is None:
                    self = self._vec()
                    s_t = self._dtype
                elif s_t.signed is None and o_t.signed == False:
                    other = other._vec()
                    o_t = other._dtype
                else:
                    raise ValueError("Invalid value for signed flag of type", s_t.signed, o_t.signed, s_t, o_t)

            if s_t == o_t:
                # due to previsous cast the type may become the same
                pass
            elif s_t.bit_length() == 1 and o_t.bit_length() == 1\
                    and s_t.signed is o_t.signed \
                    and s_t.force_vector != o_t.force_vector:
                # automatically cast to vector with a single item to a single bit
                if s_t.force_vector:
                    self = self[0]
                else:
                    other = other[0]

            else:
                raise TypeError("Can not apply operator %r (%r, %r)" % 
                                (op, self._dtype, other._dtype))

        if otherIsVal:
            r = reduceValCheckFn(self, other)
            if r is not None:
                return r

        elif iamVal:
            r = reduceValCheckFn(other, self)
            if r is not None:
                return r

        else:
            _self, _self_n = extractNegation(self)
            _other, _other_n = extractNegation(other)
            if _self is _other:
                return reduceSigCheckFn(self, _self_n, _other_n)

        return HOperatorNode.withRes(op, [self, other], self._dtype)


@internal
def bitsArithOp(self, other, op):
    other = toHVal(other, self._dtype)
    if not isinstance(other._dtype, HBits):
        raise TypeError(other._dtype)

    self_is_val = isinstance(self, HConst)
    other_is_val = isinstance(other, HConst)

    if self_is_val and other_is_val:
        return bitsArithOp__val(self, other, op._evalFn)
    else:
        if self._dtype.signed is None:
            self = self._unsigned()

        if op in (HwtOps.ADD, HwtOps.SUB) and other_is_val and other._is_full_valid() and int(other) == 0:
            return self

        resT = self._dtype
        if op == HwtOps.ADD and self_is_val and self._is_full_valid() and int(self) == 0:
            return other._auto_cast(resT)

        if isinstance(other._dtype, HBits):
            t0 = self._dtype
            t1 = other._dtype
            if t0.bit_length() != t1.bit_length():
                if not t1.strict_width:
                    # resize to type of this
                    other = other._auto_cast(t1)
                    t1 = other._dtype
                    pass
                elif not t0.strict_width:
                    # resize self to type of result
                    self = self._auto_cast(t0)
                    t0 = self._dtype
                    pass
                else:
                    raise TypeError("%r %r %r" % (self, op, other))

            if t1.signed != resT.signed:
                other = other._convSign(t0.signed)
        else:
            raise TypeError("%r %r %r" % (self, op, other))

        o = HOperatorNode.withRes(op, [self, other], self._dtype)
        return o._auto_cast(resT)
