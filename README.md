
SymFS is a program that generates a view to a collection of directories in the
form of symlinks. Specifically, given a set of directories and associated
metadata, SymFS will generate a set of symlinks to those directories, grouping
them based on a set of criteria against the metadata of those directories.


## How to Extend

If you want to use a custom proto for your metadata, you can add it directly to
`protos/ext.proto`. Alternatively, you can create a new proto file and add it
to the `ext_proto` `BUILD` rule. This can be done in two steps:

1. Add the proto definition under `protos/`.
2. Add file to the `srcs` in `BUILD` for `ext_proto`.

In either case, we also recommend updating the test cases in `ext_lib_test.py`.
See commit `c78f3407962f2d1664ce070cbcde1fc3659a0b9a` for an example. Feel free
to send a pull request for this addition!

An alternative and more "decoupled" approach is to add the proto as a separate
library. This can also be done without changing much code, in three steps:

1. Add the proto definition under `protos/` as above.
2. Add a `proto_library` and a `py_proto_library` in `BUILD` for it.
3. Add the `py_proto_library` as a dependency in `ext_lib` and import it in
   `ext_lib.py`.

The alternative approach may be good if you plan to keep your custom proto
private (i.e. a parallel branch).
