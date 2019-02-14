
class CausalLink:
    def __init__(self, step1, step2, predicate):
        self.step1 = step1
        self.step2 = step2
        self.predicate = predicate
    def __repr__(self):
        return self.step1.__repr__() + " " + self.step2.__repr__() + " " + self.predicate.__repr__()

class Subgoal:
    def __init__(self, precondition, goal):
        self.precondition = precondition
        self.goal = goal
    def __repr__(self):
        str = ""
        str += self.precondition.__repr__()
        str += self.goal.__repr__()
        return str

class ThreatResolver:
    def __init__(self, step1, step2):
        self.step1 = step1
        self.step2 = step2

class Threat:
    def __init__(self, link, step):
        self.link = link
        self.step = step
    def __repr__(self):
        return self.step.__repr__() + " " + self.link.step1.__repr__() + " " + self.link.step2.__repr__() + " " + self.link.predicate.__repr__()

class Agenda:
    def __init__(self, goal):
        self.subgoals = set()
        for precondition in goal.operator.pre:
            self.subgoals.add(Subgoal(precondition, goal))
        self.threats = set()
    def insert(self, f):
        if type(f) == Subgoal:
            self.subgoals.add(f)
        elif type(f) == Threat:
            self.threats.add(f)
    def remove(self, f):
        if type(f) == Subgoal:
            self.subgoals.remove(f)
        elif type(f) == Threat:
            self.threats.remove(f)
    def empty(self):
        return ((len(self.subgoals) + len(self.threats)) == 0)
    def __repr__(self):
        str = ""
        for subgoal in self.subgoals:
            str += " " + subgoal.__repr__()
        for threat in self.threats:
            str += " " + threat.__repr__()
        return str

class Step:
    def __init__(self, operator):
        self.operator = operator
        self.name = operator.name
    def __repr__(self):
        return self.operator.__repr__()

class Plan:
    def __init__(self, task, init, goal):
        self.task = task
        self.objects = task.objects
        self.steps = {}
        self.init = Step(init)
        self.goal = Step(goal)
        self.steps[self.init.__repr__()] = [self.init]
        self.steps[self.goal.__repr__()] = [self.goal]
        self.order = []
        self.order.append((self.init, self.goal))
        self.order_less = {}
        self.order_more = {}
        self.order_more[self.init] = set()
        self.order_more[self.init].add(self.goal)
        self.order_less[self.goal] = set()
        self.order_less[self.goal].add(self.init)
        self.causal_links = set()
        self.agenda = Agenda(self.goal)
        print(self.agenda)
    def get_n_steps(self):
        i = 0
        for key in self.order_more.keys():
            i += len(self.order_more[key])
        return i
    def isless(self, step1, step2, i = 0):
        if i > self.get_n_steps():
            return -1
        for next_step in self.order_more[step1]:
            if next_step == step2:
                return 1
            if self.isless(next_step, step2, i + 1):
                return 1
        return 0
    def add_order(self, step1, step2, building_order=False):
        if step1 not in self.order_more.keys():
            self.order_more[step1] = set()
        if step2 not in self.order_less.keys():
            self.order_less[step2] = set()
        if step2 not in self.order_more.keys():
            self.order_more[step2] = set()
        if step1 not in self.order_less.keys():
            self.order_less[step1] = set()
        if self.isless(step2, step1):
            return False
        if not building_order:
            toadd = True
            for ordering in self.order:
                if ordering[0] == step1 and ordering[1] == step2:
                    toadd = False
            if toadd:
                self.last_add = (step1, step2)
                self.order.append(self.last_add)
        self.order_more[step1].add(step2)
        self.order_less[step2].add(step1)
        return True
    def build_order_dicts(self):
        self.order_less = {}
        self.order_more = {}
        self.order_more[self.init] = set()
        self.order_more[self.init].add(self.goal)
        self.order_less[self.goal] = set()
        self.order_less[self.goal].add(self.init)
        for ordering in self.order:
            self.add_order(ordering[0], ordering[1], True)
    def add_operator(self, operator):
        self.task.operators.append(operator)
        self.order_less[operator] = set()
        self.order_more[operator] = set()
    def add_step(self, step):
        if step.__repr__() not in self.steps.keys():
            self.steps[step.__repr__()] = []
        step.name += str(len(self.steps[step.__repr__()]))
        self.steps[step.__repr__()].append(step)

class Solution:
    def __init__(self, plan):
        self.steps = []
        self.plan = plan
    def get_sol(self):
        self.plan.build_order_dicts()
        self.steps.append(self.plan.init)
        self.plan.steps[self.plan.init.__repr__()].remove(self.plan.init)
        while self.plan.goal not in self.steps:
            for key in self.plan.steps.keys():
                for step in self.plan.steps[key]:
                    if self.plan.order_less[step] <= set(self.steps):
                        self.steps.append(step)
                        self.plan.steps[key].remove(step)
        return self.steps