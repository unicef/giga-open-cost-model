import networkx as nx
from typing import Union
from ortools.sat.python import cp_model


def build_sat_problem(
    g: nx.Graph,
    gr: nx.Graph,
    dt: Union[nx.Graph, None],
    cost_m: int,
    max_cost: int,
    upper_bound: int,
    do_hints: bool,
    mstG: nx.Graph,
):
    """
    This function builds the wcnf formula for the SAT solver
    param: g: Graph containing nodes (id,label='cschool','uschool','cfnode','ufnode','splitter';cost=capex+opex cost
    param: gr: relational graph for ancestry calculation
    param: dt: dominator tree paths (optional)
    param: cost_m: the cost per m of fiber
    param: max_cost: max budget, if 0 is considered that there is no budget
    param: upper_bound: upper bound for the number of schools to be connected
    param: do_hints: whether to use hints or not
    param: mstG: minimum spanning tree of the graph
    return: d: dictionary of var index -> graph var ((type,i,j) = edge,parent or ancestor,(x,i) = node)
    return: vpool: IDtool, effectively the inverse of d
    return: wcnf formula
    return: fixed costs for unconstrained scenario (e.g. scenario 1)
    return: new_max_cost is max_cost minus some fixed costs for constrained scenario (e.g. scenario 2)
    return: budget_cost is a variable for constrained scenario (e.g. scenario 2)
    return: obj_school objective variable for constrained scenario (e.g. scenario 2)
    """

    model = cp_model.CpModel()
    ##### For the leq constraint
    for_cost_vars = []
    for_cost_weights = []
    ######
    ##### For the objective
    for_obj_vars = []
    for_obj_weights = []
    ######
    ##### For variable management
    X = {}
    P = {}
    A = {}
    vertices = {}
    ### For now and testing ####
    vertices["ufnode"] = []
    vertices["cschool"] = []
    vertices["splitter"] = []
    ############################
    fixed_costs = 0
    new_max_cost = max_cost
    ###########
    # Add Metanode id = metanode var = 1 always True
    X["metanode"] = model.NewBoolVar("x_metanode")
    model.Add(X["metanode"] == True)  # is this necessary?
    ########

    ####We start with nodes####

    for id, attributes in g.nodes(data=True):
        label = attributes["label"]
        cost = attributes["cost"]
        ncost = attributes["ncost"]
        pkmcost = attributes["pkmcost"]
        pindex = attributes["pindex"]
        ####General######
        X[id] = model.NewBoolVar("x_{0}".format(id))
        if label not in vertices:
            vertices[label] = []
        vertices[label].append(id)
        #################
        if (
            label == "cfnode" or label == "cschool"
        ):  # fiber node that is in use or a connected school
            # Add soft or substract from max cost
            if max_cost == 0:
                fixed_costs += cost + ncost
                model.Add(X[id] == True)
            else:
                new_max_cost -= cost + ncost
                model.Add(X[id] == True)
            ############################
        elif label == "uschool":
            # Add soft or save for leq
            if max_cost == 0:
                fixed_costs += cost + ncost
                model.Add(
                    X[id] == True
                )  # For schools, this assumes all schools must and can be connected
            else:
                if cost + ncost > 0:
                    for_cost_vars.append(X[id])
                    for_cost_weights.append(cost + ncost)
                # this goes for the opt function in budget scenario
                for_obj_vars.append(X[id])
                for_obj_weights.append(pindex)
        else:  # fiber node that is NOT in use (candidate location) or splitter
            # Add soft or save for leq cstr
            if max_cost == 0:
                if cost + ncost > 0:
                    for_obj_vars.append(X[id])
                    for_obj_weights.append(cost + ncost)
            else:
                if cost + ncost > 0:
                    for_cost_vars.append(X[id])
                    for_cost_weights.append(cost + ncost)
            ############################
    #################################

    ####Next we deal with edges and how they related to parenthood

    for n1, n2, attributes in g.edges(data=True):
        w = attributes["weight"]
        if (
            n1 in vertices["cfnode"]
            or n1 in vertices["ufnode"]
            or n1 in vertices["cschool"]
        ):
            if n2 in vertices["uschool"] or n2 in vertices["splitter"]:
                pkm = g.nodes[n2]["pkmcost"]
                ####Parenthood#######
                P[(n2, n1)] = model.NewBoolVar("p_{0}@{1}".format(n2, n1))
                #####################

                if w > 0:
                    if max_cost == 0:
                        for_obj_vars.append(P[(n2, n1)])
                        for_obj_weights.append(w * (pkm + cost_m))
                    else:
                        for_cost_vars.append(P[(n2, n1)])
                        for_cost_weights.append(w * (pkm + cost_m))
                #############

        elif n1 in vertices["uschool"] or n1 in vertices["splitter"]:
            if (
                n2 in vertices["cfnode"]
                or n2 in vertices["ufnode"]
                or n2 in vertices["cschool"]
            ):
                pkm = g.nodes[n1]["pkmcost"]

                ####Parenthood#######
                P[(n1, n2)] = model.NewBoolVar("p_{0}@{1}".format(n1, n2))
                #####################
                if w > 0:
                    if max_cost == 0:
                        for_obj_vars.append(P[(n1, n2)])
                        for_obj_weights.append(w * (pkm + cost_m))
                    else:
                        for_cost_vars.append(P[(n1, n2)])
                        for_cost_weights.append(w * (pkm + cost_m))
                #############

            elif n2 in vertices["uschool"] or n2 in vertices["splitter"]:
                pkm1 = g.nodes[n1]["pkmcost"]
                pkm2 = g.nodes[n2]["pkmcost"]
                ####Parenthood#######
                P[(n2, n1)] = model.NewBoolVar("p_{0}@{1}".format(n2, n1))
                P[(n1, n2)] = model.NewBoolVar("p_{0}@{1}".format(n1, n2))
                #####################

                if w > 0:
                    if max_cost == 0:
                        for_obj_vars.append(P[(n1, n2)])
                        for_obj_weights.append(w * (pkm1 + cost_m))
                        for_obj_vars.append(P[(n2, n1)])
                        for_obj_weights.append(w * (pkm2 + cost_m))
                    else:
                        for_cost_vars.append(P[(n2, n1)])
                        for_cost_weights.append(w * (pkm2 + cost_m))
                        for_cost_vars.append(P[(n1, n2)])
                        for_cost_weights.append(w * (pkm1 + cost_m))
                #############

                #### In this case also Pij=>!Pji ####
                model.AddBoolOr([P[(n1, n2)].Not(), P[(n2, n1)].Not()])
                #####################################
    ##### We need to add edges and parenthood for metanode as well ####

    for fn in vertices["cfnode"]:
        P[(fn, "metanode")] = model.NewBoolVar("p_{0}@metanode".format(fn))
        model.Add(P[(fn, "metanode")] == True)
    for fn in vertices["cschool"]:
        P[(fn, "metanode")] = model.NewBoolVar("p_{0}@metanode".format(fn))
        model.Add(P[(fn, "metanode")] == True)
    for fn in vertices["ufnode"]:
        P[(fn, "metanode")] = model.NewBoolVar("p_{0}@metanode".format(fn))

    ###################################################################
    ##############################################################################

    #####Now set the ancestor variables###################

    for n1, n2 in gr.edges():
        if n1 == "metanode":
            A[(n2, "metanode")] = model.NewBoolVar("a_{0}@metanode".format(n2))
        elif n2 == "metanode":
            A[(n1, "metanode")] = model.NewBoolVar("a_{0}@metanode".format(n1))
        elif (
            n1 in vertices["cfnode"]
            or n1 in vertices["ufnode"]
            or n1 in vertices["cschool"]
        ):
            if n2 in vertices["splitter"] or n2 in vertices["uschool"]:
                A[(n2, n1)] = model.NewBoolVar("a_{0}@{1}".format(n2, n1))
        elif (
            n2 in vertices["cfnode"]
            or n2 in vertices["ufnode"]
            or n2 in vertices["cschool"]
        ):
            if n1 in vertices["splitter"] or n1 in vertices["uschool"]:
                A[(n1, n2)] = model.NewBoolVar("a_{0}@{1}".format(n1, n2))
        elif (n1 in vertices["splitter"] or n1 in vertices["uschool"]) and (
            n2 in vertices["splitter"] or n2 in vertices["uschool"]
        ):
            A[(n1, n2)] = model.NewBoolVar("a_{0}@{1}".format(n1, n2))
            A[(n2, n1)] = model.NewBoolVar("a_{0}@{1}".format(n2, n1))

    #####################################################

    ######## Now we do all the constraints #########
    #### xi == sum(Pij)>0 and sum(Pij)<=1 ####

    for us in vertices["uschool"]:
        clause = []

        for us2 in vertices["uschool"]:
            if (us, us2) in P:
                clause.append(P[(us, us2)])
        for sp in vertices["splitter"]:
            if (us, sp) in P:
                clause.append(P[(us, sp)])
        for fn in vertices["cfnode"]:
            if (us, fn) in P:
                clause.append(P[(us, fn)])
        for fn in vertices["ufnode"]:
            if (us, fn) in P:
                clause.append(P[(us, fn)])
        for cs in vertices["cschool"]:
            if (us, cs) in P:
                clause.append(P[(us, cs)])

        if max_cost == 0:
            model.Add(
                sum(c for c in clause) == 1
            )  # we assume all unconnected scholls can and will be connected
        else:
            model.Add(sum(c for c in clause) <= 1)

        ###### Equality to xi #####
        model.Add(sum(c for c in clause) == 1).OnlyEnforceIf(X[us])
        model.Add(sum(c for c in clause) == 0).OnlyEnforceIf(X[us].Not())
        ###########################

    for sp in vertices["splitter"]:
        clause = []
        for us in vertices["uschool"]:
            if (sp, us) in P:
                clause.append(P[(sp, us)])
        for sp2 in vertices["splitter"]:
            if (sp, sp2) in P:
                clause.append(P[(sp, sp2)])
        for fn in vertices["cfnode"]:
            if (sp, fn) in P:
                clause.append(P[(sp, fn)])
        for fn in vertices["ufnode"]:
            if (sp, fn) in P:
                clause.append(P[(sp, fn)])
        for cs in vertices["cschool"]:
            if (sp, cs) in P:
                clause.append(P[(sp, cs)])

        model.Add(sum(c for c in clause) <= 1)

        ###### Equality to xi #####
        model.Add(sum(c for c in clause) == 1).OnlyEnforceIf(X[sp])
        model.Add(sum(c for c in clause) == 0).OnlyEnforceIf(X[sp].Not())
        ###########################

    for fn in vertices["ufnode"]:
        model.Add(X[fn] == P[fn, "metanode"])

    ##########################
    ##########################################

    #######connectedness#######
    # if i has a parent then this has a parent #

    for us in vertices["uschool"]:
        for us2 in vertices["uschool"]:
            if (us2, us) in P:
                pji = P[(us2, us)]
                clause = []
                for us3 in vertices["uschool"]:
                    if (us, us3) in P:
                        clause.append(P[(us, us3)])
                for sp in vertices["splitter"]:
                    if (us, sp) in P:
                        clause.append(P[(us, sp)])
                for fn in vertices["cfnode"]:
                    if (us, fn) in P:
                        clause.append(P[(us, fn)])
                for fn in vertices["ufnode"]:
                    if (us, fn) in P:
                        clause.append(P[(us, fn)])
                for cs in vertices["cschool"]:
                    if (us, cs) in P:
                        clause.append(P[(us, cs)])

                #### pji -> Vpik ####
                model.AddBoolOr([pji.Not()] + clause)
                #####################

        for sp in vertices["splitter"]:
            if (sp, us) in P:
                pji = P[(sp, us)]
                clause = []
                for us2 in vertices["uschool"]:
                    if (us, us2) in P:
                        clause.append(P[(us, us2)])
                for sp2 in vertices["splitter"]:
                    if (us, sp2) in P:
                        clause.append(P[(us, sp2)])
                for fn in vertices["cfnode"]:
                    if (us, fn) in P:
                        clause.append(P[(us, fn)])
                for fn in vertices["ufnode"]:
                    if (us, fn) in P:
                        clause.append(P[(us, fn)])
                for cs in vertices["cschool"]:
                    if (us, cs) in P:
                        clause.append(P[(us, cs)])

                #### pji -> Vpik ####
                model.AddBoolOr([pji.Not()] + clause)
                #####################

    for sp in vertices["splitter"]:
        for us in vertices["uschool"]:
            if (us, sp) in P:
                pji = P[(us, sp)]
                clause = []
                for us2 in vertices["uschool"]:
                    if (sp, us2) in P:
                        clause.append(P[(sp, us2)])
                for sp2 in vertices["splitter"]:
                    if (sp, sp2) in P:
                        clause.append(P[(sp, sp2)])
                for fn in vertices["cfnode"]:
                    if (sp, fn) in P:
                        clause.append(P[(sp, fn)])
                for fn in vertices["ufnode"]:
                    if (sp, fn) in P:
                        clause.append(P[(sp, fn)])
                for cs in vertices["cschool"]:
                    if (sp, cs) in P:
                        clause.append(P[(sp, cs)])

                #### pji -> Vpik ####
                model.AddBoolOr([pji.Not()] + clause)
                #####################

        for sp2 in vertices["splitter"]:
            if (sp2, sp) in P:
                pji = P[(sp2, sp)]
                clause = []
                for us in vertices["uschool"]:
                    if (sp, us) in P:
                        clause.append(P[(sp, us)])
                for sp3 in vertices["splitter"]:
                    if (sp, sp3) in P:
                        clause.append(P[(sp, sp3)])
                for fn in vertices["cfnode"]:
                    if (sp, fn) in P:
                        clause.append(P[(sp, fn)])
                for fn in vertices["ufnode"]:
                    if (sp, fn) in P:
                        clause.append(P[(sp, fn)])
                for cs in vertices["cschool"]:
                    if (sp, cs) in P:
                        clause.append(P[(sp, cs)])

                #### pji -> Vpik ####
                model.AddBoolOr([pji.Not()] + clause)
                #####################

    for fn in vertices["ufnode"]:
        for us in vertices["uschool"]:
            if (us, fn) in P:
                pji = P[(us, fn)]
                #### pji -> pimetanode
                model.AddImplication(pji, P[(fn, "metanode")])

        for sp in vertices["splitter"]:
            if (sp, fn) in P:
                pji = P[(sp, fn)]
                #### pji -> pimetanode
                model.AddImplication(pji, P[(fn, "metanode")])

    ###########################

    #### subset p c a #####

    for us in vertices["uschool"]:
        for us2 in vertices["uschool"]:
            if (us, us2) in P:
                model.AddImplication(P[(us, us2)], A[(us, us2)])
        for sp in vertices["splitter"]:
            if (us, sp) in P:
                model.AddImplication(P[(us, sp)], A[(us, sp)])
        for fn in vertices["cfnode"]:
            if (us, fn) in P:
                model.AddImplication(P[(us, fn)], A[(us, fn)])
        for fn in vertices["ufnode"]:
            if (us, fn) in P:
                model.AddImplication(P[(us, fn)], A[(us, fn)])
        for cs in vertices["cschool"]:
            if (us, cs) in P:
                model.AddImplication(P[(us, cs)], A[(us, cs)])

    for sp in vertices["splitter"]:
        for us in vertices["uschool"]:
            if (sp, us) in P:
                model.AddImplication(P[(sp, us)], A[(sp, us)])
        for sp2 in vertices["splitter"]:
            if (sp, sp2) in P:
                model.AddImplication(P[(sp, sp2)], A[(sp, sp2)])
        for fn in vertices["cfnode"]:
            if (sp, fn) in P:
                model.AddImplication(P[(sp, fn)], A[(sp, fn)])
        for fn in vertices["ufnode"]:
            if (sp, fn) in P:
                model.AddImplication(P[(sp, fn)], A[(sp, fn)])
        for cs in vertices["cschool"]:
            if (sp, cs) in P:
                model.AddImplication(P[(sp, cs)], A[(sp, cs)])

    for fn in vertices["ufnode"]:
        model.AddImplication(P[(fn, "metanode")], A[(fn, "metanode")])

    for fn in vertices["cfnode"]:
        model.Add(A[(fn, "metanode")] == True)

    for cs in vertices["cschool"]:
        model.Add(A[(cs, "metanode")] == True)

    #######################

    #### asymmetry ####

    for us in vertices["uschool"]:
        for us2 in vertices["uschool"]:
            if (us, us2) in A:
                model.AddImplication(A[(us, us2)], A[(us2, us)].Not())
        for sp in vertices["splitter"]:
            if (us, sp) in A:
                model.AddImplication(A[(us, sp)], A[(sp, us)].Not())

    for sp in vertices["splitter"]:
        for us in vertices["uschool"]:
            if (sp, us) in A:
                model.AddImplication(A[(sp, us)], A[(us, sp)].Not())
        for sp2 in vertices["splitter"]:
            if (sp, sp2) in A:
                model.AddImplication(A[(sp, sp2)], A[(sp2, sp)].Not())

    ###################

    #### transitivity ####

    all_vertices = (
        ["metanode"]
        + vertices["cfnode"]
        + vertices["ufnode"]
        + vertices["cschool"]
        + vertices["uschool"]
        + vertices["splitter"]
    )
    for vi in all_vertices:
        for vj in all_vertices:
            if (vi, vj) in A:
                for vk in all_vertices:
                    if (vj, vk) in A and (vi, vk) in A:
                        model.AddBoolOr(
                            [A[(vi, vj)].Not(), A[(vj, vk)].Not(), A[(vi, vk)]]
                        )

    ######################

    #### root path #######

    if max_cost == 0:
        # Again, this assumes all unconnected schools can and will be connected
        for us in vertices["uschool"]:
            model.Add(A[(us, "metanode")] == True)

    #### number of edges == nodes +1 ####

    clause1 = []
    clause2 = []
    for v in all_vertices:
        if v != "metanode":
            clause1.append(X[(v)])

    for v1 in all_vertices:
        for v2 in all_vertices:
            if (v1, v2) in P:
                clause2.append(P[(v1, v2)])
    model.Add(sum(c for c in clause1) == sum(c for c in clause2))

    #### leq constraint ####
    if max_cost > 0:
        leq = []
        for i in range(len(for_cost_vars)):
            aux = model.NewIntVar(0, 10000000, "aux")
            model.Add(aux == for_cost_weights[i]).OnlyEnforceIf(for_cost_vars[i])
            model.Add(aux == 0).OnlyEnforceIf(for_cost_vars[i].Not())
            leq.append(aux)
        budget_cost = model.NewIntVar(0, 10000000, "Budget_cost")
        model.Add(budget_cost == sum(v for v in leq))
        model.Add(budget_cost <= new_max_cost)

        # obj_schools = model.NewIntVar(0,len(vertices['uschool']),'obj_schools')
        obj_schools = model.NewIntVar(0, 100000000, "obj_schools")
        obj_aux = []
        for i in range(len(for_obj_vars)):
            aux = model.NewIntVar(0, 10000000, "aux")
            model.Add(aux == for_obj_weights[i]).OnlyEnforceIf(for_obj_vars[i])
            model.Add(aux == 0).OnlyEnforceIf(for_obj_vars[i].Not())
            obj_aux.append(aux)
        model.Add(obj_schools == sum(v for v in obj_aux))
        model.Maximize(obj_schools)

    else:
        budget_cost = None
        obj_schools = None
        if upper_bound > 0:
            obj_cost = model.NewIntVar(0, upper_bound - fixed_costs, "obj_cost")
        else:
            obj_cost = model.NewIntVar(0, 1000000000, "obj_cost")
        obj_aux = []
        for i in range(len(for_obj_vars)):
            aux = model.NewIntVar(0, 10000000, "aux")
            model.Add(aux == for_obj_weights[i]).OnlyEnforceIf(for_obj_vars[i])
            model.Add(aux == 0).OnlyEnforceIf(for_obj_vars[i].Not())
            obj_aux.append(aux)
        model.Add(obj_cost == sum(v for v in obj_aux))
        model.Minimize(obj_cost)

    ########################

    ########################
    #### Hints ########

    if max_cost == 0:
        if do_hints:
            used_hints = []
            for sc in vertices["uschool"]:
                path = list(nx.shortest_path(mstG, "metanode", sc))
                for i in range(2, len(path)):
                    if (path[i], path[i - 1]) not in used_hints:
                        model.AddHint(P[(path[i], path[i - 1])], True)
                        used_hints.append((path[i], path[i - 1]))

    ########################

    return X, P, A, model, fixed_costs, new_max_cost, budget_cost, obj_schools
