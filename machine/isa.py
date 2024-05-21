import struct
from enum import Enum

BITS = 32
MIN_SIGN = -(2 ** (BITS - 1))
MAX_SIGN = 2 ** (BITS - 1) - 1
MAX_UNSIGN = 2**BITS - 1

MAP_INPUT_ADDRESS = 0
MAP_OUTPUT_ADDRESS = 1


class ALU(Enum):
    ADD = 0
    SUB = 1
    MOD = 2
    EQ = 3
    OR = 4


class Opcode(Enum):
    # поток программы
    JMP = 0
    JZ = 1
    CALL = 2
    RET = 3
    HLT = 4

    # Работа со стеком
    GET_VAL = 10
    STORE_VAL = 11
    PEEK = 12
    PUSH = 13
    DROP = 14
    PUSHR = 15
    DROPR = 16

    # Арифметика
    ADD = 20
    SUB = 21
    MOD = 22
    EQ = 23
    OR = 24


def write_code(target: str, code: list[int]):
    with open(target, "wb") as f:
        f.write(struct.pack(f"{len(code)}I", *code))


def read_code(source: str) -> list[int]:
    code = []
    BYTES = BITS // 8
    with open(source, "rb") as f:
        short = f.read(BYTES)
        while short:
            code.append(*struct.unpack("I", short))
            short = f.read(BYTES)

    return code
