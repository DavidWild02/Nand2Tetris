import sys
import os
import re
import functools


keywords = ["class", "method", "function", "constructor", "int", "boolean", "char", "void", "var", "static", "field", "let", "do", "if", "else", "while", "return", "true", "false", "null", "this"]
symbols = ['(', ')', '+', '-', '/', '*', '<', '>', '=', '&', '|', '~', ';', '.', ',', '[', ']', '{', '}']
constants = ["keyword", "symbol", "identifier", "int_const", "string_const"] + keywords
for constant in constants:
    exec(f"{constant.upper()} = '{constant}'")


class Tokenizer:
    def __init__(self, file):
        with open(file, "r") as f:
            unclean = f.read() 
            self.text = re.sub("(\/\/.*)|(\/\*.*\*\/)", "", unclean)
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



class CompilationEngine:
    def __init__(self, outputfile, tokenizer):
        self.tokenizer = tokenizer
        self.output = open(outputfile, "w+")
        self.indentation = 0

        self.tokenizer.advance()


    def eat(self, expectedToken):
        if self.tokenizer.keyword() == expectedToken or self.tokenizer.symbol() == expectedToken:
            self.xmlToken()
            if self.tokenizer.hasMoreTokens():
                self.tokenizer.advance()
            return
        raise Exception("Unexpected Token: " + self.tokenizer.keyword() + " of Type " + self.tokenizer.tokenType() + "\nExpected Token: " + expectedToken)


    def eatType(self, expectedType):
        if self.tokenizer.tokenType() == expectedType:
            self.xmlToken()
            if self.tokenizer.hasMoreTokens():
                self.tokenizer.advance()
            return
        raise Exception("Unexpected Token: " + self.tokenizer.keyword() + " of Type " + self.tokenizer.tokenType() + "\nExpected Type: " + expectedType)  


    def xmlToken(self):
        tag = self.tokenizer.tokenType()
        if self.tokenizer.tokenType() == INT_CONST:
            tag = "integerConstant"
        elif self.tokenizer.tokenType() == STRING_CONST:  
            tag = "stringConstant"
        self.output.write(('\t' * self.indentation) + f"<{tag}> {self.tokenizer.currentToken[1]} </{tag}>\n")


    def xml_scope(tag):
        def _xml_scope(func):
            @functools.wraps(func)
            def wrapper(self, *args):
                self.output.write(('\t' * self.indentation) + f"<{tag}>\n")
                self.indentation += 1
                func(self, *args)
                self.indentation -= 1
                self.output.write(('\t' * self.indentation) + f"</{tag}>\n")
            return wrapper
        return _xml_scope


#====================== CompileXXX ==========================
    @xml_scope('class')
    def compileClass(self):
        self.eat('class')
        
        # className
        self.eatType(IDENTIFIER)

        self.eat('{')
        while self.tokenizer.keyword() in ["field", "static"]:
            self.compileClassVarDec()
        while self.tokenizer.keyword() in ["function", "method", "constructor"]:
            self.compileSubroutineDec()
        self.eat('}')


    @xml_scope('classVarDec')
    def compileClassVarDec(self):
        if self.tokenizer.keyword() == 'static':
            self.eat('static')
        else:
            self.eat('field')

        # type
        if self.tokenizer.tokenType() == IDENTIFIER or self.tokenizer.keyword() in ["int", "char", "boolean"]:
            self.xmlToken()
            self.tokenizer.advance()
        else:
            raise Exception("Expected an Type, but got instead: " + self.tokenizer.keyword())

        # varName 
        self.eatType(IDENTIFIER)      

        while self.tokenizer.symbol() == ',':
            self.eat(',')
            self.eatType(IDENTIFIER)  
        
        self.eat(';')


    @xml_scope('subroutineDec')
    def compileSubroutineDec(self):
        if self.tokenizer.keyword() == 'constructor':
            self.eat('constructor')
        elif self.tokenizer.keyword() == 'method':
            self.eat('method')
        elif self.tokenizer.keyword() == 'function':
            self.eat('function')

        # type
        if self.tokenizer.tokenType() == IDENTIFIER or self.tokenizer.keyword() in ["int", "char", "boolean", "void"]:
            self.xmlToken()
            self.tokenizer.advance()
        else:
            raise Exception("Expected an Type, but got instead: " + self.tokenizer.keyword())

        # subroutineName
        self.eatType(IDENTIFIER)

        self.eat('(')
        self.compileParameterList()
        self.eat(')')

        self.compileSubroutineBody()
        

    @xml_scope('parameterList')
    def compileParameterList(self):
        if self.tokenizer.symbol() == ')':
            return

        # type
        self.xmlToken()
        self.tokenizer.advance()
        # varName
        self.eatType(IDENTIFIER)
        while self.tokenizer.symbol() == ',':
            self.eat(',')
            self.xmlToken()
            self.tokenizer.advance()
            self.eatType(IDENTIFIER)        


    @xml_scope('subroutineBody')
    def compileSubroutineBody(self):
        self.eat('{')
        while self.tokenizer.keyword() == 'var':
            self.compileVarDec()
        self.compileStatements()
        self.eat('}')


    @xml_scope('varDec')
    def compileVarDec(self):
        self.eat('var')
        # type
        if self.tokenizer.tokenType() == IDENTIFIER or self.tokenizer.keyword() in ["int", "char", "boolean"]:
            self.xmlToken()
            self.tokenizer.advance()
        else:
            raise Exception("Expected an Type, but got instead: " + self.tokenizer.keyword())
        # varName
        self.eatType(IDENTIFIER)
        
        while self.tokenizer.symbol() == ',':
            self.eat(',')
            self.eatType(IDENTIFIER)

        self.eat(';')


    @xml_scope('statements')
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


    @xml_scope('letStatement')
    def compileLet(self):
        self.eat('let')
        self.eatType(IDENTIFIER)

        if self.tokenizer.symbol() == '[':
            self.eat('[')
            self.compileExpression()
            self.eat(']')

        self.eat('=')
        self.compileExpression()
        self.eat(';')


    @xml_scope('ifStatement')
    def compileIf(self):
        self.eat('if')
        self.eat('(')
        self.compileExpression()
        self.eat(')')

        self.eat('{')
        self.compileStatements()
        self.eat('}')

        if self.tokenizer.keyword() == 'else':
            self.eat('else')
            self.eat('{')
            self.compileStatements()
            self.eat('}')


    @xml_scope('whileStatement')
    def compileWhile(self):
        self.eat('while')
        self.eat('(')
        self.compileExpression()
        self.eat(')')

        self.eat('{')
        self.compileStatements()
        self.eat('}')


    @xml_scope('doStatement')
    def compileDo(self):
        self.eat('do')
        
        # className | varName
        self.eatType(IDENTIFIER)  
        if self.tokenizer.symbol() == '.':
            self.eat('.')
            # subroutineName
            self.eatType(IDENTIFIER)

        self.eat('(')
        self.compileExpressionList()
        self.eat(')')

        self.eat(';')


    @xml_scope('returnStatement')
    def compileReturn(self):
        self.eat('return')
        if self.tokenizer.tokenType() in [IDENTIFIER, INT_CONST, STRING_CONST] or self.tokenizer.symbol() in ['~', '-']:
            self.compileExpression()
        self.eat(';')


    @xml_scope('expression')
    def compileExpression(self):
        self.compileTerm()
        while self.tokenizer.symbol() in ['+', '-', '*', '/', '=', '>', '<', '&', '|']:
            self.eatType(SYMBOL)
            self.compileTerm()


    @xml_scope('term')
    def compileTerm(self):
        if self.tokenizer.symbol() in ['~', '-']:
            self.eatType(SYMBOL)
            self.compileTerm()
        elif self.tokenizer.tokenType() in [INT_CONST, STRING_CONST] or self.tokenizer.keyword() in ['true', 'false', 'null', 'this']:
            self.xmlToken()
            self.tokenizer.advance()
        elif self.tokenizer.symbol() == '(':
            self.eat('(')
            self.compileExpression()
            self.eat(')')
        elif self.tokenizer.tokenType() == IDENTIFIER:
            self.eatType(IDENTIFIER)
            self.tokenizer.advance()

            if self.tokenizer.symbol() == '[':
                self.eat('[')
                self.compileExpression()
                self.eat(']')
            elif self.tokenizer.symbol() in ['(', '.']:

                if self.tokenizer.symbol() == '.':
                    self.eat('.')
                    self.eatType(IDENTIFIER)

                self.eat('(')
                self.compileExpressionList()
                self.eat(')')


    @xml_scope('expressionList')
    def compileExpressionList(self):
        if self.tokenizer.symbol() == ')':
            return

        self.compileExpression()
        while self.tokenizer.symbol() == ',':
            self.eat(',')
            self.compileExpression()



def main():
    inputArg = sys.argv[1]

    def tokens(inputfile):
        tokenizer = Tokenizer(inputfile)
        outputfile = inputfile.replace(".jack", "Test.xml")
        with open(outputfile, 'w+') as f :
            f.write("<tokens>\n")
            while tokenizer.hasMoreTokens():
                tokenizer.advance()
                tag = tokenizer.tokenType()
                if tokenizer.tokenType() == INT_CONST:
                    tag = "integerConstant"
                elif tokenizer.tokenType() == STRING_CONST:  
                    tag = "stringConstant"
                f.write(f"<{tag}> {tokenizer.currentToken[1]} </{tag}>\n")
            f.write("</tokens>")

    def compileXML(inputfile):
        tokenizer = Tokenizer(inputfile)
        outputfile = inputfile.replace(".jack", "Test.xml")
        compilationEngine = CompilationEngine(outputfile, tokenizer)
        compilationEngine.compileClass()

    delegate = compileXML
    if os.path.isfile(inputArg):
        delegate(inputArg)
    elif os.path.isdir(inputArg):
        files = [os.path.join(inputArg, file) for file in os.listdir(inputArg) if file.endswith(".jack")]
        for file in files:
            delegate(file)
    else:
        raise Exception("Input was neither file nor directory")


if __name__ == "__main__":
    main()