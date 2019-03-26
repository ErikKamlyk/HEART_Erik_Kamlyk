import time
import copy

class CausalLink:
    def __init__(self, step1, step2, predicate):
        self.step1 = step1
        self.step2 = step2
        self.predicate = predicate
        self.threats = None
    def __repr__(self):
        return self.step1.__repr__() + "\t" + self.step2.__repr__() + "\t" + self.predicate.__repr__()

class Subgoal:
    def __init__(self, precondition, goal):
        self.precondition = precondition
        self.goal = goal
    def __repr__(self):
        str = ""
        str += self.precondition.__repr__()
        str += self.goal.__repr__()
        return str

class SubgoalResolver:
    def __init__(self, operator, step):
        if operator:
            self.operator = operator
            self.step = None
        elif step:
            self.step = step
            self.operator = None
    def __repr__(self):
        if self.operator:
            return "operator " + self.operator.__repr__()
        else:
            return "new_step " + self.step.__repr__()

class ThreatResolver:
    def __init__(self, step1, step2):
        self.step1 = step1
        self.step2 = step2
    def __repr__(self):
        return self.step1.__repr__() + " " + self.step2.__repr__()

class Threat:
    def __init__(self, link, step):
        self.link = link
        self.step = step
    def __eq__(self, other):
        return (self.step.num == other.step.num and self.link.predicate == other.link.predicate
                and self.link.step1 == other.link.step1 and self.link.step2 == other.link.step2)
    def __repr__(self):
        return self.step.__repr__() + " " + self.link.step1.__repr__() + " " + self.link.step2.__repr__() + " " + self.link.predicate.__repr__()

class Decomp_flaw:
    def __init__(self, step_num):
        self.step_num = step_num

class Changes:
    def __init__(self):
        self.deleted_flaw = None
        self.new_step = None
        self.new_link = None
        self.new_subgoals = []
        self.new_threats = []
        self.invalidated_threats = []
        self.new_order = None
        self.old_threats = None
        self.new_decomp_flaw = None

class Agenda:
    def __init__(self, goal):
        self.subgoals = []
        for precondition in goal.operator.pre:
            self.subgoals.append(Subgoal(precondition, goal))
        self.threats = []
        self.decomp_flaws = []
    def insert(self, f):
        if type(f) == Subgoal:
            self.subgoals.append(f)
        elif type(f) == Threat:
            self.threats.append(f)
    def remove(self, f):
        if type(f) == Subgoal:
            self.subgoals.remove(f)
        elif type(f) == Threat:
            self.threats.remove(f)
    def empty(self):
        return ((len(self.subgoals) + len(self.threats) + len(self.decomp_flaws)) == 0)
    def __repr__(self):
        str = "subgoals: "
        for subgoal in self.subgoals:
            str += " " + subgoal.__repr__()
        str += ", threats: "
        for threat in self.threats:
            str += " " + threat.__repr__()
        return str

class Step:
    def __init__(self, operator, num):
        self.operator = operator
        self.name = operator.name
        self.num = num
    def __repr__(self):
        return self.operator.__repr__()
    def __eq__(self, other):
        return ((self.operator == other.operator) and (self.name == other.name))

class Plan:
    def __init__(self, task, init, goal, max_level = 0):
        self.task = task
        self.operators_free = task.operators.copy()
        self.operators_not_free = []
        self.objects = task.objects
        self.steps = []
        self.init = Step(init, 0)
        self.goal = Step(goal, 1)
        self.steps.append(self.init)
        self.steps.append(self.goal)
        self.order_less = {}
        self.order_more = {}
        self.order_less[1] = set()
        self.order_less[1].add(0)
        self.order_more[0] = set()
        self.order_more[0].add(1)
        self.causal_links = []
        self.agenda = Agenda(self.goal)
        self.max_steps = 2
        self.reached_max = False
        self.max_level = max_level
        self.heuristic = task.heuristic
    def get_n_steps(self):
        i = 0
        for key in self.order_more.keys():
            i += len(self.order_more[key])
        return i
    def isless(self, step_num_1, step_num_2, i = 0):
        if step_num_1 == self.goal.num:
            return 0
        if step_num_2 == self.init.num:
            return 0
        if i > self.get_n_steps():
            return -1
        if step_num_1 in self.order_more.keys():
            for next_step in self.order_more[step_num_1]:
                if next_step == step_num_2:
                    return 1
                if self.isless(next_step, step_num_2, i + 1):
                    return 1
        return 0
    def hiddenisless(self, step_num_1, step_num_2):
        if step_num_2 in self.final_order_more[step_num_1]:
            return True
    def add_order(self, step_num_1, step_num_2, building_order=False):
        if step_num_1 not in self.order_more.keys():
            self.order_more[step_num_1] = set()
        if step_num_2 not in self.order_less.keys():
            self.order_less[step_num_2] = set()
        if step_num_2 not in self.order_more.keys():
            self.order_more[step_num_2] = set()
        if step_num_1 not in self.order_less.keys():
            self.order_less[step_num_1] = set()
        if self.isless(step_num_2, step_num_1):
            return (False, False)
        toadd = True
        if step_num_2 in self.order_more[step_num_1]:
            toadd = False
        if toadd:
            self.order_more[step_num_1].add(step_num_2)
            self.order_less[step_num_2].add(step_num_1)
        return (True, toadd)
    def delete_order(self, step_num_1, step_num_2):
        if step_num_1 in  self.order_more:
            self.order_more[step_num_1].discard(step_num_2)
        if step_num_2 in self.order_less:
            self.order_less[step_num_2].discard(step_num_1)
    def build_order(self):
        s = time.time()
        # self.final_order_more = {}
        # for step1 in self.steps:
        #     self.final_order_more[step1.num] = []
        #     for step2 in self.steps:
        #         if step1.num != step2.num and self.hiddenisless(step1.num, step2.num):
        #             self.final_order_more[step1.num].append(step2.num)
        # e = time.time()
        #print("time3 ", e - s)
    def add_operator(self, operator):
        self.task.operators.append(operator)
        self.order_less[operator] = set()
        self.order_more[operator] = set()
    def add_step(self, step):
        self.steps.append(step)
        self.operators_free.remove(step.operator)
        self.operators_not_free.append(step.operator)
    def delete_step(self, step):
        self.steps.remove(step)
        self.order_less.pop(step.num, None)
        self.order_more.pop(step.num, None)
        for key in self.order_less.keys():
            self.order_less[key].discard(step.num)
        for key in self.order_more.keys():
            self.order_more[key].discard(step.num)
        self.operators_free.append(step.operator)
        self.operators_not_free.remove(step.operator)

class Solution:
    def __init__(self, plan):
        self.steps = []
        self.plan = plan
        self.plan_steps = copy.deepcopy(plan.steps)
    def get_sol(self):
        self.steps.append(self.plan.init.num)
        self.plan_steps.remove(self.plan_steps[0])
        while self.plan.goal.num not in self.steps:
            for step in self.plan_steps:
                if set(self.plan.order_less[step.num]) <= set(self.steps):
                    self.steps.append(step.num)
                    self.plan_steps.remove(step)
        return self.steps