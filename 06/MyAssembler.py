import sys

class Parser:
    def __init__(self):
        self.symbolTable = {
            "SCREEN": 16384,
            "KBD": 24576,
            "SP": 0,
            "LCL": 1,
            "ARG": 2,
            "THIS": 3,
            "THAT": 4
        }
        for i in range(0, 16):
            self.symbolTable["R" + str(i)] = i

        self.compTable = {
            "0":    "0101010",
            "1":    "0111111",
            "-1":   "0111010",
            "D":    "0001100",
            "A":    "0110000",
            "M":    "1110000",  
            "!D":   "0001101",
            "!A":   "0110001",  
            "!M":   "1110001",
            "-D":   "0001111",
            "-A":   "0110011",
            "-M":   "1110011",
            "D+1":  "0011111",
            "A+1":  "0110111",
            "M+1":  "1110111",
            "D-1":  "0001110",
            "A-1":  "0110010",
            "M-1":  "1110010",
            "D+A":  "0000010",
            "D+M":  "1000010",
            "D-A":  "0010011",
            "D-M":  "1010011",
            "A-D":  "0000111",
            "M-D":  "1000111",
            "D&A":  "0000000",
            "D&M":  "1000000",
            "D|A":  "0010101",
            "D|M":  "1010101"
        }
        self.jumpTable = {
            "": "000",
            "JGT": "001",
            "JEQ": "010",
            "JGE": "011",
            "JLT": "100",
            "JNE": "101",
            "JLE": "110",
            "JMP": "111"
        }
        self.destTable = {
            "": "000",
            "M": "001",
            "D": "010",
            "MD": "011",
            "A": "100",
            "AM": "101",
            "AD": "110",
            "AMD": "111"
        }
        

    def __call__(self, file):
        instructions = self.purify(file)
        self.add_labels_to_symboltable(instructions)
        instructionsL = self.replace_symbols(instructions)
        return self.parse(instructionsL)


    def purify(self, file):
        instructions = []
        for line in file:
            removedComments = line.split("//")[0]
            removedWhitespace = removedComments.strip()
            if removedWhitespace != "":
                instructions.append(removedWhitespace)

        return instructions


    def add_labels_to_symboltable(self, instructions):
        i = 0
        while i < len(instructions):
            if instructions[i][0] == '(':
                line = instructions.pop(i)
                label = line[1:-1]
                self.symbolTable[label] = i
            else:
                i += 1


    def replace_symbols(self, instructions):
        regPointer = 16

        def f(instruction):
            nonlocal regPointer

            if instruction[0] != '@':
                return instruction
            else:
                symbolCandidate = instruction[1:]
                if symbolCandidate.isnumeric():
                    return instruction
                else:
                    symbolvalue = self.symbolTable.get(symbolCandidate)
                    if symbolvalue == None:
                        self.symbolTable[symbolCandidate] = symbolvalue = regPointer
                        regPointer += 1
                    return "@" + str(symbolvalue)      

        return map(f, instructions)


    def ainstruction(self, inst):
        num = int(inst[1:])
        bin = int_to_binstring(num)
        return bin.rjust(16, '0')


    def cinstruction(self, inst):
        dest = ""
        jump = ""
        if '=' in inst:
            [dest, inst] = inst.split('=')

        if ';' in inst:
            [inst, jump] = inst.split(';')

        comp = inst

        return "111" + self.compTable[comp] + self.destTable[dest] + self.jumpTable[jump]


    def parse(self, instructions):
        binary = ""
        for i, inst in enumerate(instructions):
            binary += self.ainstruction(inst) if inst[0] == '@' else self.cinstruction(inst)
            binary += '\n'

        return binary



def int_to_binstring(num):
    return int_to_binstring(num >> 1) + str(num % 2) if num > 1 else str(num)


def main():
    filePath = sys.argv[1]
    if not filePath:
        filePath = input("Please enter the path to the file you want to assemble")

    with open(filePath, "r") as file:
        parser = Parser()
        hack_binary = parser(file)

    with open(filePath.replace('.asm', '.hack'), "w+") as file:
        file.write(hack_binary)


if __name__ == "__main__":
    main()