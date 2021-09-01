
[![Integrate](https://github.com/directed-graph/symfs/actions/workflows/integrate.yaml/badge.svg)](https://github.com/directed-graph/symfs/actions/workflows/integrate.yaml)
[![Release](https://github.com/directed-graph/symfs/actions/workflows/release.yaml/badge.svg)](https://github.com/directed-graph/symfs/actions/workflows/release.yaml)


SymFS is a program that generates a view to a collection of directories in the
form of symlinks. Specifically, given a set of directories and associated
metadata, SymFS will generate a set of symlinks to those directories, grouping
them based on a set of criteria against the metadata of those directories.


## Example Configuration

We have an example [media collection](./example/media) that contains two media:
`m_0` and `m_1`. Each media has multiple casts, and some cast appears in
multiple media. What we want is a view on top of this collection that groups
the media by the cast. In other words, we want to browse by the cast.

To do this, we write a metadata file for each media containing the cast
members<sup>1</sup>. Then, we write the [SymFs
configuration](./example/config.textproto) to group by the `casts` field. We
then run with the following:

```
symfs.par --config_file example/config.textproto
```

Note that for the purposes of this example, we are using relative paths in the
configuration; this is generally not supported and may cause broken links.
However, the purpose of this example is to demonstrate setup and usage, so we
will ignore that for now. After running the command, the
[views](./example/views) will be generated. See the next section on how you can
automate this.

<sup>1</sup> Admittedly, this can be tedious. However, if you have a large
collection of items to which using SymFs can be beneficial, you'd likely want
to have some sort of metadata for your collection regardless. This is where the
extensible proto concept can come in handy.


## Automating

There are various ways to automate. In this section, we will go over a small
example on automating with systemd. We have provided
[symfs.service](./example/systemd/symfs.service) and
[symfs.timer](./example/systemd/symfs.timer) that you can build on top of to
automate.  You can place these files anywhere in the [systemd search
path](https://www.freedesktop.org/software/systemd/man/systemd.unit.html). One
example is `/usr/local/lib/systemd/system/`.

If you don't have any major customization needed, the `symfs.timer` can be
copied without modification (it will automatically trigger SymFs to run once a
day). For the given `symfs.service`, you need to update `Environment=` and
`User=` to something that is appropriate for you (change the `REPLACE_ME`
part). Then, simply write your `everchanging.symfs.Config` configuration
textproto to where you set it in `Environment=` and you are good to go!


## How to Extend

If you want to use a custom proto for your metadata, you can add it directly to
`protos/ext.proto`. Alternatively, you can create a new proto file and add it
to the `ext_proto` `BUILD` rule. This can be done in two steps:

1. Add the proto definition under `protos/`.
2. Add file to the `srcs` in `BUILD` for `ext_proto`.

In either case, we also recommend updating the test case in `ext_lib_test.py`
with the new message(s). Feel free to send a pull request for this addition!

An alternative and more "decoupled" approach is to add the proto as a separate
library. This can also be done without changing much code, in three steps:

1. Add the proto definition under `protos/` as above.
2. Add a `proto_library` and a `py_proto_library` in `BUILD` for it.
3. Add the `py_proto_library` as a dependency in `ext_lib` and import it in
   `ext_lib.py`.

The alternative approach may be good if you plan to keep your custom proto
private (i.e. a parallel branch).
