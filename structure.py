from variable_info import BaseVar


class Structure:
    def __init__(self, struct_name):
        self.struct_name = struct_name
        self.variables = list()
        self.name_type = dict()

    def get_name(self):
        return self.struct_name

    def add(self, name, t, val=None):
        _t = BaseVar(name, t, val)
        self.variables.append(_t)
        self.name_type[name] = t

    def get_all_variables(self):
        ret = dict()
        for name, t in self.name_type.items():
            vn = "{}.{}".format(self.struct_name, name)
            ret[vn] = t
        return ret

    def make_definition(self):
        definition = ""
        for n, t in self.name_type.items():
            d = "{} {};\n".format(t, n)
            definition = definition + d
        definition = "struct %s {\n%s}\n" % (self.struct_name, definition)
        return definition


class StructObject:
    def __init__(self, structure: Structure, object_name):
        self.object_name = object_name
        self.structure = structure

    def get_struct_name(self):
        return self.structure.get_name()

    def get_variables(self):
        return self.get_variables()

    def make_definition(self):
        struct = self.structure
        definition = ""
        for v in struct.variables:
            d = "{}.{} = {};\n".format(self.object_name, v.var_name, v.init_val)
            definition = definition + d
        return definition
