workspace(name = "everchanging")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

# grpc deps
http_archive(
    name = "com_github_grpc_grpc",
    urls = [
        "https://github.com/grpc/grpc/archive/ee5b762f33a42170144834f5ab7efda9d76c480b.tar.gz",
    ],
    strip_prefix = "grpc-ee5b762f33a42170144834f5ab7efda9d76c480b",
)
load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")
grpc_deps()
load("@com_github_grpc_grpc//bazel:grpc_extra_deps.bzl", "grpc_extra_deps")
grpc_extra_deps()

# par_binary deps
git_repository(
    name = "subpar",
    remote = "https://github.com/google/subpar",
    tag = "2.0.0",
)

# absl deps
git_repository(
    name = "bazel",
    remote = "https://github.com/bazelbuild/bazel",
    tag = "4.2.0",
)
