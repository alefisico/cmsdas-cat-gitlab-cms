---
title: "Building a container image"
teaching: 10
exercises: 10
questions:
- "How can I build a container image with my own code in a GitLab CI/CD pipeline?"
objectives:
- "Know how to build and store a container image in a GitLab CI/CD pipeline"
keypoints:
- "Easy-to-use yml templates exist for container image building"
---

## Build a container image

Using container images locally is explained in the [CMS Docker lesson](https://awesome-workshop.github.io/docker-cms/). 
In this lesson, we have used many of them already.
We will now see to build a container image including files from your repository in a GitLab CI/CD pipeline.

Here, we expect that you have a `Dockerfile` in your repository. This file defines what "base" image of your new image and what files goes in it.
See the [HSF Docker tutorial](https://hsf-training.github.io/hsf-training-docker/index.html) to learn more about containers.

For the build you can use an existing `yml` template and extend it in your pipeline. You can do this with `include:` in your `.gitlab-ci.yml`.

You will add a job that extends this template with the variables you need:

~~~
stages:
  - build
  - test_code

include:
  - project: 'cms-analysis/general/container-image-ci-templates'
    file:
      - 'kaniko-image.gitlab-ci.yml'

build_image:
  extends: .build_kaniko
  stage: build
  variables:
    PUSH_IMAGE: "true"
    REGISTRY_IMAGE_PATH: "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}"

code_testing:
  stage: test_code
  script:
    - echo "I'm testing the code"
~~~
{: .language-yaml}

The variables starting with `CI_` are predefined variables for the GitLab CI/CD pipelines, you can find them in the [GitLab CI/CD documentation](https://docs.gitlab.com/ci/variables/predefined_variables/). Here, they are used to get a one-to-one correspondance between the image and the code.

Once the pipeline completes, you will find the container image in the container registry of your repository which you can find in  **Deploy -> Container registry**.

In this manner, you can build a container image even without having docker-engine installed locally.
If your repository is public, anyone can use this image.

With snippet above, your container images always have a tag that corresponds to the commit has of your code.
If you want to have an image with the `latest` tag, you can add another tag by defining it in a variable called `EXTRA_TAGS`
in the build_image step:

~~~
[...]

build_image:
  extends: .build_kaniko
  stage: build
  variables:
    PUSH_IMAGE: "true"
    REGISTRY_IMAGE_PATH: "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}"
    EXTRA_TAGS: "latest"

[...]
~~~
{: .language-yaml}

You can use this image in GitLab pipelines (or in other workflows):

~~~
  image:
    name: gitlab-registry.cern.ch/<your username>/><your repository>:latest
~~~
{: .language-yaml}

or even use it e.g. on `lxplus`:

~~~
apptainer shell docker://gitlab-registry.cern.ch/<your username>/><your repository>:latest
~~~
{: .language-bash}

For specific code versions, you can the commit hash as the tag, instead of `:latest`. 


{% include links.md %}
