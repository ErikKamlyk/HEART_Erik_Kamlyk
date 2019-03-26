from src.pddl.task import Task, Operator
from src.pddl.pddl import Predicate
from src.plan import SubgoalResolver

def ground_action(action, types, index, types_dict, objects, operators, chosen_objects=[]):
    if index < len(types):
        for object in types_dict[types[index].name]:
            if object not in chosen_objects:
                new_chosen_objects = list(chosen_objects)
                new_chosen_objects.append(object)
                ground_action(action, types, index + 1, types_dict, objects, operators, new_chosen_objects)
    else:
        operators.append(Operator(action, chosen_objects))

def ground_actions(problem, types_dict):
    operators = []
    for action in problem.domain.actions:
        types = []
        for parameter in action.parameters:
            types.append(parameter.type)
        ground_action(action, types, 0, types_dict, problem.objects, operators)
    return operators

def sort_by_type(objects):
    types_dict = {}
    for object in objects:
        if object.type.name not in types_dict:
            types_dict[object.type.name] = set()
        types_dict[object.type.name].add(object)
        cur_type = object.type
        while cur_type.parent_type != None:
            cur_type = cur_type.parent_type
            if cur_type.name not in types_dict:
                types_dict[cur_type.name] = set()
            types_dict[cur_type.name].add(object)
    return types_dict

def get_facts(operators, goal):
    facts = []
    for operator in operators:
        for precondition in operator.pre:
            facts.append(precondition)
        for effect_pos in operator.eff_pos:
            facts.append(effect_pos)
        for effect_neg in operator.eff_neg:
            facts.append(effect_neg)
    for elem in goal:
        facts.append(elem)
    return facts

def ground_init(init):
    new_init = []
    for elem in init:
        new_init.append(Predicate(elem[0].name, elem[1]))
    return new_init

def ground_goal(goal):
    new_goal = []
    for elem in goal:
        new_goal.append(Predicate(elem[0].name, elem[1]))
    return new_goal

def ground_problem(problem, heuristic):
    objects = problem.objects
    types_dict = sort_by_type(objects)
    init = ground_init(problem.init)
    goals = ground_goal(problem.goal)
    operators = ground_actions(problem, types_dict)
    for operator in operators:
        if operator.method:
            new_vertices = []
            for vertice in operator.method.vertices:
                for operator2 in operators:
                    if vertice[0].name == operator2.name:
                        if vertice[1] == operator2.parameters:
                            new_vertices.append(operator2)
                if vertice[0].name == 'init':
                    new_vertices.append('init')
                if vertice[0].name == 'goal':
                    new_vertices.append('goal')
            operator.method.vertices = new_vertices
    facts = get_facts(operators, goals)
    task = Task(problem.name, problem.domain, facts, objects, init, goals, operators, heuristic)
    for fact in facts:
        task.subgoal_resolvers[fact.__repr__()] = []
        for operator in operators:
            if fact in operator.eff_pos:
                task.subgoal_resolvers[fact.__repr__()].append(SubgoalResolver(operator, None))
    return task