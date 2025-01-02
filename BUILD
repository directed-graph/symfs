load("@rules_proto//proto:defs.bzl", "proto_library")
load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")
load("@rules_python//python:proto.bzl", "py_proto_library")

proto_library(
    name = "ext_proto",
    srcs = ["protos/ext.proto"],
    deps = [
        "@protobuf//:descriptor_proto",
    ],
)

proto_library(
    name = "symfs_proto",
    srcs = ["protos/symfs.proto"],
    deps = [
        "@protobuf//:any_proto",
        "@protobuf//:descriptor_proto",
    ],
)

py_proto_library(
    name = "ext_py_proto",
    deps = [
        ":ext_proto",
    ],
)

py_proto_library(
    name = "symfs_py_proto",
    deps = [
        ":symfs_proto",
    ],
)

py_library(
    name = "derived_metadata/abstract_derived_metadata",
    srcs = [
        "derived_metadata/abstract_derived_metadata.py",
    ],
    deps = [
        ":symfs_py_proto",
        "@protobuf//:protobuf_python",
    ],
)

py_library(
    name = "derived_metadata_lib",
    srcs = glob(
        ["derived_metadata/*.py"],
        exclude = [
            "derived_metadata/abstract_derived_metadata.py",
            "derived_metadata/*_test.py",
        ],
    ),
    deps = [
        ":derived_metadata/abstract_derived_metadata",
        ":ext_py_proto",
        ":symfs_py_proto",
        "@abseil-py//absl/logging",
    ],
)

# Generates "derived_metadata/<module>" targets for all tests defined under
# derived_metadata. Note that this can potentially include dependencies that
# are not needed for some tests.
[
    py_test(
        name = module[:-3],
        srcs = [module],
        python_version = "PY3",
        deps = [
            ":derived_metadata_lib",
            ":ext_py_proto",
            "@abseil-py//absl/testing:absltest",
            "@abseil-py//absl/testing:parameterized",
        ],
    )
    for module in glob(["derived_metadata/*_test.py"])
]

py_library(
    name = "ext_lib",
    srcs = ["ext_lib.py"],
    deps = [
        ":derived_metadata_lib",
        ":ext_py_proto",
        ":symfs_py_proto",
        "@protobuf//:protobuf_python",
    ],
)

py_binary(
    name = "symfs",
    srcs = ["symfs.py"],
    python_version = "PY3",
    deps = [
        ":ext_lib",
        ":symfs_py_proto",
        "@abseil-py//absl:app",
        "@abseil-py//absl/flags",
        "@abseil-py//absl/logging",
    ],
)

filegroup(
    name = "symfs_zip",
    srcs = [":symfs"],
    output_group = "python_zip_file",
)

py_test(
    name = "symfs_test",
    srcs = ["symfs_test.py"],
    data = glob(["test_data/**"]),
    python_version = "PY3",
    deps = [
        ":symfs",
        ":symfs_py_proto",
        "@abseil-py//absl/testing:absltest",
        "@abseil-py//absl/testing:flagsaver",
        "@abseil-py//absl/testing:parameterized",
        "@rules_python//python/runfiles",
    ],
)

py_test(
    name = "ext_lib_test",
    srcs = ["ext_lib_test.py"],
    python_version = "PY3",
    deps = [
        ":derived_metadata_lib",
        ":ext_lib",
        ":ext_py_proto",
        "@abseil-py//absl/testing:absltest",
        "@abseil-py//absl/testing:parameterized",
    ],
)
