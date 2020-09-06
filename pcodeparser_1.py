import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from pcodelex import pcodeLexer
from variable_info import VarInfo
import utils
import structure
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
        self.is_type = {"int", "float", "char", "string", "bool", "void", "array"}
        self.funcs = set()                  # function declarations
        self.funcs_defines = set()          # function definitions
        self.par_to_be_init = dict()        # parameters to be init: {'par_name': var_info}
        self.func_pars = dict()             # functions' parameter and type
        self.buf = []  # buf
        self.main_function = ""             # main function information
        self.cur_func = "main"              # current function name
        self.flag = 0  # flag
        self.structures = dict()            # structure definition
        self.struct_objects = dict()        # struct objects
        # [TODO: complete the global variable dictionary, so that we can create global variable outside the main]
        self.global_variable = dict()       # global variable
        self.every_line_of_code = list()    # every line of code

    def _add_parameter(self, name, **kwargs):
        """

        :param name:
        :param lineno:
        :param line_statement:
        :param hint_type:
        :param is_array:
        :return:
        """
        var_info = VarInfo(name, **kwargs)
        self.par_to_be_init[name] = var_info

    def _clean_buf(self):
        """
        usage: clean all the temporary buffer after define a function
        :return: None
        """
        self.par_to_be_init.clear()
        self.cur_func = "main"
        self.is_defined.clear()
        self.func_pars.clear()
        self.buf.clear()
        self.flag = 0

    def _query_parameters(self):
        """
        usage: query the parameters information and complete the definition
        :return: None
        """
        for par_name in self.par_to_be_init.keys():
            var_info = self.par_to_be_init[par_name]
            if var_info.is_defined == False:
                where = "\nIn line {:<5}{}".format(var_info.line_no, var_info.line_statement)
                print(where)
                if var_info.method == "normal":
                    print("\nWhat's the type of {} in function {}?".format(par_name, self.cur_func))
                elif var_info.method == "array":
                    print("\nWhat's the element type of array {} in function {}?".format(par_name,
                                                                                             self.cur_func))
                elif var_info.method == "struct":
                    print("\nWhat's the struct of {}?".format(par_name))

                hint = ", ".join(self.is_type)
                print("Types available: {} or new struct".format(hint))
                t = str(input()).strip()
                t = self._check_type(t)

                if var_info.method == "struct":
                    struct_object = structure.StructObject(self.structures[t], par_name)
                    var_info.set_var_type(struct_object)
                    var_info.make_definition()
                else:
                    print("What's the initial value of {}? (default is 0)".format(par_name))
                    init_val = str(input()).strip()
                    init_val = utils.str_to_c_val(init_val)

                    var_info.set_init_val(init_val)
                    var_info.set_var_type(t)
                var_info.make_definition()

            else:
                # [TODO: 并查集？]
                pass

    def _create_structure(self, name):
        struct_name = name
        struct = structure.Structure(struct_name)
        print("enter q to quit")
        print("variable_type variable_name [init_val]")
        answer = input().strip()
        while answer != 'q':
            answer = answer.split(" ")
            if len(answer) == 2:
                struct.add(answer[1], answer[0], 0)
            if len(answer) == 3:
                struct.add(answer[1], answer[0], answer[2])
            answer = input()
        self.structures[struct_name] = struct
        return struct_name

    def _check_type(self, str):
        """ Check the variable types inputed by users.
            If it's illegal, correct it.
        """
        while not str in self.is_type:
            print("{} is not a type. If it is a new struct enter 'y' or re-enter the type?".format(str))
            str = input().strip()
            if str == 'y':
                str = self._create_structure(str)
                self.is_type.add(str)
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
        for k, v in self.structures.items():
            h = h + v.make_definition()

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
                    | MAIN LPAREN ID COMMA ID RPAREN chunk
                    """
        self._query_parameters()

        # initialize parameters
        tmp = p[len(p) - 1]
        h = ""
        for v in self.par_to_be_init.values():
            if not v.is_defined:
                j = v.definition
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

        # initialize parameters
        for v in self.par_to_be_init.values():
            if v.is_defined == False:
                j = v.definition
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
            p[0] = " " + utils.add_all(p[1:])
            line_no = p.lineno(1)
            line_statement = self.every_line_of_code[line_no]
            where = "In line {:<5}{}".format(line_no, line_statement)
            print("\n{}\nWhat's the type of function {}?".format(where, p[1]))
            print("Types available: int, float, char, string, bool, void")
            t = str(input()).strip()
            t = self._check_type(t)
            p[0] = t + p[0]
            self.cur_func = p[1]
        else:
            p[0] = p[1] + " " + utils.add_all(p[2:])
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
                        | ID LBRACKET RBRACKET
                        | vartype ID LBRACKET RBRACKET
                        | ID LBRACKET single_elem RBRACKET
                        | vartype ID LBRACKET single_elem RBRACKET
        """
        if len(p) == 3:
            p[0] = p[1] + " " + p[2]
            self.func_pars[p[2]] = p[1]
            line_no = p.lineno(1)
            self._add_parameter(p[2], is_defined=True, line_no=line_no, line_statement=self.every_line_of_code[line_no], var_type=p[1])

        elif len(p) == 2:
            line_no = p.lineno(1)
            line_statement = self.every_line_of_code[line_no]
            where = "In line {:<5}{}".format(line_no, line_statement)
            print("\n{}\nWhat's the type of {} in this function?".format(where, p[1]))
            print("Types available: array, int, float, char, string, bool, void")
            t = str(input()).strip()
            t = self._check_type(t)
            if t == "array":
                print("What's the element type of array {} in this function?".format(p[1]))
                print("Types available: int, float, char, string, bool, void")
                t = str(input()).strip()
                t = self._check_type(t)
                p[0] = t + " " + p[1] + "[]"
                self.func_pars[p[1]] = t
                self._add_parameter(p[1], is_defined=True, line_no=line_no, line_statement=line_statement, var_type=t)
            else:
                p[0] = t + " " + p[1]
                self.func_pars[p[1]] = t
                self._add_parameter(p[1], is_defined=True, line_no=line_no, line_statement=line_statement, var_type=t)

        elif p[2] == "[":
            line_no = p.lineno(1)
            line_statement = self.every_line_of_code[line_no]
            where = "In line {:<5}{}".format(line_no, line_statement)
            print("\n{}\nWhat's the element type of array {} in this function?".format(where, p[1]))
            print("Types available: int, float, char, string, bool, void")
            t = str(input()).strip()
            t = self._check_type(t)
            p[0] = t + " " + p[1] + "[]"
            self.func_pars[p[1]] = t
            self._add_parameter(p[1], is_defined=True, line_no=line_no, line_statement=line_statement, var_type=t)

        else:
            p[0] = p[1] + " " + p[2] + "[]"
            self.func_pars[p[2]] = p[1]
            line_no = p.lineno(1)
            self._add_parameter(p[2], is_defined=True, line_no=line_no, line_statement=self.every_line_of_code[line_no], var_type=p[1])

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
        p[0] = "for(%s; %s; %s)" % (init_part, bool_part, iter_part)

        if not p[2] in self.par_to_be_init.keys():
            line_no = p.lineno(1)
            self._add_parameter(p[2], line_no=line_no, line_statement=self.every_line_of_code[line_no], hint_type="int")

    def p_for_header_2(self, p):
        """ for_header_2    : FOR ID EQUALS expression SEMI boolexpre SEMI iterator
        """
        p[0] = "for(%s%s%s; %s; %s)" % (p[2], p[3], p[4], p[6], p[8])

        if not p[2] in self.par_to_be_init.keys():
            line_no = p.lineno(1)
            self._add_parameter(p[2], line_no=line_no, line_statement=self.every_line_of_code[line_no], hint_type="int")

    def p_for_header_3(self, p):
        """ for_header_3    : FOR LPAREN ID EQUALS expression SEMI boolexpre SEMI iterator RPAREN
                            | FOR LPAREN ID EQUALS expression SEMI boolexpre SEMI RPAREN
                            | FOR LPAREN SEMI boolexpre SEMI iterator RPAREN
                            | FOR LPAREN SEMI boolexpre SEMI RPAREN
        """
        if len(p) == 11:
            p[0] = "%s%s%s; %s; %s" % (p[3], p[4], p[5], p[7], p[9])

        elif len(p) == 10:
            p[0] = "%s%s%s; %s;" % (p[3], p[4], p[5], p[7])

        elif len(p) == 8:
            p[0] = "; %s; %s" % (p[4], p[6])
        else:
            p[0] = "; %s;" % (p[4])
        p[0] = "for(" + p[0] + ")"

        if len(p) >= 10:
            if not p[3] in self.par_to_be_init.keys():
                line_no = p.lineno(1)
                self._add_parameter(p[2], line_no=line_no, line_statement=self.every_line_of_code[line_no], hint_type="int")

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
        line_no = p.lineno(1)
        self.buf = [line_no, p[1]]

    def p_arr_assignment(self, p):
        """ arr_assignment  : ID LBRACKET expression RBRACKET EQUALS expression SEMI
                            | ID LBRACKET expression TO expression RBRACKET EQUALS expression SEMI
        """
        if len(p) == 8:
            p[0] = p[1] + p[2] + p[3] + p[4] + p[5] + p[6] + ";"
        if len(p) == 10:
            p[0] = "for(int i = 0; i <= %s-%s; i++) %s[%s+i]%s%s;" % (p[5], p[3], p[1], p[3], p[7], p[8])

        if not p[1] in self.par_to_be_init.keys():
            line_no = p.lineno(1)
            self._add_parameter(p[1], line_no=line_no, line_statement=self.every_line_of_code[line_no], method='array')

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
            p[0] = "swap(%s, %s);" % (p[1], p[5])
        else:
            p[0] = "swap(%s, %s);" % (p[3], p[5])

    # Assignment
    def p_assignment(self, p):
        """ assignment  : ID EQUALS expression SEMI
                        | ID EQUALS boolexpre SEMI
                        | vartype ID EQUALS expression SEMI
                        | vartype ID EQUALS boolexpre SEMI
                        | struct_elem EQUALS expression SEMI
        """
        if len(p) == 5:
            p[0] = p[1] + " " + p[2] + " " + p[3] + p[4]
            if "." in p[1]:
                struct_object, struct_var = p[1].split(".")
                if struct_object not in self.par_to_be_init.keys():
                    line_no = p.lineno(1)
                    self._add_parameter(struct_object, line_no=line_no, line_statement=self.every_line_of_code[line_no], method='struct')

            elif not p[1] in self.par_to_be_init.keys():
                line_no = p.lineno(1)
                self._add_parameter(p[1], line_no=line_no, line_statement=self.every_line_of_code[line_no])

        elif len(p) == 6:
            line_no = p.lineno(1)
            p[0] = p[1] + " " + p[2] + " " + p[3] + " " + p[4] + p[5]
            self._add_parameter(p[2], is_defined=True, line_no=line_no, line_statement=self.every_line_of_code[line_no],
                                var_type=p[1])  # add initialized paramenters into the par_to_be_init

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

        if not p[1] in self.par_to_be_init.keys():
            line_no = p.lineno(1)
            self._add_parameter(name=p[1], line_no=line_no, line_statement=self.every_line_of_code[line_no])

    def p_struct_elem(self, p):
        """ struct_elem : ID DOT ID"""
        p[0] = p[1] + p[2] + p[3]

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
                        | struct_elem
        """
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

    # Append the code
    def code_append(self, data):
        if len(self.every_line_of_code) == 0:
            self.every_line_of_code.append('')
        self.every_line_of_code.append(data)

    # Build the parser
    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)

    # Test it output
    def test(self, data):
        result = self.parser.parse(data)
        return result


if __name__ == "__main__":
    from utils import index_code
    from utils import add_lib

    # Build the parser and try it out
    file_input = "./pcode1.txt"
    file_output = "./output.c"

    m = pcodeParser()
    m.build()  # Build the parser
    with open(file_input, "r", encoding="utf-8") as f:
        data = f.readlines()

    for line_data in data:
        line_data = line_data.lstrip()    
        m.code_append(line_data)
    data = "".join(data)
    code = m.test(data)
    code = add_lib(index_code(code))

    with open(file_output, "w") as f:
        f.write(code)
