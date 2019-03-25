import copy
from src.pddl.pddl import Method

from src.pddl.pddl import Predicate

def initialize_predicate(predicate, dict):
    predicate_parameters = []
    for param in predicate[1]:
        predicate_parameters.append(dict[param])
    return Predicate(predicate[0].name, predicate_parameters)

class Operator:
    def __init__(self, action, chosen_objects):
        self.name = action.name
        self.action = action
        self.parameters = chosen_objects
        dict = {}
        for i in range(len(action.parameters)):
            dict[action.parameters[i]] = chosen_objects[i]
        self.pre = []
        for precondition in action.pre:
            self.pre.append(initialize_predicate(precondition, dict))
        self.eff_pos = []
        for eff_pos in action.eff_pos:
            self.eff_pos.append(initialize_predicate(eff_pos, dict))
        self.eff_neg = []
        for eff_neg in action.eff_neg:
            self.eff_neg.append(initialize_predicate(eff_neg, dict))
        self.method = None
        if action.method:
            self.method = Method(action.method.vertices, action.method.causal_links)
            for i in range(len(self.method.vertices)):
                grounded_parameters = []
                for parameter in self.method.vertices[i][1]:
                    grounded_parameters.append(dict[parameter])
                self.method.vertices[i] = (self.method.vertices[i][0], grounded_parameters)
        self.level = action.level
        self.str = self.name
        for parameter in self.parameters:
            self.str += " " + parameter.name
    # def __eq__(self, other):
    #     return self.name == other.name and self.parameters == other.parameters and self.action == other.action
    def __repr__(self):
        return self.name + self.parameters.__repr__()

class Task:
    def __init__(self, name, domain, facts, objects, init, goals, operators):
        self.name = name
        self.domain = domain
        self.facts = facts
        self.objects = objects
        self.init = init
        self.goals = goals
        self.operators = operators
        self.subgoal_resolvers = {}
        self.max_level = 0
        for operator in operators:
            if operator.level > self.max_level:
                self.max_level = operator.level
    def __repr__(self):
        str = "\n"
        for operator in self.operators:
            str += "operator " + operator.__repr__()
            str += '\n'
        return str