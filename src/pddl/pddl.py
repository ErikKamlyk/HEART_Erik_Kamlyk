class Type:
    def __init__(self, name, parent_type=None):
        self.name = name
        self.parent_type = parent_type

class Predicate:
    def __init__(self, name, signature):
        self.name = name
        self.signature = signature

class Action:
    def __init__(self, name, parameters, pre, eff):
        self.name = name
        self.parameters = parameters
        self.pre = pre
        self.eff = eff

class Domain:
    actions = []
    def __init__(self, name, types, predicates, actions):
        self.name = name
        self.types = types
        self.predicates = predicates
        self.actions = actions
    def print(self):
        print("Domain:")
        print("name: " + self.name)
        print("types:", self.types)
        for predicate in self.predicates:
            print("predicate:", predicate.name, predicate.signature)
        print()
        for action in self.actions:
            print("action:", action.name)
            print("parameters:", action.parameters)
            print("preconditions:", action.pre)
            print("effects:", action.eff)
            print()

class Problem:
    def __init__(self, name, domain, objects, init, goal):
        self.name = name
        self.domain = domain
        self.objects = objects
        self.init = init
        self.goal = goal
    def print(self):
        print("Problem:")
        print("name: " + self.name)
        print("domain name:", self.domain.name)
        for object in self.objects:
            print("object:", object)
        print()
        print("Init:")
        for elem in self.init:
            print(elem)
        print("Goal:")
        for elem in self.goal:
            print(elem)