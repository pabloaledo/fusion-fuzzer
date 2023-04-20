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
variations of feasible executions. The benefit of these variations over purely
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
  and we have to find them. One of the main objectives of this project is to
  eliminate any false positives, so at the end of the day, any reported
  discrepancy found by the fuzzer should be treated as an error in Fusion.

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

Requirements
============

Fusion-fuzzer requires the following setup before starting:

- fusion source code compiled in a folder that is identified with the
  environment variable FUSION_ROOT
```
export FUSION_ROOT=~/workspace/fusion
```

- minio docker running: To avoid unwanted bills in s3 traffic, considering that
  fuzzers are usually run for very long periods of time, minio is highly
  encouraged. To start a minio server, run the following:
```
docker run -it --rm -p 9000:9000 -p 9001:9001 quay.io/minio/minio server /data --console-address ":9001"
docker run --entrypoint=/bin/sh minio/mc -c 'mc config host add minio http://172.17.0.2:9000 minioadmin minioadmin && mc mb minio/fusionfs-ci'
```

- s3fs: to ensure a proper clean-up between different executions of the fuzzer
  testcases, it is recommended to also mount the minio bucket in a local path
  with s3fs.
```
echo "minioadmin:minioadmin" | sudo tee /etc/s3cred
sudo chmod 600 /etc/s3cred
s3fs fusionfs-ci $FUSION_S3FS -o passwd_file=/etc/s3cred,use_path_request_style,url=http://127.0.0.1:9000
mkdir -p $FUSION_S3FS/tests/random_test
echo fake > $FUSION_S3FS/tests/random_test/fake
```


Example of execution, debug and fix
===================================

The following is an example of a bug found with fusion-fuzzer. The program is
started with:

```
cd orchestrator
while true; do source ./script.sh; done
```

After a few hours, console shows `RESULTS DIFFER`. The information needed to
reproduce the test is now under the folder `test`. There we can find a file
`both.pattern` that might look like the following snippet.

```
-1 0  2 9 2 0    0 28
-1 0  2 9 3 0 4254 42
-1 0  3 4 5 0 5324 32
 0 1  0 6 1 3 1341 31
 1 1 -1 0 1 5 5675 92
 2 3 -1 0 1 3 5675 92
 2 2  0 5 0 0 2127 29
 3 9 -1 0 1 2 5675 92
 4 9 -1 0 2 3 5675 92
```

Per se, the file is complex to undestand among other things because it contains
many operations that are not related to the bug. We can experiment reducing
this pattern until we find a /minimal failing pattern/, a pattern in which
removing anything operation would make the test to pass instead of failing.
During this process, we can call `./reexecute` to check if the test still fails
or not.

At the end, the pattern would look something like the following:

```
-1 0  2 9 2 0    0 28 # file_2 is initialized before the execution of fusion with a size of 0
 1 1 -1 0 1 5 5675 92 # open file_1
 2 3 -1 0 1 3 5675 92 # close file_1 without having written anything
 3 9 -1 0 1 2 5675 92 # move file_1 to file_2
 4 9 -1 0 2 3 5675 92 # move file_2 to file_3
```

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

Once the test is created, the process follows common practice. A commit is
created adding the failing test to the suite of automated tests, a fix is
created, submitted for peer review and merged as common. Some tools to help in
this process can be found in experimental branches of this project.
