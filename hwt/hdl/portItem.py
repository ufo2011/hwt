from hwt.doc_markers import internal
from hwt.constants import DIRECTION
from hwt.hdl.sensitivityCtx import SensitivityCtx
from hwt.hdl.statements.statement import HwtSyntaxError
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.variables import HdlSignalItem


class HdlPortItem():
    """
    HDL entity/module/component port item
    Used to split signal paths on component boundary.

    :note: src/dst are named based on input output signal direction
        both dst and src can be parent/component signal, it depends on direction
    """

    def __init__(self, name: str, direction: DIRECTION, dtype: HdlType, module: "HwModule"):
        self.name = name
        self.module = module
        self._dtype = dtype
        self.direction = direction
        self.src = None
        self.dst = None

    @classmethod
    def fromSignal(cls, s: HdlSignalItem, component, d: DIRECTION):
        return cls(s._name, d, s._dtype, component)

    @internal
    def connectOuterSig(self, signal):
        """
        Connect to port item on submodule
        """
        if self.direction == DIRECTION.IN:
            if self.src is not None:
                raise HwtSyntaxError(
                    "Port %s is already associated with %r"
                    % (self.name, self.src))
            self.src = signal
            signal.endpoints.append(self)

        elif self.direction == DIRECTION.OUT:
            if self.dst is not None:
                raise HwtSyntaxError(
                    "Port %s is already associated with %r"
                    % (self.name, self.dst))
            self.dst = signal
            signal.drivers.append(self)

        else:
            raise NotImplementedError(self)

        signal.hidden = False
        signal.ctx.subHwModules.add(self.module)

    @internal
    def connectInternSig(self, signal):
        """
        Connect signal from internal side of of this component to this port.
        """
        if self.direction == DIRECTION.OUT:
            if self.src is not None:
                raise HwtSyntaxError(
                    "Port %s is already associated with signal %s"
                    % (self.name, str(self.src)))
            self.src = signal
            self.src.endpoints.append(self)

        elif self.direction == DIRECTION.IN:
            if self.dst is not None:
                raise HwtSyntaxError(
                    "Port %s is already associated with signal %s"
                    % (self.name, str(self.dst)))
            self.dst = signal
            self.dst.drivers.append(self)
        else:
            raise NotImplementedError(self.direction)

    @internal
    def getInternSig(self):
        """
        return signal inside module which has this port
        """
        d = self.direction
        if d == DIRECTION.IN:
            return self.dst
        elif d == DIRECTION.OUT:
            return self.src
        else:
            raise NotImplementedError(d)

    @internal
    def getOuterSig(self):
        """
        return signal inside module which has this port
        """
        d = self.direction
        if d == DIRECTION.OUT:
            return self.dst
        elif d == DIRECTION.IN:
            return self.src
        else:
            raise NotImplementedError(d)

    @internal
    def _walk_sensitivity(self, casualSensitivity: set, seen: set, ctx: SensitivityCtx):
        """
        :see: :meth:`hwt.synthesizer.rtlLevel.rtlSignal.RtlSignal._walk_sensitivity`
        """
        return
        yield

    def __repr__(self):
        return f"<{self.__class__.__name__:s} src:{self.src}, dst:{self.dst}>"
