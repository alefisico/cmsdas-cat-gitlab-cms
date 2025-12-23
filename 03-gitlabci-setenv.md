---
title: "Setting up CMSSW in GitLab CI/CD"
teaching: 10
exercises: 10
---

:::::: questions

- How do I run CMSSW in GitLab CI instead of on LXPLUS or cmslpc?
- Which runner tags provide CVMFS access, and how do I select them?
- What minimal steps must go into `.gitlab-ci.yml` to set up CMSSW?

::::::

:::::: objectives

- Select and use a CVMFS-enabled runner (e.g., `k8s-cvmfs`) and verify `/cvmfs` is mounted.
- Write a minimal `.gitlab-ci.yml` that sets CMSSW (`cmsset_default.sh`, `SCRAM_ARCH`, `cmsrel`, `cmsenv`) and validates with `cmsRun --help`.
- Understand CI isolation and ensure all environment setup is captured in the repository.

::::::

::::: prereq

If you skipped the previous lessons, ensure you have:

- A GitLab repository at CERN GitLab (named `cmsdas-gitlab-cms`).
- The repository cloned to your local machine with an empty `.gitlab-ci.yml` file.
- The example [analysis code](files/ZPeakAnalysis.zip) downloaded and added to your repository.

:::::


:::::::: discussion 

## What Do We Want to Achieve?

In the previous lesson, you ran a simple analysis workflow locally on your machine (cmslpc, lxplus, or university machine) with three steps:

1. Compile the analysis code in a CMSSW environment.
2. Run the analysis code on a small dataset.
3. Check the number of events in the output.

These are steps you'll repeat often during analysis development. Therefore, it's a **best practice** to automate them using GitLab CI/CD, ensuring consistency and catching errors early.
::::::::::::::::::::

## Setting Up CMSSW in GitLab CI/CD

### Understanding the CI Environment

When you use GitLab CI, your code is not executed on your own computer, but on a separate machine (called a **runner**) provided by CERN GitLab. Every time you push changes to your repository, the runner downloads your code and executes the pipeline steps in a clean environment.

Because of this isolation, you must ensure that all necessary setup—installing dependencies, configuring the environment, and preparing required files—is included in your CI configuration. This approach guarantees **reproducibility**, but also means you cannot rely on files or settings from your local machine: everything the pipeline needs must be version-controlled in your repository.

### Choosing the Correct GitLab Runner

To run a GitLab CI pipeline, you need a `.gitlab-ci.yml` file in your repository root. The simple pipeline from the previous lesson had minimal software requirements, but running CMSSW analysis requires special setup.

To use CMSSW in GitLab CI, you need access to **CVMFS** (CERN Virtual Machine File System), a network file system optimized for delivering software in high-energy physics. CVMFS provides access to CMSSW, grid proxies, and other tools from `/cvmfs/`.

Standard [GitLab CI runners at CERN](https://gitlab.docs.cern.ch/docs/Build%20your%20application/CI-CD/Runners/) do not mount CVMFS by default. To get a runner with CVMFS access, add a `tags` section to your `.gitlab-ci.yml`:

```yaml
tags:
  - k8s-cvmfs
```

Here's a minimal example to verify CVMFS is mounted:

```yaml
cvmfs_test:
  tags:
    - k8s-cvmfs
  script:
    - ls /cvmfs/cms.cern.ch/
```

The job `cvmfs_test` simply lists the contents of `/cvmfs/cms.cern.ch/`. If CVMFS is not mounted, this will fail.

:::::: spoiler

### To trigger the pipeline

```bash
git add .gitlab-ci.yml
git commit -m "added a CI"
git push
```

Then go to your GitLab project page and navigate to **Build > Pipelines** to watch the job run.
:::::::::::::::

:::::: challenge

### Challenge: Exploring Different Runners

Try these variations and observe what happens:

1. Run the job **without** the `tags` section. What happens?
2. Run the job with the tag `cvmfs` instead of `k8s-cvmfs`. What happens?

Discuss the differences. (Hint: Check the [CERN GitLab CI runners documentation](https://gitlab.docs.cern.ch/docs/Build%20your%20application/CI-CD/Runners/cvmfs-eos-runners/) for details.)

::::::

After pushing, check your pipeline on the GitLab project page. You'll see the job logs and the `k8s-cvmfs` label indicating the runner type.

<!-- ![A job with a GitLab CVMFS Runner showing the cvmfs label](fig/cvmfs_tag.png) -->

### Setting Up CMSSW in Your Pipeline

Now you'll learn how to configure a GitLab CI job that properly sets up and uses CMSSW. This example is applicable to any CI job requiring CVMFS access and CMS-specific tools.

::::::: callout

### Important:

The default user in the runner container is not your username, and the container has no CMS-related environment setup. Unlike LXPLUS (where CMS members get automatic environment configuration via the _zh_ group), everything must be set up manually in CI.
::::::::

#### Steps to Set Up CMSSW

In a typical workflow on LXPLUS, you would run:

```bash
cmssw-el7
source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsrel CMSSW_10_6_30
cd CMSSW_10_6_30/src
cmsenv
```

Let's break down what each command does:

- **`cmssw-el7`:** Starts a CentOS 7 container. (CMSSW_10_6_30 is old and doesn't have builds for newer LXPLUS systems.)
- **`source /cvmfs/cms.cern.ch/cmsset_default.sh`:** Sets up environment variables (adds `/cvmfs/cms.cern.ch/common` to `${PATH}`) and defines helper functions like `cmsrel` and `cmsenv`.
- **`cmsrel CMSSW_10_6_30`:** Creates a new CMSSW release. (We are using an old version of CMSSW on purpose for this exercise.)
- **`cmsenv`:** Sets up the runtime environment for the release.

:::::: spoiler

### Special Setup for cmslpc Users

At cmslpc, jobs typically run in your `nobackup` area (`/uscms_data/d3/USERNAME`). You may need to bind your directories when starting a container:

```bash
cmssw-el7 -p --bind /uscms/homes/${USER:0:1}/${USER}$ --bind /uscms_data/d3/${USER}$ --bind /uscms_data --bind /cvmfs -- /bin/bash -l
```

::::::

::::::: discussion

#### What are the actual commands behind `cmsenv` and `cmsrel`?

::::::::

::: solution

#### Solution: Determining CMSSW-related aliases

The most important aliases are in the table below:

| Alias    | Command                         |
|----------|---------------------------------|
| `cmsenv` | ``eval `scramv1 runtime -sh` `` |
| `cmsrel` | `scramv1 project CMSSW`         |

**The meaning of `eval`:** The args are read and concatenated together into a single command. This command is then read and executed by the shell, and its exit status is returned as the value of `eval`. If there are no args, or only null arguments, `eval` returns 0.
::::::::

#### Writing the `.gitlab-ci.yml` File

Now, translate the manual setup into a `.gitlab-ci.yml` configuration:

```yaml
cmssw_setup:
  image: registry.cern.ch/docker.io/cmssw/el7:x86_64
  tags:
    - k8s-cvmfs
  variables:
    CMS_PATH: /cvmfs/cms.cern.ch
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=slc7_amd64_gcc700
    - cmsrel CMSSW_10_6_30
    - cd CMSSW_10_6_30/src
    - cmsenv
    - cmsRun --help
```

**Key points:**

- **`image`:** Specifies a CentOS 7 container, equivalent to running `cmssw-el7` locally.
- **`tags`:** Ensures the job runs on a runner with CVMFS access.
- **`variables`:** Defines `CMS_PATH`, mirroring the LXPLUS environment.
- **`set +u` and `set -u`:** Temporarily allows unset variables (some setup scripts reference optional variables). This is a defensive coding practice.
- **`cmsRun --help`:** A simple test to verify CMSSW is properly configured.

:::::::: challenge

##### Exercise: Verify CMSSW Setup

Update your `.gitlab-ci.yml` with the configuration above and push it to GitLab. Check the pipeline logs to confirm:

1. The job runs on a `k8s-cvmfs` runner.
2. The `cmsRun --help` command executes successfully.

What do the logs tell you about the CMSSW installation?

::::::::::::::::::::::::::

:::::::: callout

A common pitfall when setting up CMSSW in GitLab is that execution fails because a setup script doesn't follow best practices for shell scripts (for example, returning non-zero exit codes even when setup is OK, or using unset variables). Even if the script exits without a visible error message, there could still be an issue. To avoid false negatives, temporarily disable strict checks (`set +u`) before running the setup command and re-enable them afterwards (`set -u`).

:::::::

:::::: keypoints

- GitLab CI runs on remote runners; capture all environment setup in `.gitlab-ci.yml` and do not rely on local machine files.
- Use a CVMFS-enabled Kubernetes runner tag (e.g., `k8s-cvmfs`); the `image:` keyword is only honored on Kubernetes runners; verify `/cvmfs/cms.cern.ch` is accessible.
- Set up CMSSW with `cmsset_default.sh`, `SCRAM_ARCH`, `cmsrel`, and `cmsenv`, then validate with `cmsRun --help`.
- Temporarily relax shell strict mode (`set +u` … `set -u`) around setup to avoid failures from unset variables or non-standard exit codes; inspect job logs to diagnose issues.

::::::
