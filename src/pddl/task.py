
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
        self.method = action.method
        self.level = action.level
        self.str = self.name
        for parameter in self.parameters:
            self.str += " " + parameter.name
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
    def __repr__(self):
        str = "\n"
        for operator in self.operators:
            str += operator.__repr__()
            str += '\n'
        return str