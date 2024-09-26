import argparse

from machine.isa import (
    BITS,
    write_code,
    Opcode,
    MAP_INPUT_ADDRESS,
    MAP_OUTPUT_ADDRESS,
    MIN_SIGN,
    MAX_SIGN,
)


def get_meaningful_token(line: str) -> str:
    return line.split(";", 1)[0].strip()


# превратить текст в последовательность токенов
def translate_stage_1(text: str):
    _vars = []
    variables = {}  # адреса на которые можно ссылаться

    start = 0  # адрес начала программы

    code = []  # токены кода
    data = [0, 0]  # токены данных + для input/output

    # для работы if
    if_counter = 0
    if_from_then = []
    if_to_else = []

    # для работы while
    while_counter = 0
    while_jump = []
    while_jz = []

    # для вызова функций
    stack = []
    to_unstack = 0

    for line in text.splitlines():
        # обрезать комментарии и пробелы
        token = get_meaningful_token(line)
        if token == "":
            continue

        # разделить по пробелам
        parts = token.split(" ")

        for part in parts:
            # начинается со скобки - функция
            if part.startswith("("):
                part = part.strip("(")
                # выделение памяти под число
                if part == "alloc_num":
                    name = parts[1]
                    value = parts[2].strip(")")
                    variables[name] = len(data)
                    data.append(int(value))
                    _vars.append(name)
                    break
                # выделение памяти под строку
                elif part == "alloc_str":
                    name = parts[1]
                    value = " ".join(parts[2:]).strip(")").strip('"')
                    variables[name] = len(data)
                    data.append(len(value))
                    for c in value:
                        data.append(ord(c))
                    _vars.append(name)
                    break
                # выделение памяти под буфер
                elif part == "alloc_buf":
                    name = parts[1]
                    value = parts[2].strip(")")
                    variables[name] = len(data)
                    for i in range(int(value)):
                        data.append(0)
                    _vars.append(name)
                    break
                # объявление функции
                elif part == "def_func":
                    stack.append(part)
                    variables[parts[1]] = len(code)
                    break
                # memory-mapped output заменяется обращением к памяти
                elif part == "output":
                    code.append(Opcode.PUSH)
                    code.append(MAP_OUTPUT_ADDRESS)
                # сохраняем адрес для возврата к началу цикла
                elif part == "while":
                    while_jump.append(len(code))
                elif part == "if":
                    if_from_then.append(f"if_from_then{if_counter}")
                    if_to_else.append(f"if_to_else{if_counter}")
                    if_counter += 1
                stack.append(part)
                continue

            while part.endswith(")"):
                to_unstack += 1
                part = part[:-1]

            # прыжок за цикл
            if part == "do":
                while_jz.append(f"while_after{while_counter}")
                while_counter += 1
                code.append(Opcode.JZ)
                code.append(while_jz[-1])
                continue
            elif part == "then":
                code.append(Opcode.JZ)
                code.append(if_to_else[-1])
                continue
            elif part == "else":
                code.append(Opcode.JMP)
                code.append(if_from_then[-1])
                variables[if_to_else.pop()] = len(code)
                continue
            # обращение к параметру функции
            elif part.startswith("$"):
                part = part.strip("$")
                assert part == "1", f"Sorry, only one argument: {part}"
                code.append(Opcode.PEEK)
                code.append(part)
                part = ""

            if part:
                if part.startswith("@"):
                    code.append(Opcode.PUSHR)
                    code.append(part[1:])
                else:
                    code.append(Opcode.PUSH)
                    code.append(part)

            # вызвать функцию - аргументы уже в стеке
            while to_unstack > 0:
                to_unstack -= 1
                unstacked_token = stack.pop()
                # memory-mapped input заменяется обращением к памяти
                if unstacked_token == "input":
                    code.append(Opcode.PUSH)
                    code.append(MAP_INPUT_ADDRESS)
                    code.append(Opcode.GET_VAL)
                    code.append(Opcode.STORE_VAL)
                # memory-mapped output заменяется обращением к памяти
                elif unstacked_token == "output":
                    code.append(Opcode.STORE_VAL)
                # прыжок к началу цикла и определение адреса после цикла
                elif unstacked_token == "while":
                    code.append(Opcode.JMP)
                    code.append(while_jump.pop())
                    variables[while_jz.pop()] = len(code)
                elif unstacked_token == "get_val":
                    code.append(Opcode.GET_VAL)
                elif unstacked_token == "get_by_addr":
                    code.append(Opcode.GET_VAL)
                    code.append(Opcode.GET_VAL)
                elif unstacked_token == "set":
                    code.append(Opcode.STORE_VAL)
                # выйти из функции и дропнуть параметр
                elif unstacked_token == "def_func":
                    code.append(Opcode.RET)
                    start = len(code)
                elif unstacked_token == "+":
                    code.append(Opcode.ADD)
                elif unstacked_token == "-":
                    code.append(Opcode.SUB)
                elif unstacked_token == "%":
                    code.append(Opcode.MOD)
                elif unstacked_token == "=":
                    code.append(Opcode.EQ)
                elif unstacked_token == "if":
                    variables[if_from_then.pop()] = len(code)
                elif unstacked_token == "or":
                    code.append(Opcode.OR)

                # вызов пользовательской функции
                else:
                    code.append(Opcode.CALL)
                    code.append(variables[unstacked_token])
                    code.append(Opcode.DROPR)

    # конец программы
    code.append(Opcode.HLT)

    # прибавить к адресу длину кода инструкций, тк переменные хранятся после инструкций
    for name in _vars:
        variables[name] += len(code)
    return variables, code, data, start


def translate_stage_2(variables: dict, tokens: list):
    code = []
    mnemonics = []
    for ind, token in enumerate(tokens):
        if isinstance(token, Opcode):
            mnemonics.append(f"{ind:02X} - {token.value:08X} - {token}")
            code.append(token.value)
        elif isinstance(token, int):
            assert MIN_SIGN <= token <= MAX_SIGN, f"{BITS}-bit numbers only {token}"
            mnemonics.append(f"{ind:02X} - {token:08X} - Number-value")
            code.append(token)
        elif isinstance(token, str) and token.isnumeric():
            token = int(token)
            assert MIN_SIGN <= token <= MAX_SIGN, f"{BITS}-bit numbers only {token}"
            mnemonics.append(f"{ind:02X} - {token:08X} - Number-value")
            code.append(token)
        else:
            assert token in variables, f"Variable is not defined: {token}"
            mnemonics.append(f"{ind:02X} - {variables[token]:08X} - Address: {token}")
            code.append(variables[token])

    return code, mnemonics


def translate(text: str):
    variables, code, data, start = translate_stage_1(text)
    # print(variables, code, data, start)
    code, mnemonics = translate_stage_2(variables, code)

    return [start] + code + data, mnemonics


def main(source: str, target: str, target_mnem: str = None):
    with open(source, "r") as f:
        text = f.read()

    code, mnemonics = translate(text)

    if target_mnem is not None:
        with open(target_mnem, "w") as f:
            for line in mnemonics:
                f.write(line + "\n")

    write_code(target, code)
    print(
        "LoC:",
        len(text.split("\n")),
        "Instr:",
        len(code),
        "Code bytes:",
        len(code) * BITS // 8,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Трансляция кода")
    parser.add_argument("source_file", help="Имя файла с кодом")
    parser.add_argument("target_file", help="Имя выходного файла")

    args = parser.parse_args()

    MNEMONIC_FILE = args.target_file + ".mnem"

    main(args.source_file, args.target_file, MNEMONIC_FILE)
