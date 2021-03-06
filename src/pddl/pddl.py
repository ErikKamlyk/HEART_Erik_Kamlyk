import copy

class Type:
    def __init__(self, name, parent_type=None):
        self.name = name
        self.parent_type = parent_type

class Object:
    def __init__(self, name, type=None):
        self.name = name
        self.type = type
    def __repr__(self):
        return(self.name)

class Predicate:
    def __init__(self, name, signature):
        self.name = name
        self.signature = signature
    def equal(self, predicate):
        if predicate.name == self.name and predicate.signature == self.signature:
            return True
        else:
            return False
    def __eq__(self, other):
        if other.name == self.name and other.signature == self.signature:
            return True
        return False
    def __repr__(self):
        return(self.name + str(self.signature))
    __str__ = __repr__

class Method:
    def __init__(self, vertices, causal_links):
        self.vertices = vertices.copy()
        self.causal_links = causal_links.copy()

class Action:
    def __init__(self, name, parameters, pre, eff_pos, eff_neg, method=None):
        self.name = name
        self.parameters = parameters
        self.pre = pre
        self.eff_pos = eff_pos
        self.eff_neg = eff_neg
        self.method = method
        self.level = -1

class Domain:
    actions = []
    def __init__(self, name, types, predicates, constants, actions):
        self.name = name
        self.types = types
        self.predicates = predicates
        self.constants = constants
        self.actions = actions
    def print(self):
        print("Domain:")
        print("name: " + self.name)
        for type in self.types:
            if type.parent_type != None:
                print("type:", type.name, type.parent_type.name)
            else:
                print("type:", type.name)
        for predicate in self.predicates:
            print("predicate:", predicate.name, predicate.signature)
        print()
        for action in self.actions:
            print("action:", action.name)
            print("action level:", action.level)
            print("parameters:", action.parameters)
            print("preconditions:", action.pre)
            print("effects_pos:", action.eff_pos)
            print("effects_neg:", action.eff_neg)
            subactions = ""
            if action.method != None:
                for vertice in action.method.vertices:
                    if vertice[0].name != 'init' and vertice[0].name != 'goal':
                        subactions += vertice[0].name + " "
                print("subactions:", subactions)
            print()

class Problem:
    def __init__(self, name, domain, objects, init, goal, root_operator=None):
        self.name = name
        self.domain = domain
        self.objects = objects
        self.init = init
        self.goal = goal
        self.root_operator = root_operator
    def print(self):
        print("Problem:")
        print("name: " + self.name)
        print("domain name:", self.domain.name)
        for object in self.objects:
            print("object:", object, "-", object.type.name)
        print()
        print("Init:")
        for elem in self.init:
            print(elem)
        print("Goal:")
        for elem in self.goal:
            print(elem)