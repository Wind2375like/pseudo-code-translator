import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from pcodelex import pcodeLexer
import re


class pcodeParser:
    def __init__(
            self,
            lexer=pcodeLexer):
        """ Create a new pcodeParser.
            is_defined  : a set of defined variables
            is_type     : a set of legal types
        """
        self.plex = lexer()
        self.plex.build(debug=1)
        self.tokens = self.plex.tokens
        self.is_defined = set()
        self.is_type = {"int", "float", "char", "string", "bool", "void"}
        self.funcs = set()                  # function declarations
        self.funcs_defines = set()          # function definitions
        self.par_to_be_init = dict()        # parameters to be init
        self.par_info = dict()              # parameters information
        self.completed_par = set()          # completed parameters definition
        self.func_pars = dict()             # functions' parameter and type
        self.buf = [[], []]                 # buf
        self.main_function = ""             # main function information
        self.cur_func = "main"              # current function name
        self.flag = 0                       # flag

    def _define_parameter(self, t, name, init_val=None):
        """
        usage: define the parameters
        :param t:           type
        :param name:        parameter's name
        :param init_val:    initiate value
        :return:            None
        """
        self.par_info[name] = [t, init_val]
        if init_val is not None:
            self.completed_par.add("{} {} = {};" .format(t, name, init_val))
        else:
            self.completed_par.add("{} {};" .format(t, name))

    def _add_parameter(self, name, where):
        """
        usage: record the name and where it appeared
        :param name:    parameter name
        :param where:   where it appeared
        :return:        None
        """

        if name in self.par_to_be_init.keys():
            self.par_to_be_init[name].join(where)
        else:
            self.par_to_be_init[name] = where

    def _clean_buf(self):
        """
        usage: clean all the temporary buffer after define a function
        :return: None
        """
        self.par_to_be_init.clear()
        self.par_info.clear()
        self.cur_func = "main"
        self.completed_par.clear()
        self.is_defined.clear()
        self.func_pars.clear()
        self.buf = [[], []]
        self.flag = 0

    def _query_parameters(self):
        """
        usage: query the parameters information and complete the definition
        :return: None
        """
        for par_name, where in self.par_to_be_init.items():
            print("{}\nWhat's the type of {} in function {}?" .format(where, par_name, self.cur_func))
            t = str(input()).strip()
            t = self._check_type(t)
            print("What's the initiate value of {}? (default is 0)". format(par_name))
            init_val = input()
            if init_val == '':
                init_val = 0
            elif init_val.isdigit():
                init_val = int(init_val)
            elif init_val.isdecimal():
                init_val = float(init_val)
            elif len(re.findall(r'".*"', init_val)) == 0:
                init_val = '"{}"' .format(init_val)

            self._define_parameter(t, par_name, init_val)

    def _check_type(self, str):
        """ Check the variable types inputed by users.
            If it's illegal, correct it.
        """
        while not str in self.is_type:
            print("{} is not a type. Input a correct type.".format(str))
            str = input()
            str = str.strip()
        return str

    def correct_bool(self, str):
        """ Correct and, or, not to &&, ||, !
        """

        if str == "and": return "&&"
        if str == "or": return "||"
        if str == "not": return "!"
        return str

    def p_pretty_code(self, p):
        """ pretty_code :   c_code"""
        h = ""
        for i in self.funcs:
            h = h + i + "\n"
        h = h + "\n"

        t = ""
        for i in self.funcs_defines:
            t = t + i + "\n\n"

        p[0] = h + self.main_function + "\n\n" + t

    def p_c_code(self, p):
        """ c_code  : c_code c_code
                    | main
                    | assignment
                    | func_define
                    """
        if len(p) == 3:
            p[0] = p[1] + "\n" + p[2]
        else:
            p[0] = p[1]

    # Main function
    def p_main(self, p):
        """ main    : vartype MAIN LPAREN RPAREN chunk
                    | MAIN LPAREN RPAREN chunk
                    | MAIN LPAREN expression COMMA expression RPAREN chunk
                    """
        self._query_parameters()
        tmp = p[len(p) - 1]
        h = ""
        for j in self.completed_par:
            h = h + j + "\n"
        i = tmp.find("{")
        tmp = list(tmp)
        tmp.insert(i + 2, h)
        tmp = "".join(tmp)
        p[0] = "int main(int argc, char *argv[])" + tmp
        self.main_function = p[0]
        self._clean_buf()

    # Statements
    def p_statements(self, p):
        """ statements  : statement statements
                        | statement
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1] + "\n" + p[2]

    # call void functions
    def p_call_func_2(self, p):
        """ call_func_2     : call_func_1 SEMI
        """
        p[0] = p[1] + p[2]

    # used for expressions
    def p_call_func_1(self, p):
        """ call_func_1     : ID LPAREN call_func_var RPAREN
        """
        p[0] = p[1] + p[2] + p[3] + p[4]

    def p_call_func_var(self, p):
        """ call_func_var   : expression COMMA call_func_var
                            | expression
        """
        if len(p) == 4:
            p[0] = p[1] + "," + " " + p[3]
        else:
            p[0] = p[1]

    # function define
    def p_func_define(self, p):
        """ func_define : func_head func_body """
        self._query_parameters()
        tmp = p[2]
        h = ""
        for j in self.completed_par:
            h = h + j + "\n"
        i = tmp.find("{")
        tmp = list(tmp)
        tmp.insert(i + 2, h)
        p[2] = "".join(tmp)
        p[0] = p[1] + p[2]
        self.funcs_defines.add(p[0])
        self._clean_buf()

    def p_func_head(self, p):
        """ func_head   : ID LPAREN func_pars RPAREN
                        | vartype ID LPAREN func_pars RPAREN
        """
        if len(p) == 5:
            print("What's the type of function %s?" % p[1])
            t = str(input()).strip()
            p[0] = t + " " + _add_all(p[1:])
            self.is_defined.add(p[1])
            self.cur_func = p[1]
        else:
            p[0] = p[1] + " " + _add_all(p[2:])
            self.is_defined.add(p[2])
            self.cur_func = p[2]

        self.funcs.add(p[0] + ";")

    def p_func_body(self, p):
        """ func_body   : chunk"""
        p[0] = p[1]

    def p_func_pars(self, p):
        """ func_pars   : func_par COMMA func_pars
                        | func_par 
        """
        if len(p) == 4:
            p[0] = p[1] + ", " + p[3]
        else:
            p[0] = p[1]

    def p_func_par(self, p):
        """ func_par    : vartype ID
                        | ID
        """
        if len(p) == 3:
            p[0] = p[0] + " " + p[1]
            self.func_pars[p[2]] = p[1]
        else:
            print("What's the type of %s" % p[1])
            t = str(input()).strip()
            t = self._check_type(t)
            p[0] = t + " " + p[1]
            self.func_pars[p[1]] = t

    def p_return(self, p):
        """ return  : RETURN expression SEMI """
        p[0] = p[1] + " " + p[2] + p[3]

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

        if not p[2] in self.is_defined:
            print("What's the type of {}".format(p[2]))
            t = input()
            t = t.strip()
            t = self._check_type(t)
            self.is_defined.add(p[2])
            p[0] = t + " " + p[2] + ";\n" + p[0]

    def p_for_header_2(self, p):
        """ for_header_2    : FOR ID EQUALS expression SEMI boolexpre SEMI iterator
        """
        p[0] = p[1] + "(" + p[2] + p[3] + p[4] + p[5] + p[6] + p[7] + p[8] + ")"

        if not p[2] in self.is_defined:
            print("What's the type of {}".format(p[2]))
            t = input()
            t = t.strip()
            t = self._check_type(t)
            self.is_defined.add(p[2])
            p[0] = t + " " + p[2] + ";\n" + p[0]

    def p_for_header_3(self, p):
        """ for_header_3    : FOR LPAREN ID EQUALS expression SEMI boolexpre SEMI iterator RPAREN
                            | FOR LPAREN ID EQUALS expression SEMI boolexpre SEMI RPAREN
                            | FOR LPAREN SEMI boolexpre SEMI iterator RPAREN
                            | FOR LPAREN SEMI boolexpre SEMI RPAREN
        """
        if len(p) == 11:
            p[0] = p[3] + p[4] + p[5] + p[6] + p[7] + p[8] + p[9]

        elif len(p) == 10:
            p[0] = p[3] + p[4] + p[5] + p[6] + p[7] + p[8]

        elif len(p) == 8:
            p[0] = p[3] + p[4] + p[5] + p[6]
        else:
            p[0] = p[3] + p[4] + p[5]
        p[0] = "for(" + p[0] + ")"

        if len(p) >= 10:
            if not p[3] in self.is_defined:
                print("What's the type of {}".format(p[3]))
                t = input()
                t = t.strip()
                t = self._check_type(t)
                self.is_defined.add(p[3])
                p[0] = t + " " + p[3] + ";\n" + p[0]

    # while
    def p_while(self, p):
        """ while : while_condition chunk """
        p[0] = p[1] + p[2]

    def p_while_condition(self, p):
        """ while_condition : WHILE LPAREN boolexpre RPAREN
                            | WHILE boolexpre"""
        if len(p) == 3:
            p[0] = p[1] + "(" + p[2] + ")"
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
            p[0] = p[1] + "(" + p[2] + ")"
        else:
            p[0] = p[1] + p[2] + p[3] + p[4]

    # Chunk: {statements} 
    def p_chunk(self, p):
        """ chunk   : LBRACE statements RBRACE"""
        p[0] = "{\n" + p[2] + "\n}"

    def p_statement(self, p):
        """ statement   : assignment
                        | arr_assignment
                        | if
                        | for
                        | while
                        | call_func_2
                        | single_elem_stmt
                        | swap
                        | return
        """
        p[0] = p[1]
        # [TODO: adapt the format and try to add correct line number.]
        # [TODO: gain the next statement after parameter definition.]
        self.buf[1] = "\n{}" .format(p[0])
        self.buf[0] = []

    def p_arr_assignment(self, p):
        """ arr_assignment  : ID LBRACKET expression RBRACKET EQUALS expression SEMI
                            | ID LBRACKET expression TO expression RBRACKET EQUALS expression SEMI
        """
        if len(p) == 8:
            p[0] = p[1] + p[2] + p[3] + p[4] + p[5] + p[6] + ";"
        if len(p) == 10:
            p[0] = "for(int i = 0; i <= %s-%s; i++) %s[%s+i]%s%s;" % (p[5], p[3], p[1], p[3], p[7], p[8])

        if not p[1] in self.is_defined:
            print("What's the type of {}".format(p[1]))
            t = input()
            t = t.strip()
            t = self._check_type(t)
            self.is_defined.add(p[1])
            self.par_to_be_init.add(t + " " + p[1] + "[MAXLENGTH]" + ";")

    # Variable types:
    def p_vartype(self, p):
        """ vartype : CONST vartype
                    | INT
                    | FLOAT
                    | STRING
                    | BOOL
                    | CHAR
        """
        if len(p) == 3:
            p[0] = p[1] + " " + p[2]
        else:
            p[0] = p[1]

    # Swap
    def p_swap(self, p):
        """ swap    : ID LT MINUS GT ID SEMI
                    | SWAP LPAREN ID COMMA ID RPAREN SEMI
        """
        if len(p) == 7:
            p[0] = "swap(%s, %s)" % (p[1], p[5])
        else:
            p[0] = "swap(%s, %s)" % (p[3], p[5])

    # Assignment
    def p_assignment(self, p):
        """ assignment  : ID EQUALS expression SEMI
                        | ID EQUALS boolexpre SEMI
                        | vartype ID EQUALS expression SEMI
                        | vartype ID EQUALS boolexpre SEMI
        """
        if len(p) == 5:
            p[0] = p[1] + p[2] + p[3] + p[4]
            if not p[1] in self.par_to_be_init.keys():
                self.buf[0] = p[1]
                # [TODO: adapt the format and try to add correct line number]
                self._add_parameter(p[1], where="".join(self.buf[1]) + "\n" + p[0])

        elif len(p) == 6:
            self.is_defined.add(p[2])
            p[0] = p[1] + " " + p[2] + p[3] + p[4] + p[5]

    # EQUALS
    def p_EQUALS(self, p):
        """ EQUALS      : EQUAL
                        | TIMESEQUAL
                        | DIVEQUAL
                        | MODEQUAL
                        | PLUSEQUAL
                        | MINUSEQUAL
        """
        p[0] = p[1]

    # BI_BOOL_OP and MON_BOOL_OP
    def p_BI_BOOL_OP(self, p):
        """ BI_BOOL_OP  : LE
                        | GE
                        | LT
                        | GT
                        | EQ
                        | NE
                        | AND
                        | OR
        """
        p[0] = p[1]

    def p_MON_BOOL_OP(self, p):
        """ MON_BOOL_OP : NOT
        """
        p[0] = p[1]

    def p_iterator(self, p):
        """ iterator    : ID EQUALS expression
                        | ID PLUSPLUS
                        | ID MINUSMINUS
                        | PLUSPLUS ID
                        | MINUSMINUS ID
        """
        if len(p) == 3:
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1] + p[2] + p[3]

    def p_bool_expression(self, p):
        """ boolexpre   : boolexpre BI_BOOL_OP boolexpre
                        | MON_BOOL_OP boolexpre
                        | LPAREN boolexpre RPAREN
                        | expression
                        | TRUE
                        | FALSE
                        | INT_CONST_DEC"""

        if len(p) == 2:
            p[1] = self.correct_bool(p[1])
            p[0] = p[1]
        elif len(p) == 3:
            p[1] = self.correct_bool(p[1])
            p[0] = p[1] + p[2]
        else:
            p[2] = self.correct_bool(p[2])
            p[0] = p[1] + p[2] + p[3]

    def p_array_elem_sing(self, p):
        """ array_elem_sing    : ID LBRACKET expression RBRACKET
        """
        p[0] = p[1] + p[2] + p[3] + p[4]

    def p_array_elem_multi(self, p):
        """ array_elem_multi    : ID LBRACKET ID TO ID RBRACKET
        """
        p[0] = p[1] + p[2] + p[3] + "+i" + p[6]

    def p_single_elem_stmt(self, p):
        """ single_elem_stmt    : ID PLUSPLUS SEMI
                                | ID MINUSMINUS SEMI
        """
        p[0] = p[1] + p[2] + ";"

        if not p[1] in self.is_defined:
            print("What's the type of {}".format(p[1]))
            t = input()
            t = t.strip()
            t = self._check_type(t)
            self.is_defined.add(p[1])
            self.par_to_be_init.add(t + " " + p[1] + ";")

    def p_single_elem(self, p):
        """ single_elem : array_elem_sing
                        | array_elem_multi
                        | INT_CONST_DEC 
                        | FLOAT_CONST_DEC 
                        | STRING_CONST
                        | ID
                        | ID PLUSPLUS
                        | ID MINUSMINUS 
                        | call_func_1
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1] + p[2]

    def p_expressions(self, p):
        """ expression  : expression PLUS expression 
                        | expression MINUS expression 
                        | expression TIMES expression 
                        | expression DIVIDE expression
                        | single_elem
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
        elif len(p) == 2:
            p[0] = p[1]

    # Error rule for syntax errors
    def p_error(self, p):
        print("Syntax error in input: %s" % p)

    # Build the parser
    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)

    # Test it output
    def test(self, data):
        self.plex.test(data)
        result = self.parser.parse(data)
        return result


def _add_all(p, delimited=""):
    ret = ""
    for i in range(len(p) - 1):
        ret = ret + p[i] + delimited
    ret = ret + p[-1]
    return ret


if __name__ == "__main__":
    import sys
    from pretty_code import index_code

    # Build the parser and try it out
    file_input = "./pcode1.txt"
    file_output = "./output.c"

    m = pcodeParser()
    m.build()  # Build the parser
    with open(file_input, "r", encoding="utf-8") as f:
        data = f.readlines()
    data = "".join(data)
    code = m.test(data)
    code = index_code(code)

    with open(file_output, "w") as f:
        f.write(code)
