import sys
import re

def add_lib(code):
    code = \
        "#include <stdio.h>\n#include <stdlib.h>\n#define MAXLENGTH 10\n#define INF 0x3f3f3f3f\n" + code
    return code


def index_code(code):
    lines = code.split("\n")
    index_num = 0
    text = []
    for l in lines:
        if list(l).count("{") and list(l).count("}"):
            buf = "\t"*index_num + l
            text.append(buf+"\n")
            continue
        index_num -= list(l).count("}")
        buf = "\t"*index_num + l
        index_num += list(l).count("{")
        text.append(buf+"\n")
    text = "".join(text)
    return text

def add_all(p, delimited=""):
    ret = ""
    for i in range(len(p) - 1):
        ret = ret + p[i] + delimited
    ret = ret + p[-1]
    return ret

def str_to_c_val(s: str):
    """
    init_val examples:
    ''      -> 0
    '4'     -> 4
    '4.3'   -> 4.3
    '"a"'   -> 'a'
    '"abcd"'-> "abcd"
    "'a'"   -> 'a'
    "'abc'" -> "abc"
    'a'     -> 'a'
    'abcd'  -> "abcd"
    """
    val = s
    if val == '':
        val = 0
    elif val.isdecimal():
        val = int(val)
    else:
        try:
            val = float(val)
        except ValueError:
            if len(re.findall(r'"(.*)"', val)) == 1:
                val = val.split('"')[1]
            elif len(re.findall(r"'(.*)'", val)) == 1:
                val = val.split("'")[1]

            if len(val) == 1:
                val = "'{}'".format(val)
            else:
                val = '"{}"'.format(val)

    return val


if __name__ == '__main__':
    print(str_to_c_val('"adsa"'))
