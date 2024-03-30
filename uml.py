#!/bin/env python3

import string
import json
import sys

def error(string):
    if __name__ == "__main__":
        print("error:", string)
        sys.exit(1)
    else:
        raise ValueError(string)

indenter = "    "

def escape(x):
    x = x.replace("\n", "\\n")  \
         .replace("\r", "\\r")  \
         .replace("\t", "\\t")  \
         .replace("\"", "\\\"") \
         .replace("\\", "\\\\")
    newx = ""
    for i in x:
        if i not in string.printable:
            newx += "\\x" + i.encode().hex()
        else: newx += i
    return newx

def check_hexcode(hexcode):
    for i in hexcode.lower():
        if i not in "1234567890abcdef":
            error(f"unknown hex code: {hexcode}")

def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

def isint(num):
    try:
        int(num)
        return True
    except ValueError:
        return False

def recompute_indstr(indent, indent_level, compact):
    if compact:
        newline = " "
        indstr = ""
    else:
        newline = "\n"
        indstr = indent * indent_level
    return newline, indstr

def serialize(obj: any, indent: str = "  ", compact: bool = False, *, indent_level=0) -> str:
    """
    parses krml to python object
    throws ValueError on error
    no newlines/indents if compact
    if not compact indent code with indent
    ignore extra arguments, they are ment for use inside the function.
    """
    data = ""
    newline, indstr = recompute_indstr(indent, indent_level, compact)

    if isinstance(obj, bool):
        return data + f"{indstr}bool {'true' if obj else 'false'}{newline}"
    elif obj is None:
        return data + f"{indstr}none{newline}"
    elif isinstance(obj, str):
        return data + f"{indstr}string \"{escape(obj)}\"{newline}"
    elif isinstance(obj, int):
        return data + f"{indstr}integer {obj}{newline}"
    elif isinstance(obj, float):
        return data + f"{indstr}float {obj}{newline}"
    elif isinstance(obj, dict):
        data += f"{indstr}dict{newline}"
        indent_level += 1
        newline, indstr = recompute_indstr(indent, indent_level, compact)
        indent_level += 1
        for k, i in obj.items():
            data += f"{indstr}key{newline}{serialize(k, indent=indent, indent_level=indent_level, compact=compact)}"
            data += f"{indstr}value{newline}{serialize(i, indent=indent, indent_level=indent_level, compact=compact)}"
        indent_level -= 2
        newline, indstr = recompute_indstr(indent, indent_level, compact)
        data += f"{indstr}end{newline}"
        return data
    elif isinstance(obj, list):
        data += f"{indstr}array{newline}"
        indent_level += 1
        newline, indstr = recompute_indstr(indent, indent_level, compact)
        for i in obj:
            data += f"{serialize(i, indent=indent, indent_level=indent_level, compact=compact)}"
        indent_level -= 1
        newline, indstr = recompute_indstr(indent, indent_level, compact)
        data += f"{indstr}end{newline}"
        return data
    else:
        error(f"unsupported type {type(obj)}")

def lex(text):
    tokens = []
    n = 0
    while n < len(text):
        if text[n] in "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM":
            buf = ""
            while n < len(text) and text[n] in "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890-+_=(){}[]":
                buf += text[n]
                n += 1
            tokens.append(buf)

        elif text[n] == '"':
            n += 1
            buf = ""
            while n < len(text) and text[n] != '"':
                if text[n] == '\\':
                    n += 1
                    if text[n] == 'n': buf += "\n"
                    elif text[n] == 'r': buf += "\r"
                    elif text[n] == 't': buf += "\t"
                    elif text[n] == '"': buf += '"'
                    elif text[n] == '\\': buf += "\\"
                    elif text[n] == 'x':
                        n += 2
                        hex_code = text[n-1:n]
                        check_hex(hex_code)
                        buf += bytes.fromhex(hex_code).decode()
                    else:
                        error(f"unknown escape: '\\{text[n]}'")
                else:
                    buf += text[n]
                
                n += 1
            tokens.append(buf)
        
        elif text[n] in "1234567890-":
            buf = ""
            while n < len(text) and text[n] in "-1234567890.":
                buf += text[n]
                n += 1
            tokens.append(buf)

        elif text[n] in " \t\r\n":
            n += 1
            continue
        
        else:
            error(f"unparseable token '{text[n]}'")

        n += 1
    
    return tokens

def parse_ends(tokens):
    new_tokens = []
    end_stack = []
    for k, i in enumerate(tokens):
        if i in ("dict", "array"):
            end_stack.append([k, i])
            new_tokens.append([i])
        elif i == "end":
            if len(end_stack) == 0:
                error("unexpected `end`")
            a = end_stack.pop()
            new_tokens[a[0]].append(k)
            new_tokens.append([i])
        else:
            new_tokens.append([i])

    if len(end_stack) != 0:
        error(f"unclosed blocks: {', '.join([i[1] for i in end_stack])}")

    return new_tokens

class RealNone:
    pass # dont ask please

def parse_block(tokens, index=0):
    n = 0
    while n < len(tokens):
        if tokens[n][0] == "dict":
            dict_content = tokens[n+1:tokens[n][1]-index]
            result = {}

            n1 = 0
            state = "key"
            key = None
            while n1 < len(dict_content):
                if dict_content[n1][0] == "key" and state == dict_content[n1][0]:
                    state = "value"
                    n1 += 1
                    key, read = parse_block(dict_content[n1:], index=n+n1)
                    n1 += read

                elif dict_content[n1][0] == "value" and state == dict_content[n1][0]:
                    state = "key"
                    n1 += 1
                    result[key], read = parse_block(dict_content[n1:], index=n+n1)
                    n1 += read
                else:
                    print(dict_content)
                    error(f"expected {state}, but got {dict_content[n1][0]}")
            
            n += 2 + n1
            return result, n
        elif tokens[n][0] == "array":
            arr_content = tokens[n+1:tokens[n][1]-index]
            result = []

            n1 = 0
            while n1 < len(arr_content):
                result_value, read = parse_block(arr_content[n1:], index=n+n1)
                if result_value is None:
                    n1 += read
                    continue
                if result_value == RealNone: result_value = None
                n1 += read
                result.append(result_value)
            n += 2 + n1
            return result, n

        elif tokens[n][0] == "string":
            n += 1
            return tokens[n][0], n + 1
        
        elif tokens[n][0] == "integer":
            n += 1
            if not isint(tokens[n][0]):
                error(f"not an integer: {tokens[n][0]}")
            return int(tokens[n][0]), n + 1
        
        elif tokens[n][0] == "float":
            n += 1
            if not isfloat(tokens[n][0]):
                error(f"not a float: {tokens[n][0]}")
            return float(tokens[n][0]), n + 1
        
        elif tokens[n][0] == "bool":
            n += 1
            if tokens[n][0] not in ("true", "false"):
                error(f"not a bool: {tokens[n][0]}")
            return tokens[n][0] == "true", n + 1
        
        elif tokens[n][0] == "none": return RealNone, n + 1
        
        elif tokens[n][0] == "end": return None, n + 1

        else:
            error(f"unknown word: {tokens[n][0]}")

def parse(text: str) -> any:
    """
    parses krml to python object
    throws ValueError on error
    """
    words = lex(text)
    tokens = parse_ends(words)
    return parse_block(tokens)[0]

def print_help(program):
    print(f"usage: {program} <operation> <operand>")
    print( "  operations:")
    print( "    serialize: convert json to krml")
    print( "      operand: json file (*.json) path or `-` for stdin")
    print( "    parse: convert krml to json")
    print( "      operand: krml file (*.kr) path or `-` for stdin")

def parse_args(args):
    program = args.pop(0)
    if len(args) == 0:
        print_help(program)
        error("expected operation")
    
    operation = args.pop(0)
    ops = ("serialize", "parse")
    if operation not in ops:
        print_help(program)
        error("invalid operation")

    operation = ops.index(operation)

    if len(args) == 0:
        print_help(program)
        error("expected operand")
    
    operand = args.pop(0)

    return operation, operand

if __name__ == "__main__":
    operation, operand = parse_args(sys.argv)
    if operation == 0:
        print(serialize(json.loads((sys.stdin if operand == "-" else open(operand)).read())))
    elif operation == 1:
        print(json.dumps(parse((sys.stdin if operand == "-" else open(operand)).read())))

