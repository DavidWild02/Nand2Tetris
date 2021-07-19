import sys
import os
import re


keywords = ["class", "method", "function", "constructor", "int", "boolean", "char", "void", "var", "static", "field", "let", "do", "if", "else", "while", "return", "true", "false", "null", "this"]
symbols = ['(', ')', '+', '-', '/', '*', '<', '>', '=', '&', '|', '~', ';', '.', ',', '[', ']', '{', '}']
KEYWORD = "keyword"
SYMBOL = "symbol"
IDENTIFIER = "identifier"
INT_CONST = "int_const"
STRING_CONST = "string_const"


def kindToSegment(kind):
    switch = {
        'field': 'this',
        'static': 'static',
        'arg': 'argument',
        'var': 'local'
    }
    return switch[kind]


class Tokenizer:
    def __init__(self, file):
        with open(file, "r") as f:
            unclean = f.read() 
            singleLine = "(\/\/.*)"
            contentOfMultiLine = "((?!\*\/)(.|\n))*"
            multiLine = f"(\/\*{contentOfMultiLine}\*\/)"
            self.text = re.sub(f"{singleLine}|{multiLine}", "", unclean)
        self.currentToken = None
        self.currentPos = 0


    def cc(self):
        return self.text[self.currentPos] if self.currentPos < len(self.text) else None 


    def hasMoreTokens(self):
        remaining = self.text[self.currentPos:]
        return len(remaining.split()) > 0

        
    def advance(self):
        while self.cc().isspace():
            self.currentPos += 1 

        if self.currentPos >= len(self.text):
            raise Exception("EOF")
        
        if self.cc().isnumeric():
            num = 0 
            while self.cc().isnumeric():
                num = num * 10 + int(self.cc())
                self.currentPos += 1
            self.currentToken = [INT_CONST, num]
        elif self.cc().isalpha() or self.cc() == '_':
            name = ""
            while self.cc().isalpha() or self.cc() == '_':
                name += self.cc()
                self.currentPos += 1
            tokenType = KEYWORD if name in keywords else IDENTIFIER
            self.currentToken = [tokenType, name]
        elif self.cc() == '"':
            string = ""
            self.currentPos += 1
            while self.cc() != '"':
                if self.currentPos >= len(self.text):
                    raise Exception('Missing "')
                string += self.cc()
                self.currentPos += 1
            self.currentPos += 1
            self.currentToken = [STRING_CONST, string]
        elif self.cc() in symbols:
            self.currentToken = [SYMBOL, self.cc()]
            self.currentPos += 1
        else:
            raise Exception("Unknown Token")


    def tokenType(self):
        return self.currentToken[0]


    def keyword(self):
        return self.currentToken[1]


    def symbol(self):
        return self.currentToken[1]


    def identifier(self):
        return self.currentToken[1]


    def intVal(self):
        return self.currentToken[1]


    def stringVal(self):
        return self.currentToken[1]



class SymbolTable:
    staticCounter = 0

    def __init__(self):
        self.classScope = {}
        self.subroutineScope = {}
        self.counter = {
            'static': SymbolTable.staticCounter,
            'field': 0,
            'arg': 0,
            'var': 0
        }


    def define(self, name, type, kind):
        self.counter[kind] += 1
        entry = {
            'type': type,
            'kind': kind,
            'index': self.counter[kind]
        }
        if kind in ['static', 'field']:
            self.classScope[name] = entry

            if kind == 'static':
                SymbolTable.staticCounter += 1
        else:
            self.subroutineScope[name] = entry

    
    def flush(self):
        self.subroutineScope = {}
        self.counter['var'] = 0
        self.counter['arg'] = 0


    def varCount(self, kind):
        return self.counter[kind]


    def _helper(self, name, attr):
        if name in self.subroutineScope:
            return self.subroutineScope[name][attr]
        elif name in self.classScope:
            return self.classScope[name][attr]
        else:
            return None


    def kindOf(self, name):
        return self._helper(name, 'kind')


    def typeOf(self, name):
        return self._helper(name, 'type')


    def indexOf(self, name):
        return self._helper(name, 'index')



class VMWriter:
    def __init__(self, output):
        self.output = open(output, "w+")


    def writePush(self, segment, index):
        self.output.write(f"\tpush {segment} {index}\n")


    def writePop(self, segment, index):
        self.output.write(f"\tpop {segment} {index}\n")


    def writeArithmetic(self, command):
        self.output.write(f"\t{command}\n")


    def writeLabel(self, label):
        self.output.write(f"label {label}\n")


    def writeGoto(self, label):
        self.output.write(f"\tgoto {label}\n")


    def writeIf(self, label):
        self.output.write(f"\tif-goto {label}\n")


    def writeCall(self, name, nArgs):
        self.output.write(f"\tcall {name} {nArgs}\n")


    def writeFunction(self, name, nLocals):
        self.output.write(f"function {name} {nLocals}\n")


    def writeReturn(self):
        self.output.write(f"\treturn\n\n")


    def close(self):
        self.output.close()



class ParseTreeNode:
    def __init__(self, value, nodeType, children=[], callingObj=None):
        self.value = value
        self.children = children
        self.nodeType = nodeType
        self.callingObj = callingObj



class CompilationEngine:
    def __init__(self, vmWriter, tokenizer):
        self.tokenizer = tokenizer
        self.output = vmWriter
        self.symbolTable = SymbolTable()

        self.className = None
        self.numLabels = 0
        self.tokenizer.advance()


    def eat(self, expectedToken):
        if self.tokenizer.keyword() == expectedToken or self.tokenizer.symbol() == expectedToken:
            if self.tokenizer.hasMoreTokens():
                self.tokenizer.advance()
            return
        raise Exception("Unexpected Token: " + str(self.tokenizer.keyword()) + " of Type " + self.tokenizer.tokenType() + "\nExpected Token: " + expectedToken)


    def eatType(self, expectedType):
        if self.tokenizer.tokenType() == expectedType:
            value = self.tokenizer.currentToken[1]
            if self.tokenizer.hasMoreTokens():
                self.tokenizer.advance()
            return value
        raise Exception("Unexpected Token: " + self.tokenizer.keyword() + " of Type " + self.tokenizer.tokenType() + "\nExpected Type: " + expectedType)  



#====================== CompileXXX ==========================
    def compileClass(self):
        self.eat('class')
        
        self.className = self.eatType(IDENTIFIER)

        self.eat('{')
        while self.tokenizer.keyword() in ["field", "static"]:
            self.compileClassVarDec()
        while self.tokenizer.keyword() in ["function", "method", "constructor"]:
            self.compileSubroutineDec()
        self.eat('}')


    def compileClassVarDec(self):
        kind = self.tokenizer.keyword()
        if kind == 'static':
            self.eat('static')
        else:
            self.eat('field')

        if self.tokenizer.tokenType() == IDENTIFIER or self.tokenizer.keyword() in ["int", "char", "boolean"]:
            type_ = self.tokenizer.keyword()
            self.tokenizer.advance()
        else:
            raise Exception("Expected an Type, but got instead: " + self.tokenizer.keyword())

        name = self.eatType(IDENTIFIER)  
        self.symbolTable.define(name, type_, kind)

        while self.tokenizer.symbol() == ',':
            self.eat(',')
            name = self.eatType(IDENTIFIER) 
            self.symbolTable.define(name, type_, kind) 
        
        self.eat(';')


    def compileSubroutineDec(self):
        self.symbolTable.flush()

        subroutineType = self.tokenizer.keyword() 
        if subroutineType == 'constructor':
            self.eat('constructor')
        elif subroutineType == 'method':
            self.eat('method')
        elif subroutineType == 'function':
            self.eat('function')

        # type
        if self.tokenizer.tokenType() == IDENTIFIER or self.tokenizer.keyword() in ["int", "char", "boolean", "void"]:
            self.tokenizer.advance()
        else:
            raise Exception("Expected an Type, but got instead: " + self.tokenizer.keyword())

        subroutineName = self.eatType(IDENTIFIER)

        if subroutineType == 'method':
            self.symbolTable.define('this', self.className, 'arg')

        self.eat('(')
        self.compileParameterList()
        self.eat(')')

        self.compileSubroutineBody(subroutineName, subroutineType)
        

    def compileParameterList(self):
        if self.tokenizer.symbol() == ')':
            return

        while True:
            type_ = self.tokenizer.keyword()
            self.tokenizer.advance()
            name = self.eatType(IDENTIFIER)
            self.symbolTable.define(name, type_, 'arg')

            if self.tokenizer.symbol() != ',':
                break
            self.eat(',')  


    def compileSubroutineBody(self, subroutineName, subroutineType):
        self.eat('{')
        while self.tokenizer.keyword() == 'var':
            self.compileVarDec()
        
        nLocals = self.symbolTable.varCount('var')
        self.output.writeFunction(f'{self.className}.{subroutineName}', nLocals)

        if subroutineType == 'constructor':
            spaceToAlloc = self.symbolTable.varCount('field')
            self.output.writePush('constant', spaceToAlloc)
            self.output.writeCall('Memory.alloc', 1)
            self.output.writePop('pointer', 0)
        elif subroutineType == 'method':
            self.output.writePush('argument', 0)
            self.output.writePop('pointer', 0)

        self.compileStatements()
        self.eat('}')


    def compileVarDec(self):
        self.eat('var')

        if self.tokenizer.tokenType() == IDENTIFIER or self.tokenizer.keyword() in ["int", "char", "boolean"]:
            type_ = self.tokenizer.keyword()
            self.tokenizer.advance()
        else:
            raise Exception("Expected an Type, but got instead: " + self.tokenizer.keyword())
        
        while True:
            name = self.eatType(IDENTIFIER)
            self.symbolTable.define(name, type_, 'var')

            if self.tokenizer.symbol() != ',':
                break
            self.eat(',')

        self.eat(';')


    def compileStatements(self):
        while True:
            keyword = self.tokenizer.keyword()
            if keyword == "let":
                self.compileLet()
            elif keyword == "do":
                self.compileDo()
            elif keyword == "if":
                self.compileIf()
            elif keyword == "while":
                self.compileWhile()
            elif keyword == "return":
                self.compileReturn()
            else:
                break


    def compileLet(self):
        self.eat('let')
        name = self.eatType(IDENTIFIER)

        segment = kindToSegment(self.symbolTable.kindOf(name))
        index = self.symbolTable.indexOf(name) - 1

        if self.tokenizer.symbol() == '[':
            self.output.writePush(segment, index)

            self.eat('[')
            self.compileExpression()
            self.eat(']')

            self.output.writeArithmetic('add')

            self.eat('=')
            self.compileExpression()
            self.eat(';')

            self.output.writePop('temp', 0)
            self.output.writePop('pointer', 1)
            self.output.writePush('temp', 0)
            self.output.writePop('that', 0)
        else:
            self.eat('=')
            self.compileExpression()
            self.eat(';')

            self.output.writePop(segment, index)


    def compileIf(self):
        self.eat('if')
        self.eat('(')
        self.compileExpression()
        self.eat(')')

        labelIfFalse = 'IF_FALSE' + str(self.numLabels)
        self.numLabels += 1
        labelEndIf = 'END_IF.' + str(self.numLabels)
        self.numLabels += 1

        self.output.writeArithmetic('not')
        self.output.writeIf(labelIfFalse)

        self.eat('{')
        self.compileStatements()
        self.eat('}')

        if self.tokenizer.keyword() == 'else':
            self.output.writeGoto(labelEndIf)
            self.output.writeLabel(labelIfFalse)

            self.eat('else')
            self.eat('{')
            self.compileStatements()
            self.eat('}')

            self.output.writeLabel(labelEndIf)
        else:
            self.output.writeLabel(labelIfFalse) # if no else, then labelIfFalse has the function of labelEndIf


    def compileWhile(self):
        self.eat('while')

        labelLoop = 'LOOP' + str(self.numLabels)
        self.numLabels += 1
        labelBreak = 'BREAK' + str(self.numLabels)
        self.numLabels += 1
        self.output.writeLabel(labelLoop)

        self.eat('(')
        self.compileExpression()
        self.eat(')')

        self.output.writeArithmetic('not')
        self.output.writeIf(labelBreak)

        self.eat('{')
        self.compileStatements()
        self.eat('}')

        self.output.writeGoto(labelLoop)
        self.output.writeLabel(labelBreak)


    def compileDo(self):
        self.eat('do')

        name = self.eatType(IDENTIFIER)

        funcNode = self.cptFunction(name)
        if funcNode == None:
            raise Exception('This is not a valid, do-statement! expected a function call')

        self.eat(';')

        self.traverseParseTree(funcNode)
        self.output.writePop('temp', 0)


    def compileReturn(self):
        self.eat('return')
        if self.tokenizer.symbol() != ';':
            self.compileExpression()
        else:
            self.output.writePush('constant', 0)

        self.output.writeReturn()
        self.eat(';')


    def compileExpression(self):
        parseTree = self.cptAnd()
        self.traverseParseTree(parseTree)


    # Operator precedence:
    # 1. *, /
    # 2. +, -
    # 3. =, >, <
    # 4. |
    # 5. &
    def helper(self, symbols, func):
        acc = func()
        while self.tokenizer.symbol() in symbols:
            symbol = self.eatType(SYMBOL)
            arg2 = func()
            acc = ParseTreeNode(symbol, SYMBOL, [acc, arg2])
        return acc


    def cptAnd(self):
        return self.helper(['&'], self.cptOr)


    def cptOr(self):
        return self.helper(['|'], self.cptComparision)


    def cptComparision(self):
        return self.helper(['<', '>', '='], self.cptSummand)


    def cptSummand(self):
        return self.helper(['+', '-'], self.cptFactor)


    def cptFactor(self):
        return self.helper(['/', '*'], self.cptUnary)


    def cptUnary(self):
        if self.tokenizer.symbol() in ['-', '~']:
            symbol = '- Unary' if self.eatType(SYMBOL) == '-' else '~'
            return ParseTreeNode(symbol, SYMBOL, [self.cptExpr()])
        return self.cptExpr()


    def cptExpr(self):
        if self.tokenizer.symbol() == '(':
            self.eat('(')
            v = self.cptAnd()
            self.eat(')')
        else:
            v = self.cptTerm()
        return v


    def cptTerm(self):
        if self.tokenizer.tokenType() == STRING_CONST:
            return ParseTreeNode(self.eatType(STRING_CONST), STRING_CONST)
        elif self.tokenizer.tokenType() == INT_CONST:
            return ParseTreeNode(self.eatType(INT_CONST), INT_CONST)
        elif self.tokenizer.symbol() in ['true', 'false', 'null', 'this']:
            return ParseTreeNode(self.eatType(KEYWORD), KEYWORD)
        elif self.tokenizer.tokenType() == IDENTIFIER:
            name = self.eatType(IDENTIFIER)

            if self.tokenizer.symbol() == '[':
                self.eat('[')
                children = [self.cptAnd()]
                self.eat(']')
                return ParseTreeNode(name, 'array', children)   

            funcNode = self.cptFunction(name)

            if funcNode:
                return funcNode
            
            return ParseTreeNode(name, 'variable')
        else:
            raise Exception('No valid Token in Term: ' + self.tokenizer.symbol())


    def cptFunction(self, name):
        if not self.tokenizer.symbol() in ['(', '.']:
            return None

        callingObj = None
        if self.tokenizer.symbol() == '.':
            callingObj =  name
            self.eat('.')
            name = self.eatType(IDENTIFIER)
    
        self.eat('(')
        children = self.cptExpressionList()
        self.eat(')')
    
        return ParseTreeNode(name, 'function', children, callingObj)


    def cptExpressionList(self):
        if self.tokenizer.symbol() == ')':
            return []

        expressions = []
        while True:
            expressions.append(self.cptAnd())
            if self.tokenizer.symbol() != ',':
                break
            self.eat(',')

        return expressions
            

    def traverseParseTree(self, parseTree):
        nodeType = parseTree.nodeType 

        if nodeType != 'function':  
            for child in parseTree.children:
                self.traverseParseTree(child)

        if nodeType == SYMBOL:
            symbol = parseTree.value
            if symbol == '*':
                self.output.writeCall('Math.multiply', 2)
            elif symbol == '/':
                self.output.writeCall('Math.divide', 2)
            else:
                switch = {
                    '+': 'add',
                    '-': 'sub',
                    '=': 'eq',
                    '<': 'lt',
                    '>': 'gt',
                    '|': 'or',
                    '&': 'and',
                    '~': 'not',
                    '- Unary': 'neg'
                }
                command = switch[symbol]
                self.output.writeArithmetic(command)
        elif nodeType == STRING_CONST:
            string = parseTree.value
            self.output.writePush('constant', len(string))
            self.output.writeCall("String.new", 1)
            for c in string:
                self.output.writePush('constant', ord(c))
                self.output.writeCall("String.appendChar", 2)
        elif nodeType == INT_CONST:
            self.output.writePush('constant', parseTree.value)
        elif nodeType == KEYWORD:
            keyword = parseTree.value
            if keyword == 'true':
                self.output.writePush('constant', 1)
            elif keyword in ['false', 'null']:
                self.output.writePush('constant', 0)
            elif keyword == 'this':
                self.output.writePush('pointer', 0)
            else:
                raise Exception('Unknown keyword: ' + keyword)
        elif nodeType == 'variable':
            name = parseTree.value
            kind = self.symbolTable.kindOf(name)
            index = self.symbolTable.indexOf(name) - 1
            self.output.writePush(kindToSegment(kind), index)
        elif nodeType == 'array':
            arrName = parseTree.value
            kind = self.symbolTable.kindOf(arrName)
            index = self.symbolTable.indexOf(arrName) -1
            self.output.writePush(kindToSegment(kind), index)
            self.output.writeArithmetic('add')
            self.output.writePop('pointer', 1)
            self.output.writePush('that', 0)
        elif nodeType == 'function':
            funcName = parseTree.value
            className = None
            callingObj = parseTree.callingObj
            isMethod = True
            if callingObj:
                className = self.symbolTable.typeOf(callingObj)
                if className != None:
                    kind = self.symbolTable.kindOf(callingObj)
                    index = self.symbolTable.indexOf(callingObj) - 1
                    self.output.writePush(kindToSegment(kind), index)
                else:
                    className = callingObj
                    isMethod = False
            else:
                self.output.writePush('pointer', 0)
                className = self.className

            for child in parseTree.children:
                self.traverseParseTree(child)

            nArgs = len(parseTree.children) + int(isMethod)
            self.output.writeCall(f'{className}.{funcName}', nArgs)



def main():
    inputArg = sys.argv[1]

    def compile_(inputfile):
        tokenizer = Tokenizer(inputfile)
        outputfile = inputfile.replace(".jack", ".vm")
        vmWriter = VMWriter(outputfile)
        compilationEngine = CompilationEngine(vmWriter, tokenizer)
        compilationEngine.compileClass()

    if os.path.isfile(inputArg):
        compile_(inputArg)
    elif os.path.isdir(inputArg):
        files = [os.path.join(inputArg, file) for file in os.listdir(inputArg) if file.endswith(".jack")]
        for file in files:
            compile_(file)
    else:
        raise Exception("Input was neither file nor directory")


if __name__ == "__main__":
    main()