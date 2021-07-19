import sys


C_ARITHMETIC    = "C_ARITHMETIC"
C_PUSH          = "C_PUSH"
C_POP           = "C_POP"
C_LABEL         = "C_LABEL"
C_GOTO          = "C_GOTO"
C_IF            = "C_IF"
C_FUNCTION      = "C_FUNCTION"
C_RETURN        = "C_RETURN"
C_CALL          = "C_CALL"


class Parser:
    def __init__(self, inputFile):
        with open(inputFile, "r") as file:
            self.input = file.readlines()
        self.currentLine = 0
        self.currentCommand = None
        
    
    def advance(self):
        self.currentCommand = self.input[self.currentLine].split()
        self.currentLine += 1


    def hasMoreCommands(self):
        while self.currentLine < len(self.input):
            candidate = self.input[self.currentLine]
            candidate = candidate.split("//")[0].strip()
            if candidate != "":
                return True
            self.currentLine += 1
        
        return False


    def commandType(self):
        switch = {
            "add":      C_ARITHMETIC,
            "sub":      C_ARITHMETIC,
            "neg":      C_ARITHMETIC,
            "eq":       C_ARITHMETIC,
            "gt":       C_ARITHMETIC,
            "lt":       C_ARITHMETIC,
            "and":      C_ARITHMETIC,
            "or":       C_ARITHMETIC,
            "not":      C_ARITHMETIC,
            "push":     C_PUSH,
            "pop":      C_POP,
            "label":    C_LABEL,
            "goto":     C_GOTO,
            "if-goto":  C_IF,
            "function": C_FUNCTION,
            "call":     C_CALL,
            "return":   C_RETURN
        }

        return switch[self.currentCommand[0]]


    def arg1(self):
        return self.currentCommand[1] if len(self.currentCommand) >= 2 else None


    def arg2(self):
        return self.currentCommand[2] if len(self.currentCommand) == 3 else None



class CodeWriter:
    def __init__(self, outputFile):
        self.output = open(outputFile, "w+")
        self.currentClass = None
        self.counter = 0


    def close(self):
        self.output.close()


    def setFileName(self, filename):
        pass


    def writeInit(self):
        pass


    def writeArithmetic(self, command):
        # if 2 args are given this is in fact y else it is x, because of the code below
        translation = """
            @SP
            M=M-1
            A=M
        """

        # if 2 args are needed
        if not command in ["not", "neg"]:
            # get y and save it in D, then get x
            translation += """
                D=M

                @SP
                M=M-1
                A=M
            """

        if command == "add":
            translation += "M=M+D\n"
        elif command == "sub":
            translation += "M=M-D\n"
        elif command == "neg":
            translation += "M=-M\n"
        elif command in ["eq", "gt", "lt"]:
            cond = command.upper()
            label =  cond + "." + str(self.counter)
            self.counter += 1
            translation += f"""
                A=M
                D=A-D
                @{label}
                D;J{cond}

                @SP
                A=M
                M=0
                @NOT_{label}
                0;JMP

                ({label})
                @SP
                A=M
                M=-1

                (NOT_{label})
            """
        elif command == "or":
            translation += "M=M|D\n"
        elif command == "and":
            translation += "M=M&D\n"
        elif command == "not":
            translation += "M=!M\n"

        translation += """
            @SP
            M=M+1
        """
        self.output.write(translation)


    def writePushPop(self, command, segment, index):
        segmentPointers = {
            "local": "LCL",
            "argument": "ARG",
            "this": "THIS", 
            "that": "THAT"
        }

        def get_addr(seg, i):
            nonlocal segmentPointers

            if seg in segmentPointers.keys():
                return f"""
                    @{i}
                    D=A
                    @{segmentPointers[seg]}
                    A=M
                    A=D+A
                """
            elif seg == "constant":
                return f"""
                    @{i}
                """
            elif seg == "static":
                return f"""
                    @{self.currentClass}.{i}
                """
            elif seg == "temp":
                return f"""
                    @{i}
                    D=A
                    @R5
                    A=A+D  
                """
            elif seg == "pointer":
                return f"""
                    @{ "THIS" if i == "0" else "THAT" }
                """


        translation = ""
        if command == C_PUSH:
            translation += get_addr(segment, index)
            translation += f"""
                {"D=M" if segment != "constant" else "D=A"}
                @SP
                A=M
                M=D

                @SP
                M=M+1
            """
        elif command == C_POP:
            translation += get_addr(segment, index)
            translation += """
                D=A
                @R13
                M=D
            """
            translation += f"""
                @SP
                M=M-1

                A=M
                D=M
            """
            translation += f"""
                @R13
                A=M
                M=D
            """

        self.output.write(translation)


    def writeLabel(self, label):
        pass


    def writeGoto(self, label):
        pass


    def writeIf(self, label):
        pass


    def writeFunction(self, functionName, nVars):
        pass


    def writeCall(self, functionName, nArgs):
        pass


    def writeReturn(self):
        pass



def main():
    input = sys.argv[1]
    parser = Parser(input)
    codeWriter = CodeWriter(input.replace(".vm", ".asm"))

    while parser.hasMoreCommands():
        parser.advance()
        commandType = parser.commandType()
        arg1 = parser.arg1()
        arg2 = parser.arg2()

        if commandType in [C_PUSH, C_POP]:
            codeWriter.writePushPop(commandType, arg1, arg2)
        elif commandType ==  C_ARITHMETIC:
            codeWriter.writeArithmetic(parser.currentCommand[0])
        elif commandType == C_LABEL:
            codeWriter.writeLabel(arg1)
        elif commandType == C_GOTO:
            codeWriter.writeGoto(arg1)
        elif commandType == C_IF:
            codeWriter.writeIf(arg1)
        elif commandType == C_FUNCTION:
            codeWriter(arg1, arg2)
        elif commandType == C_CALL:
            codeWriter.writeCall(arg1, arg2)
        elif commandType == C_RETURN:
            codeWriter.writeReturn()

    codeWriter.close()


if __name__ == "__main__":
    main()