import sys

def add_lib(code):
    code = \
    """#include <stdio.h>\n#include <stdlib.h>\n#define MAXLENGTH 10\n#define INF 0x3f3f3f3f\n
    """ + code
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
