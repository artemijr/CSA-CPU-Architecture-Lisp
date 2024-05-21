import contextlib
import io
import logging
import os
import tempfile

import pytest

import simulation
import translator
from machine.isa import read_code


@pytest.mark.golden_test("tests/*.yml")
def test_translator_asm_and_machine(golden, caplog):
    caplog.set_level(logging.DEBUG)

    STACK_SIZE = 10
    DEBUG_LIMIT = 200
    LIMIT = 100000

    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source.lisp")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target.o")
        target_mnem = os.path.join(tmpdirname, "target.o.mnem")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target, target_mnem)
            print("============================================================")
            simulation.main(target, input_stream, STACK_SIZE, DEBUG_LIMIT, LIMIT)

        code = read_code(target)
        with open(target_mnem, "r") as f:
            mnemonics = f.read()

        assert mnemonics == golden.out["out_mnemonics"]
        assert code == golden.out["out_code"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert caplog.text == golden.out["out_log"]
