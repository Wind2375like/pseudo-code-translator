from variable_info import VarInfo

class FuncInfo():
    def __init__(self,
                 name,
                 line_no,
                 line_statement,
                 parameters=None):
        self.func_name = name
        self.set_line_no(line_no)
        self.set_line_statement(line_statement)
        self.set_parameters(parameters)

    def set_func_name(self, name):
        self.func_name = name

    def set_line_no(self, line_no):
        self.line_no = line_no

    def set_line_statement(self, statement):
        self.line_statement = statement

    def set_parameters(self, parameters):
        if parameters is None:
            self.parameters = dict()

    def add_parameter(self, name, var_type):
        var_info = VarInfo(name=name, line_statement=self.line_statement,
                           line_no=self.line_no, init_method='func_parameters')
        self.parameters[name] = var_info
