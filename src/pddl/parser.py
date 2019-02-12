import re
import argparse
from src.pddl.pddl import Domain, Action, Type, Predicate, Problem, Object, Method


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
    bracket_balance = 0
    list = []
    for char in text:
        if char == '(':
            if bracket_balance == 0:
                str = ""
            bracket_balance += 1
        elif char == ')':
            bracket_balance -= 1
            if bracket_balance == 0 and str != "":
                list.append(str)
        elif bracket_balance > 0:
            str += char
    return list

def find_type(name, types):
    for type in types:
        if type.name == name:
            return type
    return None

def find_predicate(name, predicates):
    for predicate in predicates:
        if predicate.name == name:
            return predicate
    return None

def find_object(name, objects):
    for object in objects:
        if object.name == name:
            return object
    return None

def find_action(name, actions):
    for action in actions:
        if action.name == name:
            return action
    return None

class Parser:
    def __init__(self, domain_path):
        self.domain_path = domain_path

    def parse_domain(self):
        file_text = open(self.domain_path, "r").read()
        file_text = file_text.lower()
        pos_start = file_text.find('domain')
        domain_name = file_text[pos_start:file_text.find(')', pos_start)].split()[1]
        types = set()
        actions = []
        predicates = set()
        constants = set()

        def parse_types(text):
            types = set()
            lines = text.split('\n')
            for line in lines:
                words = line.split()
                parent_type = None
                if len(words) > 2 and words[len(words) - 2] == "-":
                    parent_type = find_type(words[len(words) - 1], types)
                    if parent_type == None:
                        parent_type = Type(words[len(words) - 1])
                        types.add(parent_type)
                    words = words[:len(words) - 2]
                for word in words:
                    if word[0] != ':' and word[0] != '-':
                        new_type = find_type(word, types)
                        if new_type == None:
                            new_type = Type(word, parent_type)
                        if new_type.parent_type == None and parent_type != None:
                            new_type.parent_type = parent_type
                        types.add(new_type)
            return types

        def parse_constants(text):
            constants = set()
            current_type = None
            for word in reversed(text.split()):
                if find_type(word):
                    current_type = find_type(word, types)
                elif word != "-":
                    constants.add(Object(word, current_type))
            return constants

        def parse_predicates(text):
            predicates = set()
            for str in split_paranthesis(text):
                parameters_words = str.split()[1:]
                parameters = []
                current_type = None
                for elem in reversed(parameters_words):
                    if elem[0] == '?':
                        parameters.append(Object(elem, current_type))
                    elif elem[0] != '-':
                        current_type = find_type(elem, types)
                new_predicate = Predicate(str.split()[0], parameters)
                predicates.add(new_predicate)
            return predicates

        def parse_action(text):
            action_name = text.split()[1]

            pos_start = text.find(':parameters')
            pos_start = text.find('(', pos_start)
            pos_end = text.find(')', pos_start)
            parameters_words = text[pos_start + 1:pos_end].split()
            parameters = []
            current_type = None
            for elem in reversed(parameters_words):
                if elem[0] == '?':
                    parameters.append(Object(elem, current_type))
                elif elem[0] != '-':
                    current_type = find_type(elem, types)
            parameters.reverse()

            pos_start = text.find(':precondition')
            precond_text = get_text('(', text[pos_start:])
            preconditions = []
            preconditions_lines = split_paranthesis(precond_text[1:])
            for line in preconditions_lines:
                predicate = find_predicate(line.split()[0], predicates)
                predicate_parameters = []
                for object in line.split()[1:]:
                    predicate_parameters.append(find_object(object, parameters))
                preconditions.append((predicate, predicate_parameters))

            pos_start = text.find(':effect')
            effect_text = get_text('(', text[pos_start:])
            effects_pos = []
            effects_neg = []
            effects_lines = split_paranthesis(effect_text[1:])
            for line in effects_lines:
                positive = True
                words = line.split()
                if line[:3] == "not":
                    positive = False
                    words = words[1:]
                predicate = find_predicate(words[0], predicates)
                predicate_parameters = []
                for object in words[1:]:
                    predicate_parameters.append(find_object(object, parameters))
                if positive:
                    effects_pos.append((predicate, predicate_parameters))
                else:
                    effects_neg.append((predicate, predicate_parameters))

            if text.find(':method') != -1:
                pos_start = text.find(':method')
                method_text = get_text('(', text[pos_start:])
                method_lines = split_paranthesis(method_text[1:])
                vertices = []
                causal_links = [[0]*(len(method_lines)*2)]*(len(method_lines)*2)
                for line in method_lines:
                    first_action_line = line.split(' -> ')[0]
                    second_action_line = line.split(' -> ')[1]
                    vertice = None
                    first_action = None
                    if first_action_line.split()[0] != 'init':
                        first_action = find_action(first_action_line.split()[0], actions)
                        vertice = (first_action, first_action_line.split()[1:])
                    else:
                        first_action = Action('init', None, None, None, None)
                        vertice = (first_action, [])
                    index1 = -1
                    for i in range(len(vertices)):
                        if vertices[i] == vertice:
                            index1 = i
                    if index1 == -1:
                        vertices.append(vertice)
                        index1 = len(vertices) - 1
                    second_action = None
                    if second_action_line.split()[0] != 'goal':
                        second_action = find_action(second_action_line.split()[0], actions)
                        vertice = (second_action, second_action_line.split()[1:])
                    else:
                        second_action = Action('goal', None, None, None, None)
                        vertice = (second_action, [])
                    index2 = -1
                    for i in range(len(vertices)):
                        if vertices[i] == vertice:
                            index2 = i
                    if index2 == -1:
                        vertices.append(vertice)
                        index2 = len(vertices) - 1
                    causal_links[index1][index2] = 1
                method = Method(vertices, causal_links)
                action = Action(action_name, parameters, preconditions, effects_pos, effects_neg, method)
            else:
                action = Action(action_name, parameters, preconditions, effects_pos, effects_neg)
            return action

        def get_action_hierarchy(actions):
            current_level = 0
            new_current_level = 1
            for action in actions:
                if action.method == None:
                    action.level = 0
            while new_current_level != current_level:
                current_level = new_current_level
                for action in actions:
                    if action.method != None:
                        max_subaction_level = -1
                        for vertice in action.method.vertices:
                            if vertice[0].level > max_subaction_level:
                                max_subaction_level = vertice[0].level
                        action.level = max_subaction_level + 1
                        if action.level > new_current_level:
                            new_current_level = action.level



        if file_text.find(':types') != -1:
            types = parse_types(get_text(':types', file_text))
        else:
            types.add(Type("any"))
        if file_text.find(':constants') != -1:
            constants = parse_constants(get_text(':constants', file_text))
        if file_text.find(':predicates') != -1:
            predicates = parse_predicates(get_text(':predicates', file_text))
        for pos in [s.start() for s in re.finditer(':action', file_text)]:
            actions.append(parse_action(get_text(':action', file_text[pos:])))
        get_action_hierarchy(actions)
        domain = Domain(domain_name, types, predicates, constants, actions)
        return domain

    def parse_problem(self, domain, problem_path):
        file_text = open(problem_path, "r").read()
        file_text = file_text.lower()
        pos_start = file_text.find('problem')
        problem_name = file_text[pos_start:file_text.find(')', pos_start)].split()[1]
        objects = set()

        def parse_objects(text):
            objects = set()
            current_type = None
            for word in reversed(text.split()):
                if find_type(word, domain.types):
                    current_type = find_type(word, domain.types)
                elif word != "-":
                    objects.add(Object(word, current_type))
            return objects

        def parse_init(text):
            init = []
            for str in split_paranthesis(text):
                predicate = find_predicate(str.split()[0], domain.predicates)
                parameters = []
                for word in str.split()[1:]:
                    parameters.append(find_object(word, objects))
                init.append((predicate, parameters))
            return init

        def parse_goal(text):
            goal_text = get_text('(', text)
            goal = []
            for elem in split_paranthesis(goal_text[1:]):
                predicate = find_predicate(elem.split()[0], domain.predicates)
                parameters = []
                for word in elem.split()[1:]:
                    parameters.append(find_object(word, objects))
                goal.append((predicate, parameters))
            return goal

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