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
  name = "ext_lib",
  srcs = ["ext_lib.py"],
  deps = [
    ":ext_py_proto",
  ],
)

par_binary(
  name = "symfs",
  srcs = ["symfs.py"],
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
  data = glob(["test_data/*"]),
  deps = [
    ":symfs",
    ":symfs_py_proto",
    "@rules_python//python/runfiles",
    "@abseil//absl/testing:parameterized",
  ],
)

py_test(
  name = "ext_lib_test",
  srcs = ["ext_lib_test.py"],
  deps = [
    ":ext_lib",
    ":ext_py_proto",
    "@abseil//absl/testing:parameterized",
  ],
)
