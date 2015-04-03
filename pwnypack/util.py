from __future__ import print_function
import argparse
from six.moves import range
import re
import binascii
import sys
import pwnypack.main
import pwnypack.codec


__all__ = [
    'cycle',
    'cycle_find',
    'reghex',
]


def deBruijn(n, k):
    '''
    An implementation of the FKM algorithm for generating the de Bruijn
    sequence containing all k-ary strings of length n, as described in
    "Combinatorial Generation" by Frank Ruskey.
    '''

    a = [ 0 ] * (n + 1)

    def gen(t, p):
        if t > n:
            for v in a[1:p + 1]:
                yield v
        else:
            a[t] = a[t - p]
         
            for v in gen(t + 1, p):
                yield v
         
            for j in range(a[t - p] + 1, k):
                a[t] = j
                for v in gen(t + 1, t):
                    yield v

    return gen(1, 1)


def cycle(length, width=4, **kwargs):
    iter = deBruijn(width, 26)
    return ''.join([chr(ord('A') + next(iter)) for i in range(length)])


def cycle_find(key, width=4):
    key_len = len(key)
    buf = ''

    iter = deBruijn(width, 26)

    for i in range(key_len):
        buf += chr(ord('A') + next(iter))

    if buf == key:
        return 0

    for i, c in enumerate(iter):
        buf = buf[1:] + chr(ord('A') + c)
        if buf == key:
            return i + 1

    return -1


REGHEX_PATTERN = r'(([a-fA-F0-9]{2})|(([?.])(\{\d+\})?)|(\*|\+)|\s+)'
reghex_check = re.compile(REGHEX_PATTERN + '+')
reghex_regex = re.compile(REGHEX_PATTERN)


def reghex(pattern):
    if not reghex_check.match(pattern):
        raise SyntaxError('Invalid reghex pattern.')

    b_pattern = b''

    for match in reghex_regex.finditer(pattern):
        _, match_hex, _, match_char, match_char_len, match_star_plus = match.groups()
        if match_hex:
            b_pattern += pwnypack.codec.dehex(match_hex)
        elif match_char:
            if match_char == '?':
                if match_char_len is None:
                    b_pattern += b'.?'
                else:
                    b_pattern += ('.{0,%d}?' % int(match_char_len[1:-1])).encode('ascii')
            else:
                if match_char_len is None:
                    b_pattern += b'.'
                else:
                    b_pattern += b'.' * int(match_char_len[1:-1])
        elif match_star_plus:
            b_pattern += b'.' + match_star_plus.encode('ascii') + b'?'

    try:
        return re.compile(b_pattern)
    except (TypeError, binascii.Error, re.error):
        raise SyntaxError('Invalid reghex pattern.')


@pwnypack.main.register('cycle')
def cycle_app(parser, cmd, args):  # pragma: no cover
    """
    Generate a de Bruijn sequence of a given length.
    """

    parser.add_argument('-w', '--width', type=int, default=4, help='the length of the cycled value')
    parser.add_argument('length', type=int, help='the cycle length to generate')
    args = parser.parse_args(args)
    return cycle(args.length, args.width)


@pwnypack.main.register('cycle-find')
def cycle_find_app(_parser, cmd, args):  # pragma: no cover
    """
    Find the first position of a value in a de Bruijn sequence.
    """

    parser = argparse.ArgumentParser(
        prog=_parser.prog,
        description=_parser.description,
    )
    parser.add_argument('-w', '--width', type=int, default=4, help='the length of the cycled value')
    parser.add_argument('value', help='the value to determine the position of, read from stdin if missing', nargs='?')
    args = parser.parse_args(args)
    index = cycle_find(pwnypack.main.string_value_or_stdin(args.value), args.width)
    if index == -1:
        print('Not found.')
        sys.exit(1)
    else:
        print('Found at position: %d' % index)
