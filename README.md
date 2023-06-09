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

The following is an example of a bug found with fusion-fuzzer. The program is
started with:

```
cd orchestrator
while true; do ./script.sh; done
```

After a few hours, console shows `RESULTS DIFFER`. If the system is configured
correctly, an email is sent with the testcase, which is also uploaded to a
server. This is the only information needed to fully reproduce the bug.

The pattern can be similar to the following snippet:

```
-1 0  2 9 2 0    0 28
-1 0  2 9 3 0 4254 42
-1 0  3 4 5 0 5324 32
 0 1  0 6 1 3 1341 31
 1 3  0 4 0 0 2946 51
 1 9 -1 0 2 1 5675 92
 2 2  0 5 0 0 2127 29
 3 9 -1 0 1 2 5675 92
 4 9 -1 0 2 3 5675 92
```

Per se, the file is complex to undestand among other things because it contains
many operations that are not related to the bug.

Calling the reducer, the file is pruned one operation at a time, while checking
that the test still fails. In case the elimination of an operation makes the
test not to fail, the removal is backtracked, and the reducer tries to
eliminate another one. The result of this step is a minimal reproducible
pattern that looks like the following:

```
-1 0  2 9 2 0    0 28
 3 9 -1 0 1 2 5675 92
 4 9 -1 0 2 3 5675 92
```

The interpretation of the pattern is as follows:

```
-1 0  2 9 2 0    0 28 # file_2 is initialized before the execution of fusion with a size of 0
 1 1 -1 0 1 5 5675 92 # open file_1
 2 3 -1 0 1 3 5675 92 # close file_1 without having written anything
 3 9 -1 0 1 2 5675 92 # move file_1 to file_2
 4 9 -1 0 2 3 5675 92 # move file_2 to file_3
```

The result of the execution can be tested as many times as wanted with `./reexecute`

The understanding of the previous pattern can be transformed in the following test-case:

```
init.sh:
    touch file_2
test.sh
    touch file_1
    mv file_1 file_2
    mv file_2 file_3
```

that for the moment needs to be created by hand, but can also be automated from
the interpretation of the pattern.

The reducer step can also generate a graph like the following (experimental):

<img src="./static/graph.svg">


In this graph, the nodes in red indicate functions that are executed in the
failing test, but not in the passing one, green indicate functions that are
executed in the passing test but not in the failing one, and yellow means
functions that are executed in both but whose logs are different. Interpreting
this graph with the previous information makes us realize that in the case of
empty files (createEmptyEntry), creating them at shutDown instead of when
inserting an entry is producing wrong results. This motivates the fix that
treats empty files similar to regular files, leading to a more robust
filesystem and fixing the bug :).
