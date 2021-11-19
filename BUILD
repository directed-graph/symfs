load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@rules_proto//proto:defs.bzl", "proto_library")
load("@subpar//:subpar.bzl", "par_binary")

proto_library(
    name = "ext_proto",
    srcs = ["protos/ext.proto"],
    deps = [
        "@com_google_protobuf//:descriptor_proto",
    ],
)

proto_library(
    name = "symfs_proto",
    srcs = ["protos/symfs.proto"],
    deps = [
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:descriptor_proto",
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
        "@com_github_protocolbuffers_protobuf//:protobuf_python",
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
        "@abseil//absl/logging",
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
            "@abseil//absl/testing:absltest",
            "@abseil//absl/testing:parameterized",
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
        "@com_github_protocolbuffers_protobuf//:protobuf_python",
    ],
)

par_binary(
    name = "symfs",
    srcs = ["symfs.py"],
    python_version = "PY3",
    deps = [
        ":ext_lib",
        ":symfs_py_proto",
        "@abseil//absl:app",
        "@abseil//absl/flags",
        "@abseil//absl/logging",
    ],
)

py_test(
    name = "symfs_test",
    srcs = ["symfs_test.py"],
    data = glob(["test_data/**"]),
    python_version = "PY3",
    deps = [
        ":symfs",
        ":symfs_py_proto",
        "@abseil//absl/testing:absltest",
        "@abseil//absl/testing:flagsaver",
        "@abseil//absl/testing:parameterized",
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
        "@abseil//absl/testing:absltest",
        "@abseil//absl/testing:parameterized",
    ],
)
