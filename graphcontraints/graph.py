import networkx as nx
import z3 as z3
from enum import Enum

class OperationTypes(Enum):
    OPEN = 1
    BOUNDED = 2
    CLOSE = 3
    UNBOUNDED = 4

class Operations(Enum):
    OPEN = 1
    CLOSE = 3
    WRITE = 4
    READ = 5
    SEEK = 6
    TRUNCATE = 7
    UNLINK = 8
    RENAME = 9
    MKDIR = 10
    RMDIR = 11
    SYMLINK = 12
    LINK = 13
    CHMOD = 14
    CHOWN = 15
    UTIMENS = 16
    CREATE = 17
    RELEASE = 18
    FSYNC = 19
    SETXATTR = 20
    GETXATTR = 21
    LISTXATTR = 22
    REMOVEXATTR = 23
    OPENDIR = 24

def add_operations_from_types(solver, graph):
    for node in graph.nodes():
        solver.add( z3.Implies( graph.nodes()[node]['operation_type'] == OperationTypes.OPEN.value, graph.nodes()[node]['operation'] == Operations.OPEN.value ) )
        solver.add( z3.Implies( graph.nodes()[node]['operation_type'] == OperationTypes.CLOSE.value, graph.nodes()[node]['operation'] == Operations.CLOSE.value ) )
        solver.add( z3.Implies( graph.nodes()[node]['operation_type'] == OperationTypes.BOUNDED.value, z3.And(graph.nodes()[node]['operation'] >= Operations.WRITE.value, graph.nodes()[node]['operation'] <= Operations.WRITE.value ) ) )

def add_operation_constraints(solver, graph):
    for node in graph.nodes():
        solver.add( graph.nodes()[node]['operation_type'] >= OperationTypes.OPEN.value, graph.nodes()[node]['operation_type'] <= OperationTypes.CLOSE.value )
        solver.add( graph.nodes()[node]['transaction'] >= 0, graph.nodes()[node]['transaction'] <= 100 )
        solver.add( graph.nodes()[node]['buffer_id'] >= 0, graph.nodes()[node]['buffer_id'] < 10 )

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
           andcondition = z3.And( andcondition, z3.And(graph.nodes()[nodep]['operation_type'] == OperationTypes.CLOSE.value, graph.nodes()[nodep]['transaction'] == graph.nodes()[node1]['transaction']) )
           for node3 in nodesn:
               andcondition = z3.And(andcondition, z3.Or(graph.nodes()[node3]['operation_type'] != OperationTypes.CLOSE.value, z3.And(graph.nodes()[node3]['operation_type'] == OperationTypes.CLOSE.value, graph.nodes()[node3]['transaction'] != graph.nodes()[node1]['transaction']) ) )
           orcondition = z3.Or(orcondition, andcondition)
       solver.add( z3.Implies( graph.nodes()[node1]['operation_type'] == OperationTypes.OPEN.value, orcondition ) )

def add_if_op_then_open(solver, graph):
    for node1 in graph.nodes():
        orcondition = False
        othernodes = set(graph.adj[node1])
        for node2 in othernodes:
            nodep  = node2
            nodesn = othernodes - {node2}
            andcondition = True
            andcondition = z3.And( andcondition, z3.And(graph.nodes()[nodep]['operation_type'] == OperationTypes.OPEN.value, graph.nodes()[nodep]['transaction'] == graph.nodes()[node1]['transaction']) )
            # for node3 in nodesn:
                # andcondition = z3.And(andcondition, z3.Or(graph.nodes()[node3]['operation_type'] != OperationTypes.OPEN.value, z3.And(graph.nodes()[node3]['operation_type'] == OperationTypes.OPEN.value, graph.nodes()[node3]['transaction'] != graph.nodes()[node1]['transaction']) ) )
            orcondition = z3.Or(orcondition, andcondition)

        solver.add( z3.Implies( graph.nodes()[node1]['operation_type'] == OperationTypes.BOUNDED.value, orcondition ) )

def add_close_after_open(solver, graph):
    for node1 in graph.nodes():
        othernodes = set(graph.adj[node1])
        for node2 in othernodes:
            solver.add( z3.Implies( z3.And( graph.nodes()[node1]['operation_type'] == OperationTypes.OPEN.value, graph.nodes()[node2]['operation_type'] == OperationTypes.CLOSE.value, graph.nodes()[node1]['transaction'] == graph.nodes()[node2]['transaction'] ) , graph.nodes()[node1]['time'] < graph.nodes()[node2]['time'] ) )

def add_open_different_transactions(solver, graph):
    for node1 in graph.nodes():
        othernodes = set(graph.adj[node1])
        for node2 in othernodes:
            solver.add( z3.Implies( z3.And( graph.nodes()[node1]['operation_type'] == OperationTypes.OPEN.value, graph.nodes()[node2]['operation_type'] == OperationTypes.OPEN.value ) , graph.nodes()[node1]['transaction'] != graph.nodes()[node2]['transaction'] ) )

def add_op_after_open(solver, graph):
    for node1 in graph.nodes():
        othernodes = set(graph.adj[node1])
        for node2 in othernodes:
            solver.add( z3.Implies( z3.And( graph.nodes()[node1]['operation_type'] == OperationTypes.OPEN.value, graph.nodes()[node2]['operation_type'] == OperationTypes.BOUNDED.value, graph.nodes()[node1]['transaction'] == graph.nodes()[node2]['transaction']) , graph.nodes()[node1]['time'] < graph.nodes()[node2]['time'] ) )

def add_op_before_close(solver, graph):
    for node1 in graph.nodes():
        othernodes = set(graph.adj[node1])
        for node2 in othernodes:
            solver.add( z3.Implies( z3.And( graph.nodes()[node1]['operation_type'] == OperationTypes.BOUNDED.value, graph.nodes()[node2]['operation_type'] == OperationTypes.CLOSE.value, graph.nodes()[node1]['transaction'] == graph.nodes()[node2]['transaction'] ) , graph.nodes()[node1]['time'] < graph.nodes()[node2]['time'] ) )

def show_solution(model, graph):
    times = set()
    for node in graph.nodes():
        times.add( model[graph.nodes()[node]['time'] ].as_long() )

    for t in times:
        for node in graph.nodes():
            if model[ graph.nodes()[node]["time"] ].as_long() == t :
                node = graph.nodes()[node]
                time        = model[ node['time'] ].as_long()
                operation_type   = model[ node['operation_type'] ].as_long()
                transaction = model[ node['transaction'] ].as_long()
                buffer_id = model[ node['buffer_id'] ].as_long()
                print(time, operation_type, transaction, buffer_id)

def generate_nodes(n):
    ret = list()
    for x in range(0,n):
        node = {
                "name": "node_%04d" % x,
                "time": z3.Int("time_%04d" % x),
                "operation_type": z3.Int("operation_type_%04d" % x),
                "operation": z3.Int("operation_%04d" % x),
                "transaction": z3.Int("transaction_%04d" % x),
                "buffer_id": z3.Int("buffer_id_%04d" % x)
                }
        ret.append(node)
    return ret

# create an empty undirected graph
G = nx.Graph()

num_nodes = 3

# define the nodes
nodes = generate_nodes(num_nodes)

for n in range(0, num_nodes):
    G.add_nodes_from([(n+1, nodes[n])])

# add the edges to the graph
for i in range(0, num_nodes):
    for j in range(i+1, num_nodes):
        G.add_edges_from([(i+1,j+1)])

# Create a solver
solver = z3.Solver()

add_operations_from_types(solver, G)
add_operation_constraints(solver, G)
add_time_constraints(solver, G)
add_if_open_then_close(solver, G)
add_if_op_then_open(solver, G)
add_close_after_open(solver, G)
add_op_after_open(solver, G)
add_op_before_close(solver, G)
add_open_different_transactions(solver, G)

solver.add( G.nodes()[2]["operation_type"] == 2 );

# Check if the solver is satisfiable
if solver.check() == z3.sat:
    # Get the model from the solver
    model = solver.model()

    show_solution(model, G)
else:
    # No solution exists that satisfies the constraints
    print("No solution exists")
