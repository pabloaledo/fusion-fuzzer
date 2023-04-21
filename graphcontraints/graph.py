import networkx as nx
import z3 as z3
from enum import Enum

class Operations(Enum):
    OPEN = 1
    WRITE = 2
    CLOSE = 3

def add_operation_constraints(solver, graph):
    for node in graph.nodes():
        solver.add( graph.nodes()[node]['operation'] >= Operations.OPEN.value, graph.nodes()[node]['operation'] <= Operations.CLOSE.value )
        solver.add( graph.nodes()[node]['transaction'] >= 0, graph.nodes()[node]['transaction'] <= 100 )

def add_time_constraints(solver, graph):
    for node in graph.nodes():
        solver.add( graph.nodes()[node]['time'] >= 0, graph.nodes()[node]['time'] <= 10000 )

def add_if_open_then_close(solver, graph):
   for node1 in graph.nodes():
       orcondition = False
       othernodes = set(graph.adj[node1])
       for node2 in othernodes:
           nodep  = node2
           nodesn = othernodes - {node2}
           andcondition = True
           andcondition = z3.And( andcondition, z3.And(graph.nodes()[nodep]['operation'] == Operations.CLOSE.value, graph.nodes()[nodep]['transaction'] == graph.nodes()[node1]['transaction']) )
           for node3 in nodesn:
               andcondition = z3.And(andcondition, z3.Or(graph.nodes()[node3]['operation'] != Operations.CLOSE.value, z3.And(graph.nodes()[node3]['operation'] == Operations.CLOSE.value, graph.nodes()[node3]['transaction'] != graph.nodes()[node1]['transaction']) ) )
           orcondition = z3.Or(orcondition, andcondition)
       solver.add( z3.Implies( graph.nodes()[node1]['operation'] == Operations.OPEN.value, orcondition ) )

def add_if_op_then_open(solver, graph):
    for node1 in graph.nodes():
        orcondition = False
        othernodes = set(graph.adj[node1])
        for node2 in othernodes:
            nodep  = node2
            nodesn = othernodes - {node2}
            andcondition = True
            andcondition = z3.And( andcondition, z3.And(graph.nodes()[nodep]['operation'] == Operations.OPEN.value, graph.nodes()[nodep]['transaction'] == graph.nodes()[node1]['transaction']) )
            # for node3 in nodesn:
                # andcondition = z3.And(andcondition, z3.Or(graph.nodes()[node3]['operation'] != Operations.OPEN.value, z3.And(graph.nodes()[node3]['operation'] == Operations.OPEN.value, graph.nodes()[node3]['transaction'] != graph.nodes()[node1]['transaction']) ) )
            orcondition = z3.Or(orcondition, andcondition)

        solver.add( z3.Implies( graph.nodes()[node1]['operation'] == Operations.WRITE.value, orcondition ) )

def add_close_after_open(solver, graph):
    for node1 in graph.nodes():
        othernodes = set(graph.adj[node1])
        for node2 in othernodes:
            solver.add( z3.Implies( z3.And( graph.nodes()[node1]['operation'] == Operations.OPEN.value, graph.nodes()[node2]['operation'] == Operations.CLOSE.value, graph.nodes()[node1]['transaction'] == graph.nodes()[node2]['transaction'] ) , graph.nodes()[node1]['time'] < graph.nodes()[node2]['time'] ) )

def add_open_different_transactions(solver, graph):
    for node1 in graph.nodes():
        othernodes = set(graph.adj[node1])
        for node2 in othernodes:
            solver.add( z3.Implies( z3.And( graph.nodes()[node1]['operation'] == Operations.OPEN.value, graph.nodes()[node2]['operation'] == Operations.OPEN.value ) , graph.nodes()[node1]['transaction'] != graph.nodes()[node2]['transaction'] ) )

def add_op_after_open(solver, graph):
    for node1 in graph.nodes():
        othernodes = set(graph.adj[node1])
        for node2 in othernodes:
            solver.add( z3.Implies( z3.And( graph.nodes()[node1]['operation'] == Operations.OPEN.value, graph.nodes()[node2]['operation'] == Operations.WRITE.value, graph.nodes()[node1]['transaction'] == graph.nodes()[node2]['transaction']) , graph.nodes()[node1]['time'] < graph.nodes()[node2]['time'] ) )

def add_op_before_close(solver, graph):
    for node1 in graph.nodes():
        othernodes = set(graph.adj[node1])
        for node2 in othernodes:
            solver.add( z3.Implies( z3.And( graph.nodes()[node1]['operation'] == Operations.WRITE.value, graph.nodes()[node2]['operation'] == Operations.CLOSE.value, graph.nodes()[node1]['transaction'] == graph.nodes()[node2]['transaction'] ) , graph.nodes()[node1]['time'] < graph.nodes()[node2]['time'] ) )

def show_solution(model, graph):
    times = set()
    for node in graph.nodes():
        times.add( model[graph.nodes()[node]['time'] ].as_long() )

    for t in times:
        for node in graph.nodes():
            if model[ graph.nodes()[node]["time"] ].as_long() == t :
                node = graph.nodes()[node]
                time        = model[ node['time'] ].as_long()
                operation   = model[ node['operation'] ].as_long()
                transaction = model[ node['transaction'] ].as_long()
                print("time: ", time, ", operation: ", operation, ", transaction: ", transaction)

def generate_nodes(n):
    ret = list()
    for x in range(0,n):
        node = {"name": "node_%04d" % x, "time": z3.Int("time_%04d" % x), "operation": z3.Int("operation_%04d" % x), "transaction": z3.Int("transaction_%04d" % x) }
        ret.append(node)
    return ret

# create an empty undirected graph
G = nx.Graph()

num_nodes = 3

# define the nodes
# node1 = {"name": "node1", "time": z3.Int('time1'), "operation": z3.Int('operation1'), "transaction": z3.Int('transaction1')}
# node2 = {"name": "node2", "time": z3.Int('time2'), "operation": z3.Int('operation2'), "transaction": z3.Int('transaction2')}
# node3 = {"name": "node3", "time": z3.Int('time3'), "operation": z3.Int('operation3'), "transaction": z3.Int('transaction3')}
# node4 = {"name": "node4", "time": z3.Int('time4'), "operation": z3.Int('operation4'), "transaction": z3.Int('transaction4')}
nodes = generate_nodes(num_nodes)

for n in range(0, num_nodes):
    # print(nodes[n])
    G.add_nodes_from([(n+1, nodes[n])])
# G.add_nodes_from([(1, node1)])
# G.add_nodes_from([(2, node2)])
# G.add_nodes_from([(3, node3)])
# G.add_nodes_from([(4, node4)])

# add the edges to the graph
# G.add_edges_from([(1,2), (1,3), (1,4), (2,3), (2,4), (3,4) ])
for i in range(0, num_nodes):
    for j in range(i+1, num_nodes):
        # print(i+1,j+1)
        G.add_edges_from([(i+1,j+1)])

# Create a solver
solver = z3.Solver()

add_operation_constraints(solver, G)
add_time_constraints(solver, G)
add_if_open_then_close(solver, G)
add_if_op_then_open(solver, G)
add_close_after_open(solver, G)
add_op_after_open(solver, G)
add_op_before_close(solver, G)
add_open_different_transactions(solver, G)

solver.add( G.nodes()[2]["operation"] == 2 );


# Check if the solver is satisfiable
if solver.check() == z3.sat:
    # Get the model from the solver
    model = solver.model()

    show_solution(model, G)
else:
    # No solution exists that satisfies the constraints
    print("No solution exists")
