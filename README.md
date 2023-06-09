Introduction
============

This repository implements an application of the wave function collapse
constraint solving technique to test fusion against a local filesystem.

The overall idea of the method is to define a set of operations and
constrained relationships between them. An example of such operations might be
(OPEN_A_FILE, CLOSE_A_FILE), and an example of constraints: if OPEN_A_FILE and
CLOSE_A_FILE refer to the same file descriptor, the former occurs in time
before the later.

Once this specification is done, we can invoke a solver to give us multiple
variations of feasible executions. The benefit of this variations over purely
random generated ones is that simply executing random functions of the API
would not exhibit any useful behavior. Most of the time, we would only be
writing to files that have not been opened before, writing at invalid offsets,
or moving files randomly. Additionally, because of the way we handle file
synchronization, we rely on certain assumptions that would easily be broken if
we just execute random calls. This would result in errors in our programs not
because of problems in Fusion, but because of the naive way in which we test.

With this approach, if we find an error, two outcomes are possible:

- "This is not a bug, it's a feature": Means that the local filesystem and
  fusion give different results, but this is expected due to the fact that the
semantics of operations are different in fusion and a local filesystem (for
example, multiple concurrent file descriptors for the same file are not
supported in fusion). If this situation appears, we can modify the fuzzer to
avoid generating more variations of this pattern in the future, avoiding losing
computational ressources and human time in debugging those scenarios.

- This is a bug: The local filesystem and fusion differ for unknown reasons,
  and we have to find them. Several tools are also available to help in this
process, that will be discussed later.

Architecture
============

The main idea consists of three pieces:

- A random testcase generator that receives a graph and generates a test plan:
  a set of operations over files that are semantically correct but random in
nature. (graphconstraints). It is a python program that takes no arguments and
prints to the standard output a set of operations. Each operation is a row
where the first number is time in milliseconds, and the rest are parameters to
the operation.

- A simulator that executes this test plan (writes into files, reads, moves
  things around, creates symlinks, removes them, creates folders, etc.). This
simulator can be executed on a local file system and on Fusion. (dtsimulator).
This is a C program that takes the name of a file as input and executes the
operations inside it. This can be run over the local filesystem and fusion. If
the results are different, we have definitively found an error in Fusion.

- An orchestrator that launches the two simulations and compares the results
  (just a script to launch everything). In the future it can do test reduction,
git bisect, error location ...

More tools outside the basic ones
=================================

Example of execution, debug and fix
===================================

<img src="./static/graph.svg">
