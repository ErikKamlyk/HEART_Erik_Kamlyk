import re
import argparse
from src.pddl.pddl import Domain, Action, Type, Predicate, Problem


def get_text(start_word, text):
    pos_start = text.find(start_word)
    pos_end = pos_start
    bracket_balance = 0
    while bracket_balance >= 0:
        pos_end += 1
        if text[pos_end] == '(':
            bracket_balance += 1
        elif text[pos_end] == ')':
            bracket_balance -= 1
    return text[pos_start:pos_end]

def split_paranthesis(text):
    str = ""
    in_bracket = False
    list = []
    for char in text:
        if char == '(':
            str = ""
            in_bracket = True
        elif char == ')':
            list.append(str)
            in_bracket = False
        elif in_bracket:
            str += char
    return list


class Parser:
    def __init__(self, domain_path):
        self.domain_path = domain_path

    def parse_domain(self):
        file_text = open(self.domain_path, "r").read()
        pos_start = file_text.find('domain')
        domain_name = file_text[pos_start:file_text.find(')', pos_start)].split()[1]

        def parse_types(text):
            types = []
            for word in text.split():
                if word[0] != ':' and word[0] != '-':
                    new_type = Type(word)
                    types.append(new_type)
            return types

        def parse_predicates(text):
            predicates = []
            for str in split_paranthesis(text):
                new_predicate = Predicate(str.split()[0], str.split()[1:])
                predicates.append(new_predicate)
            return predicates

        def parse_action(text):
            action_name = text.split()[1]

            pos_start = text.find(':parameters')
            pos_start = text.find('(', pos_start)
            pos_end = text.find(')', pos_start)
            parameters = text[pos_start + 1:pos_end].split()

            pos_start = text.find(':precondition')
            precond_text = get_text('(', text[pos_start:])
            preconditions = split_paranthesis(precond_text[1:])

            pos_start = text.find(':effect')
            effect_text = get_text('(', text[pos_start:])
            effects = split_paranthesis(effect_text[1:])

            action = Action(action_name, parameters, preconditions, effects)
            return action

        actions = []
        for pos in [s.start() for s in re.finditer(':action', file_text)]:
            actions.append(parse_action(get_text(':action', file_text[pos:])))
        types = []
        if file_text.find(':types') != -1:
            types = parse_types(get_text(':types', file_text))
        predicates = []
        if file_text.find(':predicates') != -1:
            predicates = parse_predicates(get_text(':predicates', file_text))
        domain = Domain(domain_name, types, predicates, actions)
        return domain

    def parse_problem(self, domain, problem_path):
        file_text = open(problem_path, "r").read()
        pos_start = file_text.find('problem')
        problem_name = file_text[pos_start:file_text.find(')', pos_start)].split()[1]

        def parse_objects(text):
            objects = []
            for word in text.split():
                if word[0] != ':' and word[0] != '-':
                    objects.append(word)
            return objects

        def parse_init(text):
            init = []
            for str in split_paranthesis(text):
                init.append(str)
            return init

        def parse_goal(text):
            goal_text = get_text('(', text)
            goal = split_paranthesis(goal_text[1:])
            return goal

        objects = []
        if file_text.find(':objects') != -1:
            objects = parse_objects(get_text(':objects', file_text))
        init = parse_init(get_text(':init', file_text))
        goal = parse_goal(get_text(':goal', file_text))
        problem = Problem(problem_name, domain, objects, init, goal)
        return problem


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument(dest='domain', help='specify domain file')
    args.add_argument(dest='problem', help='specify problem file')
    options = args.parse_args()
    parser = Parser(options.domain)
    domain = parser.parse_domain()
    domain.print()
    problem = parser.parse_problem(domain, options.problem)
    problem.print()