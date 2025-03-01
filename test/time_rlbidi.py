#!/usr/bin/python
# -*- coding: utf-8 -*-
""" 
time rlbidi with all hebrew encodings.
"""
import timeit
import rlbidi
import sys
isPy3 = sys.version_info[0]==3
if isPy3:
    xrange = range

hebrew_encodings = ['unicode', 'utf-8', 'utf-16', 'iso8859-8', 'cp1255']

def timeEncoding(encoding, tests):
    setup="""
import rlbidi
text = u'Hello - \\u05e9\\u05dc\\u05d5\\u05dd, hello - \\u05e9\\u05dc\\u05d5\\u05dd, hello - \\u05e9\\u05dc\\u05d5\\u05dd, hello - \\u05e9\\u05dc\\u05d5\\u05dd, hello - \\u05e9\\u05dc\\u05d5\\u05dd.'
if '%(encoding)s' != 'unicode':
    text = text.encode('%(encoding)s')
""" % locals()
    
    if encoding in ['unicode', 'utf-8']:
        # utf-8 is the default encoding for strings
        code = "rlbidi.log2vis(text)"
    else:
        # other encodings require encoding parameter
        code = "rlbidi.log2vis(text, encoding='%s')" % encoding

    timer = timeit.Timer(code, setup)
    seconds = timer.timeit(number=tests)
    microseconds = 1000000 * seconds / tests
    print("%12s: %.8f seconds (%.2f usec/pass)" % (encoding, seconds,
                                                   microseconds))

    
# warm up caches
for i in xrange(100000):
    rlbidi.log2vis(u'Some text to warm up the caches')

lines = 50 # typical screen of text
print('\ntime to reorder %s lines:\n' % lines)
for encoding in hebrew_encodings:
    timeEncoding(encoding, lines)

lines = 100000 
print('\ntime to reorder %s lines:\n' % lines)
for encoding in hebrew_encodings:
    timeEncoding(encoding, lines)
