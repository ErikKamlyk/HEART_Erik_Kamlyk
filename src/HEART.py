import argparse
import random
import copy
from src.pddl.parser import Parser
from src.pddl.grounding import ground_problem
from src.plan import Plan, Subgoal, Threat, CausalLink, Step, Solution, ThreatResolver, SubgoalResolver, Changes, Decomp_flaw
from src.pddl.pddl import Action
from src.pddl.task import Operator
import time

def solve_flaw(f, plan):
    resolvers = []
    if type(f) is Subgoal:
        cur_max_level = -1
        other_resolvers = []
        for operator in plan.operators_free:
            if f.precondition in operator.eff_pos:
                for eff in operator.eff_pos:
                    if f.precondition.equal(eff):
                        if operator.level > cur_max_level:
                            cur_max_level = operator.level
                            other_resolvers += resolvers
                            resolvers = [SubgoalResolver(operator, None)]
                        elif operator.level == cur_max_level:
                            resolvers.append(SubgoalResolver(operator, None))
                        else:
                            other_resolvers.append(SubgoalResolver(operator, None))
        other_resolvers = []
        # for operator in plan.operators_free:
        #     if f.precondition in operator.eff_pos:
        #     # for eff in operator.eff_pos:
        #     #     if f.precondition.equal(eff):
        #         resolvers.append(SubgoalResolver(operator, None))
        resolvers2 = []
        for step in plan.steps:
            if not plan.isless(f.goal.num, step.num):
                for eff in step.operator.eff_pos:
                    if f.precondition.equal(eff):
                        resolvers2.append(SubgoalResolver(None, step))
        return resolvers, resolvers2, other_resolvers
    elif type(f) is Threat:
        if (f.link.step1.name != "init") and not plan.isless(f.link.step1.num, f.step.num):
            resolvers.append(ThreatResolver(f.step, f.link.step1))
        if (f.link.step2.name != "goal") and not plan.isless(f.step.num, f.link.step2.num):
            resolvers.append(ThreatResolver(f.link.step2, f.step))
    elif type(f) is Decomp_flaw:
        resolvers.append(f)
    return resolvers, [], []

def count_flaws(f, plan):
    result = solve_flaw(f, plan)
    resolvers = [0, 0]
    if type(f) is Subgoal:
        resolvers[0] = len(result[0])
        resolvers[1] = len(result[1])
        return resolvers
    elif type(f) is Threat:
        if (f.link.step1.name != "init") and not plan.isless(f.link.step1.num, f.step.num):
            resolvers.append(ThreatResolver(f.step, f.link.step1))
        if (f.link.step2.name != "goal") and not plan.isless(f.step.num, f.link.step2.num):
            resolvers.append(ThreatResolver(f.link.step2, f.step))
    elif type(f) is Decomp_flaw:
        resolvers.append(f)
    return resolvers, None

def add_new_subgoals(causal_link):
    new_subgoals = []
    for precondition in causal_link.step1.operator.pre:
        new_subgoals.append(Subgoal(precondition, causal_link.step1))
    return new_subgoals

def add_new_threats(plan, causal_link, new_step=None):
    new_threats = []
    for step in plan.steps:
        for eff_neg in step.operator.eff_neg:
            if causal_link.step1 != step and causal_link.step2 != step and eff_neg.equal(causal_link.predicate):
                if not plan.isless(step.num, causal_link.step1.num) and not plan.isless(causal_link.step2.num, step.num):
                    new_threats.append(Threat(causal_link, step))
    if new_step:
        for eff_neg in new_step.operator.eff_neg:
            for link in plan.causal_links:
                if link != causal_link and link.step1 != new_step and link.step2 != new_step and eff_neg.equal(link.predicate):
                    if not plan.isless(new_step.num, link.step1.num) and not plan.isless(link.step2.num, new_step.num):
                        new_threats.append(Threat(link, new_step))
    for threat in new_threats:
        if threat not in plan.agenda.threats:
            plan.agenda.threats.append(threat)
    return new_threats

def delete_invalidated_threats(plan):
    invalidated_threats = []
    for threat in plan.agenda.threats:
        if plan.isless(threat.step.num, threat.link.step1.num) or plan.isless(threat.link.step2.num, threat.step.num):
            invalidated_threats.append(threat)
    for threat in invalidated_threats:
        plan.agenda.threats.remove(threat)
    return invalidated_threats

def apply(resolver, f, plan):
    if type(f) is Subgoal:
        changes = Changes()
        new_step = resolver.step
        if not new_step:
            if len(plan.steps) >= plan.max_steps:
                plan.reached_max = True
                return (False, changes)
            new_step = Step(resolver.operator, len(plan.steps))
            plan.add_step(new_step)
            new_causal_link = CausalLink(new_step, f.goal, f.precondition)
            plan.causal_links.append(new_causal_link)
            changes.new_step = new_step
            changes.new_link = new_causal_link
            add_order_res = plan.add_order(new_step.num, f.goal.num)
            if not add_order_res[0]:
                return (False, changes)
            plan.agenda.subgoals.remove(f)
            changes.deleted_flaw = f
            changes.new_subgoals = add_new_subgoals(new_causal_link)
            changes.new_threats = add_new_threats(plan, new_causal_link, new_step)
            changes.invalidated_threats = delete_invalidated_threats(plan)
            if add_order_res[1]:
                changes.new_order = (new_step.num, f.goal.num)
            plan.agenda.subgoals += changes.new_subgoals
            return (True, changes)
        else:
            new_causal_link = CausalLink(resolver.step, f.goal, f.precondition)
            plan.causal_links.append(new_causal_link)
            changes.new_link = new_causal_link
            add_order_res = plan.add_order(resolver.step.num, f.goal.num)
            if not add_order_res[0]:
                return (False, changes)
            plan.build_order()
            plan.agenda.subgoals.remove(f)
            changes.deleted_flaw = f
            changes.new_threats = add_new_threats(plan, new_causal_link)
            changes.invalidated_threats = delete_invalidated_threats(plan)
            if add_order_res[1]:
                changes.new_order = (resolver.step.num, f.goal.num)
            return (True, changes)
    elif type(f) is Threat:
        changes = Changes()
        add_order_res = plan.add_order(resolver.step1.num, resolver.step2.num)
        if not add_order_res[0]:
            return (False, changes)
        if add_order_res[1]:
            changes.new_order = (resolver.step1.num, resolver.step2.num)
        plan.build_order()
        plan.agenda.threats.remove(f)
        changes.deleted_flaw = f
        changes.invalidated_threats = delete_invalidated_threats(plan)
        return (True, changes)
    elif type(f) is Decomp_flaw:
        changes = Changes()
        old_step_num = f.step_num
        if len(plan.steps) + len(plan.steps[old_step_num].operator.method.vertices) - 3 > plan.max_steps:
            return (False, changes)
        plan.agenda.decomp_flaws.remove(f)
        old_step = plan.steps[old_step_num]
        plan.steps[old_step_num] = Step(plan.steps[old_step_num].operator.method.vertices[1], old_step_num)
        second_in_method_num = len(plan.steps)
        for i in range(2, len(old_step.operator.method.vertices) - 1):
            plan.steps.append(Step(old_step.operator.method.vertices[i], len(plan.steps)))
            plan.build_order()
            if i > 2:
                plan.add_order(len(plan.steps) - 2, len(plan.steps) - 1)
        plan.build_order()
        plan.add_order(old_step_num, second_in_method_num)
        more_than_1 = []
        for num in plan.order_more[old_step_num]:
            if num != second_in_method_num:
                more_than_1.append(num)
        for num in more_than_1:
            plan.delete_order(old_step_num, num)
            plan.build_order()
            plan.add_order(len(plan.steps) - 1, num)
        plan.build_order()
        return (True, changes)

def revert(plan, changes):
    if changes.new_link:
        plan.causal_links.remove(changes.new_link)
    if changes.new_step:
        plan.delete_step(changes.new_step)
    if changes.deleted_flaw:
        plan.agenda.insert(changes.deleted_flaw)
    if len(changes.invalidated_threats) > 0:
        plan.agenda.threats += changes.invalidated_threats
    if changes.new_order:
        plan.delete_order(changes.new_order[0], changes.new_order[1])
    for new_sub in changes.new_subgoals:
        plan.agenda.subgoals.remove(new_sub)
    for new_thr in changes.new_threats:
        plan.agenda.threats.remove(new_thr)

def choose_flaw(plan):
    s = time.time()
    if plan.heuristic == 'rand':
        if len(plan.agenda.threats + plan.agenda.subgoals) > 0:
            f = random.sample(plan.agenda.threats + plan.agenda.subgoals, 1)[0]
        else:
            f = random.sample(plan.agenda.decomp_flaws, 1)[0]
        return f
    if plan.heuristic == 'threat_first':
        if len(plan.agenda.threats) > 0:
            f = random.sample(plan.agenda.threats, 1)[0]
            return f
        elif len(plan.agenda.subgoals) > 0:
            f = random.sample(plan.agenda.subgoals, 1)[0]
        else:
            f = random.sample(plan.agenda.decomp_flaws, 1)[0]
        return f
    if plan.heuristic == 'min_subgoal' or plan.heuristic == 'first_existing_link' or plan.heuristic == 'first_new_step':
        if len(plan.agenda.threats) > 0:
            f = random.sample(plan.agenda.threats, 1)[0]
        elif len(plan.agenda.subgoals) > 0:
            f = None
            min = 1000000
            for subgoal in plan.agenda.subgoals:
                resolvers = count_flaws(subgoal, plan)
                if resolvers[1] == 0:
                    if resolvers[0] < min:
                        f = subgoal
                        min = resolvers[0]
            if min < 1000000:
                e = time.time()
                #print("time ", e - s)
                return f
            f = random.sample(plan.agenda.subgoals, 1)[0]
        else:
            f = random.sample(plan.agenda.decomp_flaws, 1)[0]
        return f
    e = time.time()
    #print("time ", e - s)

def choose_resolver(plan, f, resolvers, resolvers2, other_resolvers):
    r = None
    if type(f) == Threat:
        r = random.sample(resolvers, 1)[0]
        resolvers.remove(r)
        return r
    if type(f) == Decomp_flaw:
        r = resolvers[0]
        resolvers.remove(r)
        return r
    if plan.heuristic == 'rand' or plan.heuristic == 'threat_first' or plan.heuristic == 'min_subgoal':
        r = random.sample(resolvers + resolvers2, 1)[0]
        if r in resolvers:
            resolvers.remove(r)
        elif r in resolvers2:
            resolvers2.remove(r)
        return r
    if plan.heuristic == 'first_existing_link':
        if len(resolvers2) > 0:
            r = random.sample(resolvers2, 1)[0]
            resolvers2.remove(r)
        elif len(resolvers) > 0:
            r = random.sample(resolvers, 1)[0]
            resolvers.remove(r)
            #print(resolvers)
            # max_quality = -1000000
            # for resolver in resolvers:
            #     quality = -len(resolver.operator.pre)
            #     #print(quality)
            #     for precond in resolver.operator.pre:
            #         if precond in plan.init.operator.eff_pos:
            #             quality += 1
            #     #print(quality)
            #     if quality > max_quality:
            #         max_quality = quality
            #         r = resolver
            #print(r)
            #resolvers.remove(r)
        else:
            r = random.sample(other_resolvers, 1)[0]
            other_resolvers.remove(r)
        return r
    if plan.heuristic == 'first_new_step':
        if len(resolvers) > 0:
            r = random.sample(resolvers, 1)[0]
            resolvers.remove(r)
        elif len(resolvers2) > 0:
            r = random.sample(resolvers2, 1)[0]
            resolvers2.remove(r)
            #print(resolvers)
            # max_quality = -1000000
            # for resolver in resolvers:
            #     quality = -len(resolver.operator.pre)
            #     #print(quality)
            #     for precond in resolver.operator.pre:
            #         if precond in plan.init.operator.eff_pos:
            #             quality += 1
            #     #print(quality)
            #     if quality > max_quality:
            #         max_quality = quality
            #         r = resolver
            #print(r)
            #resolvers.remove(r)
        else:
            r = random.sample(other_resolvers, 1)[0]
            other_resolvers.remove(r)
        return r

def pop_solve(plan, counter):
    if plan.agenda.empty():
        return True
    f = choose_flaw(plan)
    flaw_resolvers = solve_flaw(f, plan)
    while (len(flaw_resolvers[0]) > 0 or (len(flaw_resolvers[1]) > 0)) or (len(flaw_resolvers[2]) > 0):
        r = choose_resolver(plan, f, flaw_resolvers[0], flaw_resolvers[1], flaw_resolvers[2])
        res = apply(r, f, plan)
        if res[0]:
            if pop_solve(plan, counter):
                return True
            revert(plan, res[1])
        else:
            revert(plan, res[1])
    return False

if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument(dest='domain', help='specify domain file')
    args.add_argument(dest='problem', help='specify problem file')
    args.add_argument(dest='heuristic', help='specify heuristic')
    options = args.parse_args()
    parser = Parser(options.domain)
    domain = parser.parse_domain()
    domain.print()
    problem = parser.parse_problem(domain, options.problem)
    problem.print()
    task = ground_problem(problem, options.heuristic)
    print(task)
    step_init = Operator(Action('init', problem.objects, [], problem.init, []), problem.objects)
    step_goal = Operator(Action('goal', problem.objects, problem.goal, [], []), problem.objects)
    max_level = task.max_level
    plan = Plan(task, step_init, step_goal, max_level)
    success = False
    plan.reached_max = True
    i = 1
    start = time.time()
    while not success and plan.reached_max:
        plan = Plan(task, step_init, step_goal, max_level)
        i += 1
        plan.max_steps = i
        print(plan.max_steps)
        plan.reached_max = False
        success = pop_solve(plan, 0)
    if success:
        print("\nSUCCESS")
        print("\nList of steps:")
        for step in plan.steps:
            print(step.name + str(step.num), step.operator.parameters)
        print("\nOrdering of steps")
        for key in plan.order_more.keys():
            for value in plan.order_more[key]:
                ordering = (plan.steps[key], plan.steps[value])
                print(ordering[0].name, ordering[0].operator.parameters, '  <  ', ordering[1].name,
                      ordering[1].operator.parameters)
        # print("\nCausal links:")
        # for link in plan.causal_links:
        #     print(link)
        solution = Solution(plan).get_sol()
        for i in range(1, len(solution)):
            plan.add_order(solution[i - 1], solution[i])
        print("\nPlan of level ", plan.max_level, ":")
        for step in solution:
            print(plan.steps[step])
        while max_level > 0:
            plan.max_steps = 1000000
            max_level -= 1
            plan.max_level = max_level
            for step in plan.steps:
                if step.operator.level > max_level:
                    plan.agenda.decomp_flaws.append(Decomp_flaw(step.num))
            success = pop_solve(plan, 0)
            solution = Solution(plan).get_sol()
            print("\nPlan of level ", plan.max_level, ":")
            for step in solution:
                print(plan.steps[step])
        print("\nExample of plan execution:")
        steps_orig = copy.deepcopy(plan.steps)
        solution = Solution(plan).get_sol()
        for step in solution:
            print(steps_orig[step])
        end = time.time()
        print("time: ", end - start)
    else:
        print("Failure")
