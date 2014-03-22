#!/usr/bin/env python3

import json, hashlib, pyprimes, sys, time

def sha256(d):
    m = hashlib.sha256()
    m.update(d)
    return m.digest()

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
    b = bytearray(
        block["time"].to_bytes(byteorder="big", length=8)
      + bytes.fromhex(block["bits"])
      + bytes.fromhex(block["merkleroot"])
      + bytes.fromhex(block["previousblockhash"])
      + block["version"].to_bytes(byteorder="big", length=4)
    )
    b.reverse()
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
    size = x >> 24
    size = 3 - size if size <= 3 else size - 3
    return (x & 0x7fffff) >> (size * 8)

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
    return target, trailing_zeros

def is_prime(p, nchecks, do_trail_division):
    """ signature of http://linux.die.net/man/3/bn_is_prime_fasttest """
    #print(p, nchecks, do_trail_division)
    return pyprimes.miller_rabin(p)

FACTORIZE = False #not DONT_CHECK

def check_proof_of_work(pow_hash, compact_bits, delta, DONT_CHECK):
    #if pow_hash == genesis_pow_hash: return True
    target, trailing_zeros = generate_prime_base(pow_hash, compact_bits)
    factorization = []
    copy = target
    if FACTORIZE:
        yield "n = "
        t = time.time()
        for i, j in pyprimes.factorise(target):
             yield "({} ^ {}) * ".format(i,j)
             copy //= i ** j
             factorization.append((i, j))
             if time.time() - t > 3: break
        yield "{} * 2 ^ {} + {}\n".format(copy, trailing_zeros, delta)
    factorization.append((copy, 1))
    factorization.append((2, trailing_zeros))

    target <<= trailing_zeros
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
            yield from check(remaining[1:])
        if nchecks_after is not None and not is_prime(target + offset, nchecks_after, False):
            raise Exception("n+{0} not prime".format(offset))
        yield "n+{0} = {1}\n".format(offset, target + offset)

    constellation = [(0, 1, 9), (4, 1, 9), (6, 1, 9), (10, 1, 9), (12, 1, 9), (16, 10, None)]

    if DONT_CHECK:
        yield [(factorization, delta), [(x[0], target + x[0]) for x in constellation]]
    else:
        yield from check(constellation)
    return True

def get_primes_from_block(block, DONT_CHECK = True):
    yield from check_proof_of_work(
        int.from_bytes(get_hash_for_pow(block), byteorder="big"),
        int(block["bits"], 16),
        int(block["nOffset"], 16),
        DONT_CHECK
    )

def main():
    DONT_CHECK = len(sys.argv) > 1

    if not DONT_CHECK:
        sys.stdout.buffer.write(b"reading from stdin...\n")
        sys.stdout.buffer.flush()
    try:
        block = json.loads(sys.stdin.read())
    except ValueError:
        print("Usage: riecoind getblock $(riecoind getblockhash <block number>) | python3 " + sys.argv[0])
        return

    primes = get_primes_from_block(block, DONT_CHECK)
    for prime in primes:
        sys.stdout.buffer.write(str(prime).encode("utf-8"))
        sys.stdout.buffer.flush()

if __name__ == "__main__":
    main()
