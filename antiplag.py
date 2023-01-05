#!/usr/bin/python
import argparse
import ast
import numpy as np


class LevensteinLower(ast.NodeTransformer):
    def visit_arg(self, node):
        return ast.arg(**{**node.__dict__, 'arg': 'a'})

    def visit_Name(self, node):
        return ast.Name(**{**node.__dict__, 'id': 'N'})


def damerau_levenshtein_distance(s1, s2):
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    d = np.zeros((lenstr1 + 1, lenstr2 + 1))

    for i in range(lenstr1 + 1):
        for j in range(lenstr2 + 1):
            if i > 1 and j > 1 and\
               s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1,
                              d[i - 1][j - 1] +
                              (1 if s1[i - 1] != s2[j - 1] else 0),
                              d[i - 2][j - 2] + 1)
            if i > 0 and j > 0:
                d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1,
                              d[i - 1][j - 1] +
                              (1 if s1[i - 1] != s2[j - 1] else 0))
            elif i > 0:
                d[i][j] = d[i - 1][j] + 1
            elif j > 0:
                d[i][j] = d[i][j - 1] + 1
            else:
                d[i][j] = 0

    return d[lenstr1][lenstr2]


def ast_normalize(filename):
    with open(filename) as f:
        code = f.read()
    parsed = ast.parse(code)  # Getting rid of comments

    # Getting rid of docstrings
    for node in ast.walk(parsed):
        if not isinstance(node, (ast.FunctionDef,
                                 ast.ClassDef,
                                 ast.AsyncFunctionDef)):
            continue
        if not len(node.body):
            continue
        if not isinstance(node.body[0], ast.Expr):
            continue
        if not hasattr(node.body[0], 'value') or\
           not isinstance(node.body[0].value, ast.Str):
            continue
        node.body = node.body[1:]
    return ast.unparse(LevensteinLower().visit(parsed))


def files_comparator(first_filename, second_filename):
    return round(1 - damerau_levenshtein_distance(
                 x := ast_normalize(first_filename),
                 y := ast_normalize(second_filename)) / max(len(x),
                                                            len(y)),
                 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compares python files and produces similarity")
    parser.add_argument("input")
    parser.add_argument("scores")
    args = parser.parse_args()
    with open(args.input, "r") as r, open(args.scores, "w") as w:
        for line in r.readlines():
            w.write(str(files_comparator(*line.split())))
            w.write("\n")
