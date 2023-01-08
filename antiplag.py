#!/usr/bin/python
import argparse
import ast
import multiprocessing as mp
import numpy as np


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

    return d[lenstr1][lenstr2] / max(lenstr1, lenstr2)


class AntiPlagiarism:
    class LevensteinLower(ast.NodeTransformer):
        def visit_arg(self, node):
            return ast.arg(**{**node.__dict__, 'arg': 'a'})

        def visit_Name(self, node):
            return ast.Name(**{**node.__dict__, 'id': 'N'})

    def __init__(self, metrics):
        self.__metrics = metrics
        self.metric_results = {}

    def __load_files(self, first_filename, second_filename):
        """Load files from filenames and parse them"""
        with open(first_filename, "r") as first_file,\
                open(second_filename, "r") as second_file:
            self.first_code = ast.parse(first_file.read())
            self.second_code = ast.parse(second_file.read())

    def __normalize(self, root_node):
        """Getting rid of comments and docstrings"""

        for node in ast.walk(root_node):
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
        return ast.unparse(self.LevensteinLower().visit(root_node))

    def __get_normalized_code(self):
        return self.__normalize(self.first_code),\
            self.__normalize(self.second_code)

    def Compare(self, first_filename, second_filename):
        self.__load_files(first_filename, second_filename)
        self.metric_results.clear()
        for i in self.__metrics:
            self.metric_results[i.__name__] = i(*self.__get_normalized_code())
        return round(1 - sum(self.metric_results.values()) /
                     len(self.metric_results), 2)


results = []  # TODO: Get rid of global variable


def end_func(response):
    """Collecting results of all processes"""
    results.extend(response)


def worker(line):
    """Compare two filenames from one line"""
    comparator = AntiPlagiarism([damerau_levenshtein_distance])
    return comparator.Compare(*line.split())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compares python files and produces similarity")
    parser.add_argument("input")
    parser.add_argument("scores")
    args = parser.parse_args()

    filename_pairs = []

    with open(args.input, "r") as r:
        for line in r.readlines():
            filename_pairs.append(line)

    with mp.Pool(mp.cpu_count()) as p:
        p.map_async(worker, filename_pairs, callback=end_func)
        p.close()
        p.join()

    with open(args.scores, "w") as w:
        w.write('\n'.join(str(i) for i in results))
