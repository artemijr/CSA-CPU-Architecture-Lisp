from machine.datapath import Datapath
from machine.isa import Opcode, ALU


class ControlUnit:
    program: list = None
    program_counter: int = None
    return_stack_size: int = None
    return_stack: list = None
    return_stack_pointer: int = None

    instruction: int = None

    datapath: Datapath = None

    _tick: int = None

    def __init__(self, code: list, start: int, stack_size: int, datapath: Datapath):
        self.program = code
        self.program_counter = start
        self.return_stack_size = stack_size
        self.return_stack = [-1] * stack_size
        self.return_stack_pointer = -1
        self.instruction_register = 0
        self.datapath = datapath
        self._tick = 0

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def signal_latch_program_counter(self, val: int):
        self.program_counter = val

    def signal_latch_return_stack_pointer(self, val: int):
        self.return_stack_pointer = val

    def signal_latch_rstack_top(self, val: int):
        self.return_stack[self.return_stack_pointer] = val

    def signal_latch_instruction_register(self, val: int):
        self.instruction_register = val

    def get_instr(self):
        return self.program[self.program_counter]

    def get_rtos(self):
        return self.return_stack[self.return_stack_pointer]

    def decode_and_execute_control_flow_instruction(self, opcode):
        if opcode is Opcode.HLT:
            raise StopIteration("ABOBA")
        elif opcode is Opcode.JMP:
            self.signal_latch_program_counter(self.get_instr())
            self.tick()
        elif opcode is Opcode.JZ:
            if self.datapath.zero():
                self.signal_latch_program_counter(self.get_instr())
            else:
                self.signal_latch_program_counter(self.program_counter + 1)
            self.datapath.signal_latch_stack_pointer(self.datapath.stack_pointer - 1)
            self.tick()
        elif opcode is Opcode.CALL:
            self.signal_latch_return_stack_pointer(self.return_stack_pointer + 1)
            self.tick()
            self.signal_latch_rstack_top(self.program_counter + 1)
            self.signal_latch_program_counter(self.get_instr())
            self.tick()
        elif opcode is Opcode.RET:
            self.signal_latch_program_counter(self.get_rtos())
            self.signal_latch_return_stack_pointer(self.return_stack_pointer - 1)
            self.tick()
        else:
            return False
        return True

    def decode_and_execute_instruction(self):
        instr = self.get_instr()
        opcode = Opcode(instr)
        self.signal_latch_instruction_register(instr)
        self.signal_latch_program_counter(self.program_counter + 1)
        self.tick()

        # print(instr, opcode, self.program)

        if self.decode_and_execute_control_flow_instruction(opcode):
            return

        if opcode is Opcode.GET_VAL:
            self.datapath.signal_latch_data_address(self.datapath.get_tos())
            self.tick()
            self.datapath.signal_latch_stack_top(self.datapath.get_data())
        elif opcode is Opcode.STORE_VAL:
            self.datapath.signal_latch_data_address(self.datapath.get_sos())
            self.tick()
            self.datapath.set_data(self.datapath.get_tos())
            self.datapath.signal_latch_stack_pointer(self.datapath.stack_pointer - 2)
        elif opcode is Opcode.PEEK:
            self.datapath.signal_latch_stack_pointer(self.datapath.stack_pointer + 1)
            self.tick()
            self.datapath.signal_latch_stack_top(
                self.return_stack[self.return_stack_pointer - self.get_instr()]
            )
            self.signal_latch_program_counter(self.program_counter + 1)
        elif opcode is Opcode.PUSH:
            self.datapath.signal_latch_stack_pointer(self.datapath.stack_pointer + 1)
            self.tick()
            self.datapath.signal_latch_stack_top(self.get_instr())
            self.signal_latch_program_counter(self.program_counter + 1)
        elif opcode is Opcode.DROP:
            self.datapath.signal_latch_stack_pointer(self.datapath.stack_pointer - 1)
        elif opcode is Opcode.PUSHR:
            self.signal_latch_return_stack_pointer(self.return_stack_pointer + 1)
            self.tick()
            self.signal_latch_rstack_top(self.get_instr())
            self.signal_latch_program_counter(self.program_counter + 1)
        elif opcode is Opcode.DROPR:
            self.signal_latch_return_stack_pointer(self.return_stack_pointer - 1)
        elif opcode is Opcode.ADD:
            res = self.datapath.alu_operation(
                ALU.ADD, self.datapath.get_sos(), self.datapath.get_tos()
            )
            self.datapath.signal_latch_stack_second(res)
            self.datapath.signal_latch_stack_pointer(self.datapath.stack_pointer - 1)
        elif opcode is Opcode.SUB:
            res = self.datapath.alu_operation(
                ALU.SUB, self.datapath.get_sos(), self.datapath.get_tos()
            )
            self.datapath.signal_latch_stack_second(res)
            self.datapath.signal_latch_stack_pointer(self.datapath.stack_pointer - 1)
        elif opcode is Opcode.MOD:
            res = self.datapath.alu_operation(
                ALU.MOD, self.datapath.get_sos(), self.datapath.get_tos()
            )
            self.datapath.signal_latch_stack_second(res)
            self.datapath.signal_latch_stack_pointer(self.datapath.stack_pointer - 1)
        elif opcode is Opcode.EQ:
            res = self.datapath.alu_operation(
                ALU.EQ, self.datapath.get_sos(), self.datapath.get_tos()
            )
            self.datapath.signal_latch_stack_second(res)
            self.datapath.signal_latch_stack_pointer(self.datapath.stack_pointer - 1)
        elif opcode is Opcode.OR:
            res = self.datapath.alu_operation(
                ALU.OR, self.datapath.get_sos(), self.datapath.get_tos()
            )
            self.datapath.signal_latch_stack_second(res)
            self.datapath.signal_latch_stack_pointer(self.datapath.stack_pointer - 1)

        self.tick()

    def __repr__(self):
        stack = self.datapath.stack
        tos = stack[self.datapath.stack_pointer]

        opcode = Opcode(self.program[self.program_counter])

        state_repr = (
            f"TICK: {self._tick:4} [{self.program_counter:2}: {opcode.name:10}] "
            f"PC: {self.program_counter:3} "
            f"RSP: {self.return_stack_pointer:2} "
            f"TOS: {tos: 3} "
            f"DA: {self.datapath.data_address:3} "
            f"SP: {self.datapath.stack_pointer:2} "
            f"STACK: {stack[:5]} "
            f"RSTACK: {self.return_stack[:5]} "
        )
        return state_repr
