import logging

from machine.isa import ALU, MAX_SIGN, MAP_INPUT_ADDRESS, MAP_OUTPUT_ADDRESS, MIN_SIGN


class Datapath:
    data: list = None
    data_address: int = None
    stack_size: int = None
    stack: list = None
    stack_pointer: int = None

    input_buffer: list = None
    output_buffer: list = None

    def __init__(self, data: list, stack_size: int, input_buffer: list):
        self.data = data
        self.data_address = 0
        self.stack_size = stack_size
        self.stack = [-1] * stack_size
        self.stack_pointer = -1
        self.input_buffer = input_buffer
        self.output_buffer = []

    def signal_latch_data_address(self, val: int):
        self.data_address = val

    def signal_latch_stack_pointer(self, val: int):
        self.stack_pointer = val

    def signal_latch_stack_top(self, val):
        self.stack[self.stack_pointer] = val

    def signal_latch_stack_second(self, val):
        self.stack[self.stack_pointer - 1] = val

    def alu_operation(self, operation: ALU, left: int, right: int):
        if operation == ALU.ADD:
            res = left + right
        elif operation == ALU.SUB:
            res = left - right
        elif operation == ALU.MOD:
            res = left % right
        elif operation == ALU.EQ:
            res = 1 if left == right else 0
        elif operation == ALU.OR:
            res = 1 if left or right else 0
        else:
            raise ValueError(f"Operation {operation} not supported")

        if res < MIN_SIGN:
            res += MAX_SIGN - 1
        if res > MAX_SIGN:
            res -= MAX_SIGN + 1
        return res

    def get_tos(self):
        return self.stack[self.stack_pointer]

    def get_sos(self):
        return self.stack[self.stack_pointer - 1]

    def get_data(self):
        addr = self.data_address
        if addr == MAP_INPUT_ADDRESS:
            return self._signal_input()
        return self.data[addr]

    def set_data(self, val: int):
        addr = self.data_address
        if addr == MAP_OUTPUT_ADDRESS:
            self._signal_output(val)
        else:
            self.data[addr] = val

    def _signal_input(self):
        if len(self.input_buffer) == 0:
            raise EOFError("End of input file")
        ord_char = self.input_buffer.pop(0)
        if ord_char == 0:
            symbol = ""
        else:
            symbol = chr(ord_char)
        logging.debug(f"input: {symbol}")
        return ord_char

    def _signal_output(self, ord_char: int):
        symbol = "" if ord_char == 0 else chr(ord_char)
        self.output_buffer.append(ord_char)
        logging.debug(
            f"output: {''.join(map(lambda x: chr(x) if 0 < x < 256 else str(x), self.output_buffer))} << {symbol}"
        )
        pass

    def zero(self):
        return self.stack[self.stack_pointer] == 0
