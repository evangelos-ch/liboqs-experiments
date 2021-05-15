from time import process_time_ns

from cryptography.hazmat.primitives.asymmetric import ec

# Recommended curves from https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-4.pdf
CURVE_MAP = {
    'P-192': ec.SECP192R1(),
    'P-224': ec.SECP224R1(),
    'P-256': ec.SECP256R1(),
    'P-384': ec.SECP384R1()
}

def current_milli_time():
    return process_time_ns()
