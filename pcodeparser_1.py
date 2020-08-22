import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from pcodelex import pcodeLexer

class pcodeParser: 
    def __init__(
            self, 
            lexer=pcodeLexer):
        """ Create a new pcodeParser.
        """
        self.plex = lexer()
        self.plex.build(debug=1)
        self.tokens = self.plex.tokens
        self.is_defined = set()

    def p_statements(self, p):
        """ statements  : statement statements
                        | statement
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1] + "\n"+ p[2]

# for
    def p_for(self, p):
        """ for : for_header_1 chunk
                | for_header_2 chunk
                | for_header_3 chunk"""
        p[0] = p[1] + p[2]


    def p_for_header_1(self, p):
        """ for_header_1    : FOR ID EQUALS expression TO expression
                            | FOR ID EQUALS expression TO expression BY expression 
                        """

        init_part = p[2] + "=" + p[4] 
        bool_part = p[2] + "<=" + p[6]
        if len(p) == 7:
            iter_part = p[2] + "++"
        else:
            iter_part = p[2] + "+=" + p[8]
        p[0] = "for(%s;%s;%s)" % (init_part, bool_part, iter_part)

    def p_for_header_2(self, p):
        """ for_header_2    : FOR ID EQUALS expression SEMI boolexpre SEMI iterator
        """
        p[0] = p[1]+"("+ p[2]+p[3]+p[4]+p[5]+p[6]+p[7]+p[8]+")"

    def p_for_header_3(self, p):
        """ for_header_3    : FOR LPAREN ID EQUALS expression SEMI boolexpre SEMI iterator RPAREN
                            | FOR LPAREN ID EQUALS expression SEMI boolexpre SEMI RPAREN
                            | FOR LPAREN SEMI boolexpre SEMI iterator RPAREN
                            | FOR LPAREN SEMI boolexpre SEMI RPAREN
        """
        if len(p) == 11:
            p[0] = p[3]+p[4]+p[5]+p[6]+p[7]+p[8]+p[9]
        elif len(p) == 10:
            p[0] = p[3]+p[4]+p[5]+p[6]+p[7]+p[8]
        elif len(p) == 8:
            p[0] = p[3]+p[4]+p[5]+p[6]
        else:
            p[0] = p[3]+p[4]+p[5]
        p[0] = "for("+p[0]+")"


#  while
    def p_while(self, p):
        """ while : while_condition chunk """
        p[0] = p[1] + p[2]

    def p_while_condition(self, p):
        """ while_condition : WHILE LPAREN boolexpre RPAREN
                            | WHILE boolexpre"""
        if len(p) == 3:
            p[0] = p[1] +"(" +p[2] + ")"
        else:
            p[0] = p[1] + p[2] + p[3] + p[4]

# if
    def p_if(self, p):
        """ if  : if_condition chunk 
                | if_condition chunk ELSE chunk"""
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1] + p[2] + p[3] + p[4]

    def p_if_condition(self, p):
        """ if_condition    : IF LPAREN boolexpre RPAREN
                            | IF boolexpre"""
        if len(p) == 3:
            p[0] = p[1] +"(" +p[2] + ")"
        else:
            p[0] = p[1] + p[2] + p[3] + p[4]

# chunk
    def p_chunk(self, p):
        """ chunk   : LBRACE statements RBRACE"""
        p[0] = "{\n" + p[2] + "\n}"

    def p_statement(self, p):
        """ statement   : assignment
                        | if
                        | while
                        | for
        """
        p[0] = p[1]


# assignment
    def p_assignment(self, p):
        """ assignment  : ID EQUALS expression SEMI
                        | ID EQUALS boolexpre SEMI
        """
        p[0] = p[1] + p[2] + p[3]
        if not p[1] in self.is_defined:
            print("What's the type of {}". format(p[1]))
            t = input()
            t = t.strip()
            self.is_defined.add(p[1])
            p[0] = t + " " + p[0]
        p[0] = p[0] + ";"

    def p_iterator(self, p):
        """ iterator    : ID EQUALS expression
                        | ID PLUSPLUS
                        """
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1] + p[2] + p[3]


    def p_boool_expression(self, p):
        """ boolexpre   : boolexpre BI_BOOL_OP boolexpre
                        | MON_BOOL_OP boolexpre
                        | LPAREN boolexpre RPAREN
                        | expression
                        | TRUE
                        | FALSE
                        | INT_CONST_DEC"""

        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1] + p[2] + p[3]


    def p_expressions(self, p):
        """ expression  : expression PLUS expression 
                        | expression MINUS expression 
                        | expression TIMES expression 
                        | expression DIVIDE expression
                         
                        | INT_CONST_DEC 
                        | FLOAT_CONST_DEC 
                        | STRING_CONST
                        | ID 
                        | LPAREN expression RPAREN 
        """
        self.precedence = (
            ('left', 'PLUS', 'MINUS'),
            ('left', 'TIMES', 'DIVIDE'),
            # ('right', 'UPLUS'),             # Unary plus operator
            # ('right', 'UMINUS'),            # Unary minus operator
        )

        # def p_expr_uminus(self, p):
        #     'expression : MINUS expression %prec UMINUS'
        #     p[0] = -p[2]
        
        if len(p) == 4:
            p[0] = p[1] + p[2] + p[3]
        
        # elif len(p) == 3:
        #     if p[1] == '-':
        #         p[0] = -p[2]
        #     elif p[1] == '+':
        #         p[0] = p[2]
        elif len(p) == 2: 
            p[0] = p[1]


    # Error rule for syntax errors
    def p_error(self, p):
        print("Syntax error in input: %s"% p)

    # Build the parser
    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)

    # Test it output
    def test(self, data):
        tmp = self.plex.test(data)   
        result = self.parser.parse(data)
        print(result)

# Build the parser and try it out
m = pcodeParser()
m.build()           # Build the parser
with open("./pcode1.txt", "r", encoding="utf-8") as f:
    data = f.readlines()
print("######################--   语法分析   --######################")
m.test("for i = 1 to 10 {a=a+1;}")
