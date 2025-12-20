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
- Configure `.gitlab-ci.yml` to reuse a built CMSSW release via artifacts instead of rebuilding each time.
- Validate the analysis output (ROOT file and event counts) within the CI pipeline.

:::::::: 

:::::::: instructor

Notice that, **on purpose**, students in this lesson we are NOT running anything, but just discussing how to set up the code.
If the students only copy-paste the code, these examples will **fail**. _This is by design_, as the goal is to have them understand what they are doing, not just copy-paste code.
The reason if that they have to access files thought xrood, and therefore they need to have a valid grid proxy. That is the topic of the next lesson.

::::::::

After successfully setting up CMSSW in GitLab CI/CD in the previous lesson, you are now ready to run the next steps of the analysis workflow from [Episode 2](02-cmsswexercise.md): run the analysis on a small dataset and check the number of events in the output.

## Running a CMSSW Analysis in GitLab CI/CD

### A Simple Job

First, ensure the analysis code is committed to your GitLab repository:

```bash
# Inside your gitlab repository cmsdas-gitlab-cms/
# Download and unzip the analysis code (https://alefisico.github.io/cmsdas-cat-gitlab-cms/files/ZPeakAnalysis.zip)
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
    - cd AnalysisCode/ZPeakAnalysis/
    - echo "Running analysis code"
    - cmsRun test/MyZPeak_cfg.py
    - ls -l myZPeak.root
    - echo "Checking number of events"
    - python3 test/check_number_events.py
    - echo "Testing output"
    - python3 test/check_cutflows.py number_of_events.txt test/number_of_expected_events.txt
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
    - cd ${CMSSW_RELEASE}/src
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
    - cd ${CMSSW_RELEASE}/src
    - cmsenv
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
    - cd ${CMSSW_RELEASE}/src
    - cmsenv
    - cd AnalysisCode/ZPeakAnalysis/
    - python3 test/check_number_events.py --input ${CMSSW_RELEASE}/src/AnalysisCode/ZPeakAnalysis/myZPeak.root
    - python3 test/check_cutflows.py number_of_events.txt test/number_of_expected_events.txt
```

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

:::: callout

If you are satisfied with your pipeline, commit and push the changes. Check the pipeline logs for errors and verify that output files are produced as expected.

:::::::

:::::: keypoints

- GitLab CI runs on remote runners; every dependency and setup step must be in `.gitlab-ci.yml`.
- Split the pipeline into stages and pass the built CMSSW area via artifacts to avoid rebuilding in each job.
- Validate outputs in CI (e.g., `myZPeak.root`, event counts) to catch issues early; inspect job logs for failures.

::::::
