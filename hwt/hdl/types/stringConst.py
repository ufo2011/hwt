from hwt.doc_markers import internal
from hwt.hdl.const import HConst
from hwt.hdl.operator import HOperatorNode
from hwt.hdl.operatorDefs import HwtOps
from hwt.hdl.types.defs import BOOL
from hwt.hdl.types.typeCast import toHVal


class HStringConst(HConst):
    """
    Value class for hdl HString type
    """

    @classmethod
    def from_py(cls, typeObj, val, vld_mask=None):
        """
        :param val: python string or None
        :param typeObj: instance of HString HdlType
        :param vld_mask: if is None validity is resolved from val
            if is 0 value is invalidated
            if is 1 value has to be valid
        """
        assert isinstance(val, str) or val is None
        vld = 0 if val is None else 1
        if not vld:
            assert vld_mask is None or vld_mask == 0
            val = ""
        else:
            if vld_mask == 0:
                val = ""
                vld = 0

        return cls(typeObj, val, vld)

    def to_py(self):
        if not self._is_full_valid():
            raise ValueError(f"Value of {self} is not fully defined")
        return self.val

    @internal
    def _eq__const(self, other):
        eq = self.val == other.val
        vld = int(self.vld_mask and other.vld_mask)

        return BOOL.getConstCls()(BOOL, int(eq), vld)

    def _eq(self, other):
        other = toHVal(other, self._dtype)
        self_is_val = isinstance(self, HConst)
        other_is_val = isinstance(self, HConst)

        if self_is_val and other_is_val:
            return self._eq__const(other)
        else:
            assert self._dtype == other._dtype, (self, self._dtype, other, other._dtype)
            return HOperatorNode.withRes(HwtOps.EQ, [self, other], BOOL)
