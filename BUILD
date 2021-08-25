load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@rules_proto//proto:defs.bzl", "proto_library")

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
