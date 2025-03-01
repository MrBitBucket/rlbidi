"""simple Python binding for fribidi.

rlbidi uses libfribidi to order text visually using the unicode
algorithm. rlbidi can also convert text from visual order to
logical order, but the conversion may be wrong in certain cases.
"""
__version__ = '0.0.1'
__all__ = ('log2vis', 'reorderMap', 'LTR', 'ON', 'RTL', 'WLTR', 'WRTL',
           'rlbidiVersion', 'fribidiVersion', 'fribidiInterfaceVersion',
           'fribidiUnicodeVersion', '_log2vis', 'bidiDirMap',
           'bidiWordList')
import sys
isPy3 = sys.version_info[0]==3
if isPy3:
    unicode = str

from . _rlbidi import LTR, ON, RTL, WLTR, WRTL, rlbidiVersion, fribidiVersion, \
        fribidiInterfaceVersion, fribidiUnicodeVersion, log2vis as _log2vis, \
        reorderMap as _reorderMap
bidiDirMap = dict(LTR=LTR, ON=ON, RTL=RTL, WLTR=WLTR, WRTL=WRTL)

assert __version__==rlbidiVersion, "Non matching version rlbidi=%s!= _rlbidi=%s" % (__version__,rlbidiVersion)

def log2vis(logical, base_direction=RTL, encoding="utf-8", clean=True, reordernsm=True,
                        positions_L_to_V=None, positions_V_to_L=None, embedding_levels=None):
    """
    Return string reordered visually according to base direction.
    Return the same type of input string, either unicode or string using
    encoding.

    Note that this function does not handle line breaking. You should
    call log2vis with each line.

    Arguments:
    - logical: unicode or encoded string
    - base_direction: optional logical base direction. Accepts one of
      the constants LTR, RTL or ON, defined in this module. ON calculate
      the base direction according to the BiDi algorithm.
    - encoding: optional string encoding (ignored for unicode input)
    """
    if isinstance(base_direction,str):
        _ = bidiDirMap.get(base_direction.upper(),ON)
        if _ is None:
            raise ValueError(f'argument base_direction={base_direction} is invalid; should be one of ({", ".join(bidiDirMap.keys())})')
        else:
            base_direction = _
    if not isinstance(logical, unicode):
        logical = unicode(logical, encoding)
    else:
        encoding = None
    res = _log2vis(logical, base_direction=base_direction, clean=clean, reordernsm=reordernsm,
                        positions_L_to_V=positions_L_to_V, positions_V_to_L=positions_V_to_L,
                        embedding_levels=embedding_levels)
    return res.encode(encoding) if encoding else res

def reorderMap(logical, encoding="utf-8"):
    if not isinstance(logical, unicode):
        logical = unicode(logical, encoding)
    return _reorderMap(logical)

import re
wordpat = re.compile(r'\S+')
del re
class BidiIndexStr(str):
    def __new__(cls, s, bidiIndex=0):
        self = super().__new__(cls,s)
        self.__bidiIndex__ = bidiIndex
        return self

def bidiWordList(words,direction='RTL',clean=True):
    if direction not in ('LTR','RTL'): return words
    if not isinstance(words,(list,tuple)):
        raise ValueError('bidiWordList argument words should be a list or tuple of strings')
    raw = ' '.join(words)
    V2L = []
    bidi = log2vis(raw, base_direction=direction, clean=clean, positions_V_to_L=V2L)

    VMAP = {}
    for i, m in enumerate(wordpat.finditer(bidi)):
        t = (m.group(0), i)
        start, end = m.span()
        for j in range(start,end):
            VMAP[V2L[j]] = t

    res = [].append
    #create result by assigning a V word to a raw one
    for w, m in enumerate(wordpat.finditer(raw)):
        for j in range(*m.span()):
            if j in VMAP:
                res(BidiIndexStr(*VMAP[j]))
                break
        else:
            #we seem to have a raw word that doesn't appear in bidi
            pass
    return res.__self__
