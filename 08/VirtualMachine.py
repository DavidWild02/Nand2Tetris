import sys
import os


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
        line = self.input[self.currentLine]
        remWhite = line.split("//")[0].strip()
        self.currentCommand = remWhite.split()
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



def pushD(D=""):
    return D + """
        @SP
        A=M
        M=D
        @SP
        M=M+1
    """

def pushVar(Var):
    return pushD(f"""
        @{Var}
        D=M
    """)


class CodeWriter:
    def __init__(self, outputFile):
        self.output = open(outputFile, "w+")
        self.currentClass = None
        self.currentFunction = None
        self.counter = 0


    def close(self):
        self.output.close()


    def setFileName(self, filename):
        self.currentClass = os.path.basename(filename).split('.')[0]


    def writeInit(self):
        bootstrapCode = """
            @261
            D=A
            @0
            M=D

            @Sys.init
            0;JMP
        """
        self.output.write(bootstrapCode)


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

        translation = ""
        if segment in segmentPointers.keys():
            translation += f"""
                @{index}
                D=A
                @{segmentPointers[segment]}
                A=M
                A=D+A
            """
        elif segment == "constant":
            translation += f"""
                @{index}
            """
        elif segment == "static":
            translation += f"""
                @{self.currentClass}.{index}
            """
        elif segment == "temp":
            translation += f"""
                @{index}
                D=A
                @R5
                A=A+D  
            """
        elif segment == "pointer":
            translation += f"""
                @{ "THIS" if index == "0" else "THAT" }
                """

        if command == C_PUSH:
            translation += pushD(f"""
                {"D=M" if segment != "constant" else "D=A"}
            """)
        elif command == C_POP:
            translation += """
                D=A
                @R13
                M=D

                @SP
                M=M-1
                A=M
                D=M

                @R13
                A=M
                M=D
            """


        self.output.write(translation)


    def writeLabel(self, label):
        self.output.write(f"""
            ({self.currentFunction}${label})
        """)


    def writeGoto(self, label):
        self.output.write(f"""
            @{self.currentFunction}${label}
            0;JMP
        """)


    def writeIf(self, label):
        # cond is true, if its != zero
        self.output.write(f"""
            @SP
            M=M-1
            A=M
            D=M
            @{self.currentFunction}${label}
            D;JNE
        """)


    def writeFunction(self, functionName, nVars):
        self.currentFunction = functionName
        translation = f"""
            ({functionName})
        """
        for i in range(int(nVars)):
            translation += pushD("""
                @0
                D=A
            """)

        self.output.write(translation)


    def writeCall(self, functionName, nArgs):
        returnAddress = f"{self.currentFunction}$ret.{self.counter}"
        translation = pushD(f"""
            @{returnAddress}
            D=A
        """)
        self.counter += 1

        translation += pushVar("LCL") + pushVar("ARG") + pushVar("THIS") + pushVar("THAT")
        translation += f"""
            @SP
            D=M
            @LCL
            M=D

            @5
            D=D-A
            @{nArgs}
            D=D-A
            @ARG
            M=D

            @{functionName}
            0;JMP

            ({returnAddress})
        """

        self.output.write(translation)


    def writeReturn(self):
        # R13 is the endFrame, R14 the return address
        translation = """
            @LCL
            D=M
            @R13
            M=D

            @5
            A=D-A
            D=M
            @R14
            M=D

            @SP
            M=M-1
            A=M
            D=M
            @ARG
            A=M
            M=D

            D=A
            @SP
            M=D+1
        """
        for var in ["THAT", "THIS", "ARG", "LCL"]:
            translation += f"""
                @R13
                M=M-1
                A=M
                D=M
                @{var}
                M=D
            """
        translation += """
            @R14
            A=M
            0;JMP
        """

        self.output.write(translation)



def main():
    input = sys.argv[1]

    def parseWriteLogic(file, codeWriter):
        parser = Parser(file)
        codeWriter.setFileName(file)

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
                codeWriter.writeFunction(arg1, arg2)
            elif commandType == C_CALL:
                codeWriter.writeCall(arg1, arg2)
            elif commandType == C_RETURN:
                codeWriter.writeReturn()


    if os.path.isfile(input):
        output = input.replace(".vm", ".asm")
        codeWriter = CodeWriter(output)
        parseWriteLogic(input, codeWriter)    
    elif os.path.isdir(input):
        output = os.path.join(input, os.path.basename(input) + ".asm")
        files = [os.path.join(input, file) for file in os.listdir(input) if file.endswith(".vm")]
        codeWriter = CodeWriter(output)

        codeWriter.writeInit()
        for file in files:
            parseWriteLogic(file, codeWriter)
    else:
        raise Exception("argv[1] is neither a dir nor a file")

    codeWriter.close()


if __name__ == "__main__":
    main()