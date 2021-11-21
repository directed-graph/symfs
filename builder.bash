#!/usr/bin/env bash

# This script is to build SymFs incrementally during development. For SymFs
# Docker image, see `Dockerfile`.
#
# Usage:
#     ./builder.bash [<bazel args>]
#
# Set HOST_CACHE_DIR environment variable to change location of the cache for
# incremental builds. Set USE_CACHE to no to not use cache. If USE_CACHE is
# set, do not set the --output_base argument.

USE_CACHE="${USE_CACHE:-yes}"
HOST_CACHE_DIR="${HOST_CACHE_DIR:-${HOME}/.cache/bazel/symfs}"

args=("${@}")

if (("${#args[@]}" == 0 )); then
  args=("build" ":all")
fi

cache_volume=()
if [[ "${USE_CACHE}" == "yes" ]]; then
  args=("--output_base" "/mnt/cache" "${args[@]}")
  cache_volume=("--volume" "${HOST_CACHE_DIR}:/mnt/cache")
  mkdir -p "${HOST_CACHE_DIR}"
fi

project_directory="$(dirname "$(realpath $0)")"

set -o xtrace
docker run --rm \
  --volume "${project_directory}":/mnt/project \
  "${cache_volume[@]}" \
  --env USE_BUILD_DIR=yes \
  --env BUILD_USER_UID=$(id -u) \
  implementing/builder bazel "${args[@]}"
