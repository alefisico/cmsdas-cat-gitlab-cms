---
title: "Running a CMSSW analysis in GitLab CI/CD"
teaching: 10
exercises: 10
---

::::::::  questions

- How do I run my CMSSW analysis with GitLab CI instead of locally?
- How can I avoid re-downloading and rebuilding CMSSW on every CI job?
- How do artifacts help share build outputs between pipeline stages?

::::::::

:::::::: objectives

- Run a CMSSW analysis job in GitLab CI using a CVMFS-enabled runner.
- Configure `.gitlab-ci.yml` to reuse a built CMSSW release via artifacts instead of rebuilding each time, and handle write-protection in downstream jobs.
- Validate the analysis output (ROOT file and event counts) within the CI pipeline.

:::::::: 

:::::::: instructor

Notice that, **on purpose**, students in this lesson we are NOT running anything, but just discussing how to set up the code.
If the students only copy-paste the code, these examples will **fail**. _This is by design_, as the goal is to have them understand what they are doing, not just copy-paste code.
The reason if that they have to access files thought xrood, and therefore they need to have a valid grid proxy. That is the topic of the next lesson.

::::::::

After successfully setting up CMSSW in GitLab CI/CD in the previous lesson, you are now ready to run the next steps of the analysis workflow from [Episode 2](02-cmsswexercise.md): run the analysis on one file located in _EOS_ via xrootd, apply some selections and check the number of events in the output.

## Running a CMSSW Analysis in GitLab CI/CD

### A Simple Job

First, ensure the analysis code is committed to your GitLab repository:

```bash
# Inside your gitlab repository cmsdas-gitlab-cms/
# Download and unzip the analysis code (wget https://github.com/FNALLPC/cmsdas-cat-gitlab-cms/raw/refs/heads/main/episodes/files/ZPeakAnalysis.zip)
git add ZPeakAnalysis/
git commit -m "Add analysis code"
git push
```

Then extend your `.gitlab-ci.yml` to set up CMSSW and run the analysis with `cmsRun`:

```yaml
cmssw_setup:
  image: registry.cern.ch/docker.io/cmssw/el7:x86_64
  tags:
    - k8s-cvmfs
  variables:
    CMS_PATH: /cvmfs/cms.cern.ch
  script:
    - echo "Setting up CMSSW environment"
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=slc7_amd64_gcc700
    - cmsrel CMSSW_10_6_30
    - cd CMSSW_10_6_30/src
    - cmsenv
    - echo "Copying analysis code"
    - mkdir -p AnalysisCode
    - cp -r $CI_PROJECT_DIR/ZPeakAnalysis AnalysisCode/
    - scram b -j 4
    - cd AnalysisCode/ZPeakAnalysis/
    - echo "Running analysis code"
    - cmsRun test/MyZPeak_cfg.py
    - ls -l myZPeak.root
    - echo "Checking number of events"
    - python test/check_number_events_cmssw10.py
    - echo "Testing output"
    - python test/check_cutflows_cmssw10.py number_of_events.txt test/number_of_expected_events.txt
```

::::: discussion
#### Do you see any potential issues with this job definition?
:::::

::: solution
#### HINT: Is this how you would run your analysis locally?

The job above will work, but it’s inefficient:

- CMSSW setup (release download, build) runs every time.
- If you want multiple datasets, you’d duplicate the job and repeat the setup.
:::

### Using Artifacts for Efficiency

Use artifacts so you set up and build CMSSW once, then reuse it:

```yaml
stages:
  - compile
  - run
  - check

cmssw_compile:
  image: registry.cern.ch/docker.io/cmssw/el7:x86_64
  stage: compile
  tags:
    - k8s-cvmfs
  variables:
    CMS_PATH: /cvmfs/cms.cern.ch
    CMSSW_RELEASE: CMSSW_10_6_30
    SCRAM_ARCH: slc7_amd64_gcc700
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=${SCRAM_ARCH}
    - cmsrel ${CMSSW_RELEASE}
    - cd ${CMSSW_RELEASE}/src
    - cmsenv
    - mkdir -p AnalysisCode
    - cp -r $CI_PROJECT_DIR/ZPeakAnalysis AnalysisCode/
    - cd ${CMSSW_BASE}/src
    - scram b -j 4
  artifacts:
    untracked: true
    expire_in: 1 hour
    paths:
      - ${CMSSW_RELEASE}

cmssw_run:
  needs:
    - cmssw_compile
  stage: run
  image: registry.cern.ch/docker.io/cmssw/el7:x86_64
  tags:
    - k8s-cvmfs
  variables:
    CMS_PATH: /cvmfs/cms.cern.ch
    CMSSW_RELEASE: CMSSW_10_6_30
    SCRAM_ARCH: slc7_amd64_gcc700
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=${SCRAM_ARCH}
    - mkdir -p run
    - cp -r ${CMSSW_RELEASE} run/
    - chmod -R +w run/${CMSSW_RELEASE}/
    - cd run/${CMSSW_RELEASE}/src
    - cmsenv
    - mkdir -p AnalysisCode
    - cp -r $CI_PROJECT_DIR/ZPeakAnalysis AnalysisCode/
    - cd AnalysisCode/ZPeakAnalysis/
    - cmsRun test/MyZPeak_cfg.py
    - ls -l myZPeak.root
  artifacts:
    untracked: true
    expire_in: 1 hour
    paths:
      - ${CMSSW_RELEASE}/src/AnalysisCode/ZPeakAnalysis/myZPeak.root

check_events:
  needs:
    - cmssw_compile
    - cmssw_run
  stage: check
  image: registry.cern.ch/docker.io/cmssw/el7:x86_64
  tags:
    - k8s-cvmfs
  variables:
    CMS_PATH: /cvmfs/cms.cern.ch
    CMSSW_RELEASE: CMSSW_10_6_30
    SCRAM_ARCH: slc7_amd64_gcc700
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=${SCRAM_ARCH}
    - mkdir -p run
    - cp -r ${CMSSW_RELEASE} run/
    - chmod -R +w run/${CMSSW_RELEASE}/
    - cd run/${CMSSW_RELEASE}/src
    - cmsenv
    - mkdir -p AnalysisCode
    - cp -r $CI_PROJECT_DIR/ZPeakAnalysis AnalysisCode/
    - cd AnalysisCode/ZPeakAnalysis/
    - python test/check_number_events_cmssw10.py --input ${CMSSW_RELEASE}/src/AnalysisCode/ZPeakAnalysis/myZPeak.root
    - python test/check_cutflows_cmssw10.py number_of_events.txt test/number_of_expected_events.txt
```

For the compiled code to be available in subsequent steps, the artifacts must be explicitly defined. In the `cmssw_compile` job, we specify:

```yaml
artifacts:
  untracked: true
  expire_in: 1 hour
  paths:
    - ${CMSSW_RELEASE}
```

**Key options:**

- **`untracked: true`:** Includes files not tracked by git (ignores `.gitignore`), ensuring the full CMSSW build area is captured.
- **`expire_in`:** Specifies how long artifacts are kept before automatic deletion. Use `1 hour` for testing or `1 week` for longer workflows.
- **`paths`:** Lists directories/files to preserve. Here, `${CMSSW_RELEASE}` captures the entire CMSSW work area.

:::::::: callout

### Artifacts Are Write-Protected

Artifacts are write-protected by default. You cannot modify files directly in the artifact directory in downstream jobs.

::::::::

To work around this, copy the artifact to a new directory and add write permissions:

```yaml
script:
  - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
  - export SCRAM_ARCH=${SCRAM_ARCH}
  - mkdir -p run
  - cp -r ${CMSSW_RELEASE} run/
  - chmod -R +w run/${CMSSW_RELEASE}/
  - cd run/${CMSSW_RELEASE}/src
  - cmsenv
  - mkdir -p AnalysisCode
  - cp -r $CI_PROJECT_DIR/ZPeakAnalysis AnalysisCode/
  - cd AnalysisCode/ZPeakAnalysis/
  - cmsRun test/MyZPeak_cfg.py
```

This ensures `cmssw_run` and `check_events` can reuse the built CMSSW area without rebuilding, while still being able to write output files.

### Using `needs` vs `dependencies`

In the pipeline above, we use the `needs` keyword to define job dependencies:

```yaml
cmssw_run:
  needs:
    - cmssw_compile
  stage: run
  # ...
```

**Differences between `needs` and `dependencies`:**

| Keyword | Behavior |
|---------|----------|
| [`needs`][gitlab-need] | Job starts **immediately** when the needed job completes, regardless of stage. Enables parallelism. |
| [`dependencies`][gitlab-dependencies] | Job starts only when **all jobs in the prior stage** complete. Strictly follows stage order. |

**Best practice:** Use `needs` for faster pipelines—it allows jobs to start as soon as their dependencies are met, rather than waiting for an entire stage to finish.

::::::: discussion
#### How does this updated pipeline improve efficiency?
::::::::
::: solution
#### HINT: Are we repeating any steps unnecessarily?

- `cmssw_compile` sets up and builds CMSSW once and stores it as an artifact.
- `cmssw_run` reuses that artifact and skips re-building.
- Global variables can avoid repetition:

```yaml
...
variables:
  CMS_PATH: /cvmfs/cms.cern.ch
  CMSSW_RELEASE: CMSSW_10_6_30
  SCRAM_ARCH: slc7_amd64_gcc700

cmssw_compile:
  image: registry.cern.ch/docker.io/cmssw/el7:x86_64
  stage: compile
  tags:
    - k8s-cvmfs
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=${SCRAM_ARCH}
...
```
:::

:::: spoiler

##### Did your pipeline run successfully?

If yes, you dont need the rest of the lessons. If they are failing, continue with the next lesson.  

:::::::

:::::: keypoints

- GitLab CI runs on remote runners; every dependency and setup step must be in `.gitlab-ci.yml`.
- Use CVMFS-enabled Kubernetes runners (`k8s-cvmfs`); the `image:` keyword is honored only there.
- Split the pipeline into stages and pass the built CMSSW area via artifacts to avoid rebuilding in each job.
- Validate outputs in CI (e.g., `myZPeak.root`, event counts) to catch issues early; inspect job logs for failures.
- Artifacts are write-protected by default; downstream jobs must copy them to a writable directory using `mkdir`, `cp -r`, and `chmod -R +w`.
- Define artifacts with `untracked: true` to capture build outputs, and set `expire_in` to control automatic cleanup (e.g., `1 hour` for testing, `1 week` for production).
- Use the `needs` keyword for faster pipelines—jobs start immediately when dependencies complete, rather than waiting for entire stages to finish. `dependencies` is an alternative that strictly respects stage order.

::::::
