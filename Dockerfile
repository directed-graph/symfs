# This Dockerfile is for building the SymFs binary; it is not meant for use
# during development, as there is no incremental build functionality. See
# `docker_build.bash` instead if you want incremental builds.

FROM implementing/builder:latest

WORKDIR /github/directed-graph/symfs

# Actual items are based on what's defined in .dockerignore.
COPY . .

RUN bazel build :symfs.par && \
    bazel test --test_output=all :all && \
    mkdir -p /usr/local/bin && \
    cp bazel-bin/symfs.par /usr/local/bin/symfs.par && \
    bazel clean

ENTRYPOINT ["/usr/local/bin/symfs.par"]
