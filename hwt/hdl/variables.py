from hwt.doc_markers import internal
from hwt.hdl.hdlObject import HdlObject
from hwt.mainBases import RtlSignalBase


class HdlSignalItem(HdlObject):
    """
    Basic hdl signal used to design circuits
    """
    __slots__ = [
        "_name",
        "_dtype",
        "virtual_only",
        "def_val",
    ]
    
    def __init__(self, name: str, dtype: "HdlType", def_val=None, virtual_only=False):
        """
        :param _name: name for better orientation in netlists
            (used only in serialization)
        :param dtype: data type of this signal
        :param def_val: value for initialization
        :param virtual_only: flag indicates that this assignments is only
            virtual and should not be added into
            netlist, because it is only for internal notation
        """
        assert isinstance(name, str), name
        self._name = name
        self._dtype = dtype
        self.virtual_only = virtual_only
        if def_val is None:
            def_val = dtype.from_py(None)
        self.def_val = def_val
        self._set_def_val()

    @internal
    def _set_def_val(self):
        v = self.def_val
        if isinstance(v, RtlSignalBase):
            v = v.staticEval()

        self._val = v.__copy__()
