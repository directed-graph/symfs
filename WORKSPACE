workspace(name = "everchanging")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

# protobuf deps
git_repository(
    name = "com_google_protobuf",
    remote = "https://github.com/protocolbuffers/protobuf",
    tag = "v27.0",
)
load("@com_google_protobuf//:protobuf_deps.bzl", "protobuf_deps")
protobuf_deps()

# abseil deps
git_repository(
    name = "abseil",
    remote = "https://github.com/abseil/abseil-py",
    tag = "v2.1.0",
)

# python deps
git_repository(
    name = "rules_python",
    remote = "https://github.com/bazelbuild/rules_python",
    tag = "0.32.2",
)
load("@rules_python//python:repositories.bzl", "py_repositories")
py_repositories()
