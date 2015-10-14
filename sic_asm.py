#! /usr/bin/env python

from json import load
from sys import argv


class SicAsm:
    """
    An ultra-simple, barebones assembler for the SIC machine

    USAGE
    $ ./sic_asm input_file

    OR...

    >>> from sic_asm import SicAsm
    >>> m = SicAsm()
    >>> m.assemble(source_input_file, object_output_file)

    """
    def __init__(self):
        # list all the important variables used

        self.optab = load(open('instr_set'))
        self.symtab = {}

        self.ip = None
        self.op = None

        self.label = None
        self.addr = None
        self.opcode = None
        self.operand = None
        self.errors = []

        self.startaddress = 0
        self.locctr = 0

        self.prog_length = 0
        self.prog_valid = True
        self.prog_name = None
        self.prog_length = 0
        self.prog_start_str = None

        # place holder values are...
        # START = start address
        # LN = length of current text record
        self.cur_text_rec = ["T", "START ", "LN"]
        self.cur_text_len = 0

        # this is the intermediate data structure
        # this list contains many other lists
        # each nested list represts one line of orignal source code
        # each nested list has 5 elements:
        # 1. addrss, label, opcode, operand, errors(list)
        self.parsed = []
        self.parsed_iter = None

    # ============== PASS1 FUNCTIONS =================

    def read_next_line(self):
        """
        read next line from input/source file
        """
        self.label = None
        self.opcode = None
        self.operand = None
        self.errors = []

        line = self.ip.readline().upper()
        if line.startswith('.'):
            # this is a comment line
            self.opcode = "COMMENT"
            self.operand = line.strip()
        elif line.startswith(' '):
            # no label present in this line
            line = line.strip().split()
            self.opcode = line[0]
            if len(line) >= 2:
                self.operand = line[1]
        else:
            # label is present in this line
            line = line.strip().split()
            self.label = line[0]
            self.opcode = line[1]
            if len(line) >= 3:
                self.operand = line[2]

    def write_locctr(self):
        """
        create a new list in intermediate with locctr
        """
        locctr_str = format(self.locctr, '04X')
        # we are CREATING a new list in intermediate
        self.parsed.append([locctr_str])

    def write_line(self):
        """
        populate newly created record/list in intermediate
        """
        parsed_line = []
        # convert locctr to uppercase hex with atleast 4 digits
        if self.opcode != "COMMENT":
            if not self.label:
                self.label = "~"
            parsed_line.append(self.label)

            parsed_line.append(self.opcode)

            if not self.operand:
                self.operand = "~"

            parsed_line.append(self.operand)

            parsed_line.append(self.errors)
        else:
            self.parsed.append([])
            parsed_line.append(self.operand)

        self.parsed[-1].extend(parsed_line)

        if self.errors:
            self.prog_valid = False

    def bytelen(self, operand):
        """
        if X'F1' then it's 1B long,
        if C'EOF' then it's 3B long.

        handle those two kinds of notations.
        """
        if operand.startswith('X'):
            return (len(operand) - 3)/2
        if operand.startswith('C'):
            return len(operand) - 3

    def pass1(self):
        """
        textbook pseudocode translated to python
        """
        self.read_next_line()
        if self.opcode == 'START':
            if self.operand:
                self.locctr = int(self.operand, base=16)
                self.startaddress = self.locctr

            self.prog_name = self.label

            self.write_locctr()
            self.write_line()

            # The next line we will read will be the first one
            self.read_next_line()

        while self.opcode != "END":
            if self.opcode != 'COMMENT':
                self.write_locctr()
                if self.label:
                    if self.label in self.symtab:
                        self.errors.append("Duplicate symbol " + self.label)
                    else:
                        self.symtab[self.label] = self.locctr
                if self.opcode in self.optab:
                    self.locctr += 3
                elif self.opcode == 'WORD':
                    self.locctr += 3
                elif self.opcode == 'RESW':
                    self.locctr += (3 * int(self.operand))
                elif self.opcode == 'RESB':
                    self.locctr += int(self.operand)
                elif self.opcode == 'BYTE':
                    self.locctr += self.bytelen(self.operand)
                else:
                    self.errors.append("Invalid operation code " + self.opcode)

            self.write_line()
            self.read_next_line()

        self.write_locctr()
        self.write_line()

        self.prog_length = self.locctr - self.startaddress

        self.ip.close()

    # ==================== PASS2 FUNCTIONS ==================

    def reinit_text_rec(self):
        """
        create a new text record in object code
        """
        self.cur_text_rec = ["T", "START ", "LN"]
        self.cur_text_len = 0

    def read_next_line_from_int(self):
        """
        This function works correctly, but it is not needed
        in this version of the program. The current version
        doesn't require the intermediate file at all -- it
        uses internal data structures instead. I have kept
        this function intact for the purpose of study.
        """

        self.label = None
        self.opcode = None
        self.operand = None
        self.errors = []

        line = self.ip.readline().strip()
        if line.startswith('.'):
            # this is a comment line
            self.opcode = "COMMENT"
            return
        elif line.startswith(' '):
            return

        line = line.upper().split()

        self.addr = int(line[0], base=16)
        self.label = line[1]
        self.opcode = line[2]
        self.operand = line[3]

        print "{:04X}  {:10s}  {:10s}  {:10s}".format(
                self.addr, self.label, self.opcode, self.operand),

    def write_header(self):
        """
        write the first line of object code
        """
        temp = ["H"]
        temp.append("{:6s}".format(self.label))  # prog name
        self.prog_start_str = "{:>06s}".format(self.operand)
        temp.append(self.prog_start_str)  # start address
        temp.append("{:06x}".format(self.prog_length))  # prog length

        self.op.write('^'.join(temp) + "\n")
        return

    def write_txt_rec(self):
        """
        format current text record and then write it
        """
        self.cur_text_rec[2] = format(self.cur_text_len/2, '02X')
        self.op.write('^'.join(self.cur_text_rec) + "\n")

    def write_end(self):
        """
        write last line of object code
        """
        temp = ["E", self.prog_start_str]
        self.op.write('^'.join(temp) + "\n")

    def read_intermediate(self):
        """
        read the intermediate data structure called "parsed"
        to read from an actual intermediate file, please use:

                read_next_line_from_int(self):
        """
        self.label = None
        self.opcode = None
        self.operand = None
        self.errors = []

        tmp = self.parsed_iter.next()
        if tmp[0].startswith('.'):
            self.opcode = "COMMENT"
            return
        else:
            self.addr, self.label, self.opcode, self.operand, _ = tmp
            self.addr = int(self.addr, base=16)

        print "{:04X}  {:10s}  {:10s}  {:10s}".format(
                self.addr, self.label, self.opcode, self.operand),

    def pass2(self):
        """
        modified pass2 of textbook algorithm
        """

        self.parsed_iter = iter(self.parsed)
        self.read_intermediate()
        print

        self.write_header()

        # start address of first record
        self.cur_text_rec[1] = "{:>06s}".format(self.operand)

        while True:
            # self.read_next_line_from_int()
            self.read_intermediate()

            if self.opcode == "END":
                self.write_txt_rec()
                self.write_end()
                break

            # ignore comment lines
            if self.opcode == "COMMENT":
                continue

            # set the start address of a new record
            if len(self.cur_text_rec) == 3:
                # start address of new record
                self.cur_text_rec[1] = "{:>06X}".format(self.addr)

            # assemble the instruction to hex
            opcode_hex = ""
            if self.opcode in self.optab:
                opcode_hex = self.optab[self.opcode][0]

                # RSUB has no operand, so set operand = 0
                if self.operand == "~":
                    opcode_hex += '0000'
                # handle indexed addressing mode
                elif self.operand.find(',X') != -1:
                    target_label_addr = int(
                            self.symtab[self.operand.split(',')[0]])
                    # the assembled instruction for indexed mode looks
                    # like this:
                    #           AAAA AAAA 1BBB BBBB BBBB BBBB BBBB
                    # to get the assembled hex value we do:
                    # 1. convert label address to 15bit binary number (BBBB...)
                    # 2. prepend it with a "1" indicating indexed addressing
                    # 3. convert the resulting binary number to hex
                    opcode_hex += format(
                            int("1" + format(
                                target_label_addr, '015b'), base=2), '04X')
                else:
                    # simple addressing is... well, simple
                    opcode_hex += format(int(self.symtab[self.operand]), '04X')
            elif self.opcode == 'BYTE':
                # get the character string in temp
                temp = self.operand.split("'")[1]
                if self.operand.startswith('C'):
                    # convert chars to equivalent byte values
                    for c in temp:
                        opcode_hex += format(ord(c), '02X')
                    # if the string is hex, then add it as it is
                elif self.operand.startswith('X'):
                    opcode_hex += temp
            elif self.opcode == 'WORD':
                opcode_hex = format(int(self.operand), '06X')
            elif self.opcode == 'RESW' or self.opcode == 'RESB':
                # RESW and RESB allocate space
                # by allocate we mean it's left "empty"
                # all we have to do is, end the current record
                # and reinitialize a new record to insert
                # the necessary blanks
                print
                if len(self.cur_text_rec) > 3:
                    self.write_txt_rec()
                    self.reinit_text_rec()
                continue

            # side by side listing of address, assembly and object code
            print "  {:10s}".format(str(opcode_hex))

            # will the current instruction fit into the current record?
            if self.cur_text_len + len(str(opcode_hex)) <= 60:
                # yes, it will
                self.cur_text_rec.append(str(opcode_hex))
                self.cur_text_len += len(str(opcode_hex))
            else:
                # no, it will not, so finish current rec...
                self.write_txt_rec()
                # ...and start a new one
                self.reinit_text_rec()
                # start address of new record
                self.cur_text_rec[1] = "{:>06X}".format(self.addr)
                self.cur_text_rec.append(str(opcode_hex))
                self.cur_text_len += len(str(opcode_hex))

        self.op.close()
        self.ip.close()

    def assemble(self, source_file, dest_file):
        """
        take filenames, do operations in the right sequence, etc.
        a simple handler function.
        """
        self.ip = open(source_file)

        self.pass1()
        self.write_intermediate_file()

        if self.prog_valid:
            self.op = open(dest_file, "w")
            self.pass2()
        else:
            print "Invalid assembly program."
            print "Check intermediate.txt for details."

    def write_intermediate_file(self, int_file="intermediate.txt"):
        """
        once pass1 is done, if required, write some intermediate data
        for reference.
        """

        self.op = open("intermediate.txt", "w")

        self.parsed_iter = iter(self.parsed)
        print
        print
        for line in self.parsed_iter:
            if line[0].startswith('.'):
                self.op.write(line[0] + "\n")
                continue

            for item in line[:-1]:
                self.op.write(item.ljust(10))

            # there are errors?
            if line[-1]:
                for item in line[-1]:
                    self.op.write(item + " | ")

            self.op.write("\n")


if __name__ == "__main__":
    machine = SicAsm()
    if len(argv) == 3:
        machine.assemble(argv[1], argv[2])
    elif len(argv) == 2:
        machine.assemble(argv[1], "out.txt")
    else:
        print
        print
        print "\t%s input_file # output in out.txt" % argv[0]
        print
        print
        print "\t\t\tor..."
        print
        print
        print "\t%s input_file output_file" % argv[0]
        print
        print
