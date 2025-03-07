"""simple Python binding for fribidi.

rlbidi uses libfribidi to order text visually using the unicode
algorithm. rlbidi can also convert text from visual order to
logical order, but the conversion may be wrong in certain cases.
"""
__version__ = '0.1.0'
__all__ = ('log2vis', 'LTR', 'ON', 'RTL', 'WLTR', 'WRTL',
           'rlbidiVersion', 'fribidiVersion', 'fribidiInterfaceVersion',
           'fribidiUnicodeVersion', '_log2vis', 'bidiDirMap',
           'bidiWordList')
from . _rlbidi import LTR, ON, RTL, WLTR, WRTL, rlbidiVersion, fribidiVersion, \
        fribidiInterfaceVersion, fribidiUnicodeVersion, log2vis as _log2vis
bidiDirMap = dict(LTR=LTR, ON=ON, RTL=RTL, WLTR=WLTR, WRTL=WRTL)

assert __version__==rlbidiVersion, "Non matching version rlbidi=%s!= _rlbidi=%s" % (__version__,rlbidiVersion)

def log2vis(logical, base_direction=RTL, encoding="utf-8", clean=True, reordernsm=True,
                        positions_L_to_V=None, positions_V_to_L=None, embedding_levels=None):
    """
    Return string reordered visually according to base direction.
    Return the same type of input string, either str or bytes using
    encoding.

    Note that this function does not handle line breaking. You should
    call log2vis with each line.

    Arguments:
    - logical: str or encoded bytes
    - base_direction: optional logical base direction. Accepts one of
      the constants LTR, RTL or ON, defined in this module. ON calculate
      the base direction according to the BiDi algorithm.
    - encoding: optional string encoding (ignored for str input)
    """
    if isinstance(base_direction,str):
        _ = bidiDirMap.get(base_direction.upper(),None)
        if _ is None:
            raise ValueError(f'argument base_direction={base_direction} is invalid; should be one of ({", ".join(bidiDirMap.keys())})')
        else:
            base_direction = _
    if not isinstance(logical, str):
        logical = str(logical, encoding)
    else:
        encoding = None
    res = _log2vis(logical, base_direction=base_direction, clean=clean, reordernsm=reordernsm,
                        positions_L_to_V=positions_L_to_V, positions_V_to_L=positions_V_to_L,
                        embedding_levels=embedding_levels)
    return res.encode(encoding) if encoding else res
