---
title: "EXTRA: Building a Container Image in GitLab CI/CD"
teaching: 10
exercises: 10
---

::::::::: questions

- How can I build a container image with my own code in a GitLab CI/CD pipeline?
- How can I reuse the same container building configuration across multiple jobs?

:::::::::

::::::::: objectives

- Build and push a container image to the GitLab container registry using buildah.
- Create a reusable `.buildah` template for container building.
- Use container images built in CI/CD pipelines in your analysis workflows.

:::::::::

## Building Container Images with Buildah

[Buildah](https://buildah.io/) is a container build tool that works well in CI/CD environments without requiring Docker. In this lesson, you'll learn to build and store container images in the GitLab container registry within your CI/CD pipeline.

### What You'll Need

- A `Dockerfile` in your repository that defines your container image.
- If unfamiliar with Docker, see the [HSF Docker tutorial](https://hsf-training.github.io/hsf-training-docker/index.html).

---

## Creating a Reusable Buildah Template

Instead of repeating buildah commands in every job, define a reusable `.buildah` template that other jobs can extend:

```yaml
.buildah:
  stage: build
  image: quay.io/buildah/stable
  variables:
    DOCKER_FILE_NAME: "Dockerfile"
    REGISTRY_IMAGE_PATH: ${CI_REGISTRY_IMAGE}:latest
    EXTRA_TAGS: ""
  script:
    - echo "$CI_REGISTRY_PASSWORD" | buildah login -u "$CI_REGISTRY_USER" --password-stdin $CI_REGISTRY
    - export BUILDAH_FORMAT=docker
    - export STORAGE_DRIVER=vfs
    - buildah build --storage-driver=${STORAGE_DRIVER} -f ${DOCKER_FILE_NAME} -t ${REGISTRY_IMAGE_PATH}
    - |
      if [ -n "${EXTRA_TAGS}" ]; then
        for tag in ${EXTRA_TAGS}; do
          buildah tag ${REGISTRY_IMAGE_PATH} ${CI_REGISTRY_IMAGE}:${tag}
        done
      fi
    - buildah push --storage-driver=${STORAGE_DRIVER} ${REGISTRY_IMAGE_PATH}
    - |
      if [ -n "${EXTRA_TAGS}" ]; then
        for tag in ${EXTRA_TAGS}; do
          buildah push --storage-driver=${STORAGE_DRIVER} ${CI_REGISTRY_IMAGE}:${tag}
        done
      fi
```

**Template variables:**

- **`DOCKER_FILE_NAME`:** Path to your Dockerfile (default: `Dockerfile`).
- **`REGISTRY_IMAGE_PATH`:** Full image path and tag (e.g., `registry.example.com/user/repo:tag`).
- **`EXTRA_TAGS`:** Space-separated list of additional tags (optional, e.g., `"latest v1.0"`).

---

## Example 1: Simple Image Build and Push

Extend the `.buildah` template to build an image tagged with your commit hash:

```yaml
stages:
  - build

build_image:
  extends: .buildah
  variables:
    DOCKER_FILE_NAME: "Dockerfile"
    REGISTRY_IMAGE_PATH: "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}"
    EXTRA_TAGS: "latest"
```

**What happens:**

1. The image is tagged with your commit hash (e.g., `a1b2c3d`).
2. It's also tagged as `latest` via `EXTRA_TAGS`.
3. Both tags are pushed to your GitLab container registry.

Find your image at **Deploy > Container registry** in your GitLab project.

---

## Example 2: Conditional Builds with Rules

Build the container image only when the Dockerfile changes or on a schedule:

```yaml
stages:
  - build

build_image:
  extends: .buildah
  variables:
    DOCKER_FILE_NAME: "Dockerfile"
    REGISTRY_IMAGE_PATH: "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}"
    EXTRA_TAGS: "latest"
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
      variables:
        EXTRA_TAGS: "latest scheduled"
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - Dockerfile
    - if: $CI_COMMIT_BRANCH == "main"
      changes:
        - Dockerfile
```

This ensures containers are only rebuilt when necessary, saving CI/CD time.

---

## Using Your Built Container Image

Once the image is pushed to the registry, use it in subsequent CI jobs or elsewhere:

### In GitLab CI/CD

```yaml
test_with_image:
  stage: test
  image: ${CI_REGISTRY_IMAGE}:latest
  script:
    - echo "Running tests in the custom container"
    - # your test commands here
```

### Locally (on LXPLUS or your machine)

```bash
apptainer shell docker://${CI_REGISTRY_IMAGE}:latest
```

Or with Docker:

```bash
docker run ${CI_REGISTRY_IMAGE}:latest
```

Replace `${CI_REGISTRY_IMAGE}` with your actual registry path (e.g., `gitlab-registry.cern.ch/username/repo`).

---

:::::: challenge

### Challenge: Build Your Own Container

1. Create a simple `Dockerfile` in your repository that compiles `CMSSW` like the previous example.
2. Add a `build_image` job to your `.gitlab-ci.yml` that extends `.buildah`.
3. Push your code and check **CI/CD > Pipelines** to watch the build.
4. Find your image in **Deploy > Container registry**.
5. Use it in a downstream CI job or locally with apptainer.

::::::

---

:::::: callout

**Tip:** The commit hash tag (e.g., `a1b2c3d`) ensures a one-to-one correspondence between your code and the built image, making it easy to reproduce analysis runs from a specific commit.

::::::

## Build an image that includes the compiled CMSSW area (from `cmssw_compile`)

If you already compile CMSSW in a `cmssw_compile` job and publish the full `${CMSSW_RELEASE}` as an artifact, you can bake that compiled area into a reusable runtime image. This lets downstream jobs (or local users) run `cmsRun` without rebuilding.

### 1) Ensure `cmssw_compile` exports the area as an artifact

```yaml
variables:
  CMS_PATH: /cvmfs/cms.cern.ch
  CMSSW_RELEASE: CMSSW_10_6_30
  SCRAM_ARCH: slc7_amd64_gcc700

cmssw_compile:
  image: registry.cern.ch/docker.io/cmssw/el7:x86_64
  stage: compile
  tags: [k8s-cvmfs]
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=${SCRAM_ARCH}
    - cmsrel ${CMSSW_RELEASE}
    - cd ${CMSSW_RELEASE}/src && cmsenv
    - mkdir -p AnalysisCode && cp -r $CI_PROJECT_DIR/ZPeakAnalysis AnalysisCode/
    - cd ${CMSSW_RELEASE}/src && scram b -j 4
  artifacts:
    untracked: true
    expire_in: 1 hour
    paths:
      - ${CMSSW_RELEASE}
```

### 2) Add a Dockerfile that copies the compiled area

Create `Dockerfile` in your repository:

```Dockerfile
# Dockerfile
FROM registry.cern.ch/docker.io/cmssw/el7:x86_64

ARG CMSSW_RELEASE
ENV CMS_PATH=/cvmfs/cms.cern.ch \
    SCRAM_ARCH=slc7_amd64_gcc700 \
    CMSSW_RELEASE=${CMSSW_RELEASE} \
    CMSSW_BASE=/opt/${CMSSW_RELEASE}

# Copy the compiled CMSSW area from the CI workspace (artifact) into the image
COPY ${CMSSW_RELEASE} /opt/${CMSSW_RELEASE}

SHELL ["/bin/bash", "-lc"]
RUN echo 'source ${CMS_PATH}/cmsset_default.sh && cd ${CMSSW_BASE}/src && cmsenv' >> /etc/profile.d/cmssw.sh
WORKDIR /opt/${CMSSW_RELEASE}/src
```

Notes:

- The `COPY ${CMSSW_RELEASE} ...` works because the build job (below) uses `needs: cmssw_compile` with `artifacts: true`, so the compiled directory is present in the build context.
- This image contains your compiled code, so downstream jobs can run `cmsRun` directly.

### 3) Build the image by extending the reusable `.buildah` template

Assuming you already defined the reusable `.buildah` template:

```yaml
.buildah:
  stage: build
  image: quay.io/buildah/stable
  variables:
    DOCKER_FILE_NAME: "Dockerfile"
    REGISTRY_IMAGE_PATH: ${CI_REGISTRY_IMAGE}:latest
    EXTRA_TAGS: ""
  script:
    - echo "$CI_REGISTRY_PASSWORD" | buildah login -u "$CI_REGISTRY_USER" --password-stdin $CI_REGISTRY
    - export BUILDAH_FORMAT=docker
    - export STORAGE_DRIVER=vfs
    - buildah build --storage-driver=${STORAGE_DRIVER} -f ${DOCKER_FILE_NAME} -t ${REGISTRY_IMAGE_PATH}
    - |
      if [ -n "${EXTRA_TAGS}" ]; then
        for tag in ${EXTRA_TAGS}; do
          buildah tag ${REGISTRY_IMAGE_PATH} ${CI_REGISTRY_IMAGE}:${tag}
        done
      fi
    - buildah push --storage-driver=${STORAGE_DRIVER} ${REGISTRY_IMAGE_PATH}
    - |
      if [ -n "${EXTRA_TAGS}" ]; then
        for tag in ${EXTRA_TAGS}; do
          buildah push --storage-driver=${STORAGE_DRIVER} ${CI_REGISTRY_IMAGE}:${tag}
        done
      fi
```

Then add the image build job:

```yaml
stages: [compile, build]

build_cmssw_image:
  stage: build
  extends: .buildah
  needs:
    - job: cmssw_compile
      artifacts: true
  variables:
    DOCKER_FILE_NAME: "Dockerfile"
    REGISTRY_IMAGE_PATH: "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}"
    EXTRA_TAGS: "latest"
    # Optional: pass release as build-arg
    BUILDAH_ARGS: "--build-arg CMSSW_RELEASE=${CMSSW_RELEASE}"
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | buildah login -u "$CI_REGISTRY_USER" --password-stdin $CI_REGISTRY
    - export BUILDAH_FORMAT=docker
    - export STORAGE_DRIVER=vfs
  script:
    - buildah build --storage-driver=${STORAGE_DRIVER} ${BUILDAH_ARGS} -f ${DOCKER_FILE_NAME} -t ${REGISTRY_IMAGE_PATH}
    - |
      if [ -n "${EXTRA_TAGS}" ]; then
        for tag in ${EXTRA_TAGS}; do
          buildah tag ${REGISTRY_IMAGE_PATH} ${CI_REGISTRY_IMAGE}:${tag}
        done
      fi
    - buildah push --storage-driver=${STORAGE_DRIVER} ${REGISTRY_IMAGE_PATH}
    - |
      if [ -n "${EXTRA_TAGS}" ]; then
        for tag in ${EXTRA_TAGS}; do
          buildah push --storage-driver=${STORAGE_DRIVER} ${CI_REGISTRY_IMAGE}:${tag}
        done
      fi
```

You can now use the image `${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}` (or `:latest`) in later jobs:

```yaml
run_with_baked_image:
  stage: test
  image: ${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}
  tags: [k8s-cvmfs]
  script:
    - source /cvmfs/cms.cern.ch/cmsset_default.sh
    - cd /opt/${CMSSW_RELEASE}/src && cmsenv
    - cmsRun AnalysisCode/ZPeakAnalysis/test/MyZPeak_cfg.py
```

Tips:

- Artifacts are read-only in downstream jobs, but Buildah only needs to read them (no extra `chmod` is required).
- Tag images by commit for exact reproducibility; add `latest` for a moving pointer.
