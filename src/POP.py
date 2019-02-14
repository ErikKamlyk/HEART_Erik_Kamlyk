import argparse
import random
import copy
from src.pddl.parser import Parser
from src.pddl.grounding import ground_problem
from src.plan import Plan, Subgoal, Threat, CausalLink, Step, Solution, ThreatResolver
from src.pddl.pddl import Action
from src.pddl.task import Operator

def solve_flaw(f, task):
    resolvers = set()
    if type(f) is Subgoal:
        for operator in task.operators:
            for eff in operator.eff_pos:
                if f.precondition.equal(eff):
                    resolvers.add(operator)
    elif type(f) is Threat:
        if (f.link.step1.name != "init") and not plan.isless(f.link.step1, f.step):
            resolvers.add(ThreatResolver(f.step, f.link.step1))
        if (f.link.step2.name != "goal") and not plan.isless(f.step, f.link.step2):
            resolvers.add(ThreatResolver(f.link.step2, f.step))
        for link in plan.causal_links:
            if link != f.link and link.predicate.equal(f.link.predicate) and link.step2 == f.link.step2:
                resolvers.add(ThreatResolver(link.step1, link.step2))
        for key1 in plan.steps.keys():
            for step1 in plan.steps[key1]:
                if step1 != f.link.step2 and step1 != f.link.step1 and f.link.step2.name != "goal" and not plan.isless(f.link.step2, step1):
                    for eff_pos in step1.operator.eff_pos:
                        if eff_pos.equal(f.link.predicate):
                            resolvers.add(ThreatResolver(step1, f.link.step2))
    return resolvers

def add_new_subgoals(plan, causal_link):
    new_subgoals = set()
    for precondition in causal_link.step1.operator.pre:
        solved = False
        #print('precondition ', precondition.name, precondition.signature)
        for key in plan.steps.keys():
            for step in plan.steps[key]:
                if step != causal_link.step1 and step != causal_link.step2:
                    for eff in step.operator.eff_pos:
                        #print('effect ', eff.name, eff.signature)
                        if eff.equal(precondition):
                            solved = True
                            #print("SOLVED ", step.name, step.operator.parameters)
                            if plan.add_order(step, causal_link.step1):
                                plan.causal_links.add(CausalLink(step, causal_link.step1, precondition))
                            else:
                                solved = False
                        if solved:
                            break
                    if solved:
                        break
            if solved:
                break
        if not solved:
            #print("NOT solved")
            new_subgoals.add(Subgoal(precondition, causal_link.step1))
    return new_subgoals

def add_new_threats(plan, breaker):
    new_threats = set()
    for eff_neg in breaker.operator.eff_neg:
        #print("aaa ", eff_neg)
        for link in plan.causal_links.copy():
            #print("bb ", link.step1, link.step2, link. predicate)
            if link.step1 != breaker and link.step2 != breaker and eff_neg.equal(link.predicate):
                if not plan.isless(breaker, link.step1) and not plan.isless(link.step2, breaker):
                    # only_link = True
                    # for link2 in plan.causal_links:
                    #     if link2 != link and link2.predicate.equal(link.predicate) and link2.step2 == link.step2:
                    #         only_link = False
                    # if only_link:
                    new_threats.add(Threat(link, breaker))
                    #print(breaker, " ", link.step1, " ", link.step2, " ", link.predicate)
                    # else:
                    #     plan.causal_links.remove(link)
    for link in plan.causal_links:
        if link.step2 == breaker:
            for key1 in plan.steps.keys():
                for step1 in plan.steps[key1]:
                    if step1 != breaker:
                        for eff_neg in step1.operator.eff_neg:
                            if eff_neg.equal(link.predicate):
                                if not plan.isless(step1, link.step1) and not plan.isless(link.step2, step1):
                                    new_threats.add(Threat(link, step1))
    return new_threats

def delete_invalidated_threats(plan):
    for threat in plan.agenda.threats.copy():
        if plan.isless(threat.step, threat.link.step1) or plan.isless(threat.link.step2, threat.step):
            plan.agenda.threats.remove(threat)

def apply(resolver, f, plan):
    if type(f) is Subgoal:
        plan.add_step(resolver)
        new_causal_link = CausalLink(resolver, f.goal, f.precondition)
        for eff_pos in resolver.operator.eff_pos:
            for precond in f.goal.operator.pre:
                if eff_pos.equal(precond):
                    plan.causal_links.add(CausalLink(resolver, f.goal, precond))
        if not plan.add_order(resolver, f.goal):
            return (False, set(), set())
        plan.agenda.subgoals.remove(f)
        return (True, add_new_subgoals(plan, new_causal_link), add_new_threats(plan, resolver))
    elif type(f) is Threat:
        #print(plan.order_more)
        if not plan.add_order(resolver.step1, resolver.step2):
            return (False, set(), set())
            #print("FALSE")
        plan.agenda.threats.remove(f)
        delete_invalidated_threats(plan)
        return (True, set(), set())
        # remove_invalidated_flaws(plan, new_causal_link)
    # elif type(f) is Threat:
    #     plan.causal_links.append()
    #     plan.order.add((action, f.goal))
    #     plan.agenda.threats.remove(f)

def revert(plan, old_causal_links, old_threats, new_flaws, r, f):
    plan.causal_links = old_causal_links
    plan.agenda.threats = old_threats
    if type(r) != ThreatResolver:
        plan.steps[r.__repr__()].remove(r)
    #     plan.order.remove((r, f.goal))
    # else:
    #     plan.order.remove(plan.last_add)
    plan.order.pop()
    plan.build_order_dicts()
    # plan.order_less -= plan.reverse_add_order_less
    # plan.order_more -= plan.reverse_add_order_more
    plan.agenda.insert(f)
    for flaw in new_flaws:
        plan.agenda.remove(flaw)

# def revert(action, f, plan):
#     plan.steps.remove(action)
#     if type(f) is Subgoal:
#         new_causal_link = None
#         plan.causal_links.remove(new_causal_link)
#         plan.order.remove((action, f.goal))
#         plan.agenda.subgoals.add(f)
#     # if type(f) is Threat:
#     #     new_causal_link = None
#     #     plan.causal_links.remove(new_causal_link)
#     #     plan.order.remove((action, f.goal))
#     #     plan.agenda.subgoals.add(f)

# def update_casual_links(plan):
#     update = False
#     for key1 in plan.steps.keys():
#         for step1 in plan.steps[key1]:
#             for key2 in plan.steps.keys():
#                 for step2 in plan.steps[key2]:
#                     if step1 != step2 and step2.name != "goal" and not set([step1]) <= plan.order_more[step2]:
#                         for eff_pos in step1.operator.eff_pos:
#                             for precond in step2.operator.pre:
#                                 if eff_pos.equal(precond):
#                                     found = False
#                                     for link in plan.causal_links:
#                                         if link.step1 == step1 and link.step2 == step2 and link.predicate.equal(eff_pos):
#                                             found = True
#                                     if not found:
#                                         plan.causal_links.add(CausalLink(step1, step2, eff_pos))
#                                         update = True
#     return update
#
# def update_threats(plan):
#     new_threats = set()
#     for key in plan.steps.keys():
#         for step in plan.steps[key]:
#             new_threats |= add_new_threats(plan, step)
#     return new_threats


def pop_solve(plan):
    if plan.agenda.empty():
        return True
    #print('AGENDA ', plan.agenda)
    #print('ORDER', plan.order_more)
    if len(plan.agenda.subgoals) > 0:
        f = random.sample(plan.agenda.subgoals, 1)[0]
    else:
        f = random.sample(plan.agenda.threats, 1)[0]
    resolvers = solve_flaw(f, plan.task)
    if type(f) == Threat:
        print("\nflaw: ", f.step, f.link.step1, f.link.step2, f.link.predicate)
    else:
        print("\nflaw: ", f.precondition, f.goal)
    # print('resolvers ', resolvers)
    i = 0
    while len(resolvers) > 0 and i < 20:
        i += 1
        #print('AGENDA ', plan.agenda)
        #print('i = ', i)
        r = random.sample(resolvers, 1)[0]
        if type(r) != ThreatResolver:
            for res in resolvers:
                if res.name == "pick-up":
                    r = res
            print('resolver ', r.name, r.parameters)
            resolvers.remove(r)
            r = Step(r)
        else:
            print("Threat ressolver: ", r.step1, " ", r.step2)
            resolvers.remove(r)
        old_causal_links = set()
        for link in plan.causal_links:
            old_causal_links.add(link)
        old_threats = set()
        for threat in plan.agenda.threats:
            old_threats.add(threat)
        res = apply(r, f, plan)
        if res[0]:
            plan.agenda.subgoals |= res[1]
            plan.agenda.threats |= res[2]
            #print('\nis agenda empty ', plan.agenda.empty())
            # if update_casual_links(plan):
            #     plan.agenda.threats = update_threats(plan)
            # print(plan.causal_links)
            if pop_solve(plan):
                return True
            revert(plan, old_causal_links, old_threats, res[1], r, f)
        else:
            revert(plan, old_causal_links, old_threats, res[1], r, f)
        #print("NEW ITERATION")
    return False

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
    task = ground_problem(problem)
    print(task)
    step_init = Operator(Action('init', problem.objects, [], problem.init, []), problem.objects)
    step_goal = Operator(Action('goal', problem.objects, problem.goal, [], []), problem.objects)
    plan = Plan(task, step_init, step_goal)
    if pop_solve(plan):
        print("Success")
        print("List of steps:")
        for key in plan.steps.keys():
            for step in plan.steps[key]:
                print(step.name, step.operator.parameters)
        print("Ordering of steps")
        for ordering in plan.order:
            print(ordering[0].name, ordering[0].operator.parameters, '   ', ordering[1].name, ordering[1].operator.parameters)
        print("\nExample of plan execution:")
        solution = Solution(plan).get_sol()
        for step in solution:
            print(step)
    else:
        print("Failure")