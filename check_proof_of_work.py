#!/usr/bin/env python3

import json, hashlib, pyprimes, sys

def sha256(d):
    m = hashlib.sha256()
    m.update(d)
    return m.digest()

def flip(x):
    return bytes(reversed(x))

def get_hash_for_pow(block):
    """
    original memory layout:
        int nVersion;
        uint256 hashPrevBlock;
        uint256 hashMerkleRoot;
        bitsType nBits;
        int64 nTime;
        offsetType nOffset;
    """
    b = block["version"].to_bytes(byteorder="little", length=4) + \
        flip(bytes.fromhex(block["previousblockhash"])) + \
        flip(bytes.fromhex(block["merkleroot"])) + \
        flip(bytes.fromhex(block["bits"])) + \
        flip(block["time"].to_bytes(byteorder="big", length=8))
    b = sha256(sha256(b))
    b = b[::-1]
    return b

ZEROES_BEFORE_HASH_IN_PRIME = 8 # main.h

def set_compact(x):
    """
    The "compact" format is a representation of a whole
    number N using an unsigned 32bit number similar to a
    floating point format.
    The most significant 8 bits are the unsigned exponent of base 256.
    This exponent can be thought of as "number of bytes of N".
    The lower 23 bits are the mantissa.
    Bit number 24 (0x800000) represents the sign of N.
    N = (-1^sign) * mantissa * 256^(exponent-3)
    """
    #word = x & (0x800000-1)
    #size = x >> 24
    #if size <= 3:
    #    size = 3-size
    #else:
    #    size -= 3
    #return word << (8*size)
    size = x >> 24
    size = 3-size if x > 3 else size-3
    return (x & (0x800000-1)) >> (size*8)

def generate_prime_base(has, compact_bits):
    target = 1
    target <<= ZEROES_BEFORE_HASH_IN_PRIME
    for _ in range(256):
        target = (target << 1) + (has & 1)
        has >>= 1

    significant_digits = 1 + ZEROES_BEFORE_HASH_IN_PRIME + 256
    trailing_zeros = set_compact(compact_bits)
    if trailing_zeros < significant_digits:
        return target, 0
    trailing_zeros -= significant_digits
    target <<= trailing_zeros
    return target, trailing_zeros

def is_prime(p, nchecks, do_trail_division):
    """ signature of http://linux.die.net/man/3/bn_is_prime_fasttest """
    #print(p, nchecks, do_trail_division)
    return pyprimes.miller_rabin(p)

def check_proof_of_work(powhash, compact_bits, delta):
    #if powhash == genesisPoWhash: return True
    target, trailing_zeros = generate_prime_base(powhash, compact_bits)
    if trailing_zeros < 256:
        if delta >= 1 << trailing_zeros:
            raise Exception("candidate larger than allowed")
    target += delta
    if target % 210 != 97:
        raise Exception("not valid pow")

    def check(remaining):
        offset, nchecks_before, nchecks_after = remaining[0]
        if not is_prime(target + offset, nchecks_before, True):
            raise Exception("n+{0} not prime".format(offset))
        if len(remaining) > 1:
            check(remaining[1:])
        if nchecks_after is not None and not is_prime(target + offset, nchecks_after, False):
            raise Exception("n+{0} not prime".format(offset))

    check([(0, 1, 9), (4, 1, 9), (6, 1, 9), (10, 1, 9), (12, 1, 9), (16, 10, None)])
    return True

def main():
    print("reading from stdin...")
    try:
        block = json.loads(sys.stdin.read())
    except ValueError:
        print("Usage: riecoind getblock $(riecoind getblockhash <block number>) | python3 " + sys.argv[0])
        return

    assert set_compact(33869056) == (205) + (4 << 8)
    assert generate_prime_base(int("e2998096fcd2fb5f95f0fc9e1c57400522947db1fb00d88dfbc4c819cc9a4606", 16), 33869056)[1] == 964
    assert check_proof_of_work(
        int.from_bytes(get_hash_for_pow(block), byteorder="big"),
        int(block["bits"], 16),
        int.from_bytes(
            flip(bytes.fromhex(block["nOffset"])),
            byteorder="little"
        )
    )
    print("success!")

if __name__ == "__main__":
    main()
