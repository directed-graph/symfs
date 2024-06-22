# This Dockerfile is for building the SymFs binary; it is not meant for use
# during development, as there is no incremental build functionality. See
# `docker_build.bash` instead if you want incremental builds.

FROM implementing/builder:latest

WORKDIR /github/directed-graph/symfs

# Actual items are based on what's defined in .dockerignore.
COPY . .

RUN bazel test -c opt --test_output=all :all && \
    bazel build -c opt :symfs_zip && \
    mkdir -p /usr/local/bin && \
    cp bazel-bin/symfs.zip /usr/local/bin/symfs.zip && \
    bazel clean

ENTRYPOINT ["python", "/usr/local/bin/symfs.zip"]
