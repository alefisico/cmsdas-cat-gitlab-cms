---
title: "Putting It All Together: Final Run with CAT Services"
teaching: 10
exercises: 10
---

:::::: questions

- How do I combine CMSSW compilation, data access, and authentication into a single CI/CD pipeline?
- What are the trade-offs between using personal grid credentials versus CAT services?
- How can I use both CAT EOS and VOMS proxy services in the same pipeline?

::::::::

:::::::: objectives

- Create a complete `.gitlab-ci.yml` pipeline that compiles CMSSW, obtains authentication, and runs analysis on EOS data.
- Implement data access using either CAT EOS file service or CAT VOMS proxy service.
- Compare and choose between personal credentials and CAT services based on your workflow.

::::::::

## Putting It All Together: Final Run with CAT Services

In this final episode, you will combine everything you've learned to build a complete GitLab CI/CD pipeline that runs a CMSSW analysis using CAT services for data access and authentication. Your pipeline will include:

1. **Set up the CMSSW environment** — Configure CMSSW version and environment variables.
2. **Obtain authentication** — Use CAT services or personal grid credentials for CMS resource access.
3. **Access CMS data on EOS** — Read input datasets via XRootD.
4. **Run the CMSSW analysis** — Execute analysis code on input data.
5. **Validate output** — Store and review analysis results.

---

## Accessing Files on EOS via XRootD

Most analyses run on centrally produced files stored on EOS. To access them, you need a valid grid proxy for the CMS Virtual Organisation (VO).

We have already used EOS files in previous lessons. For this final example, we'll explicitly define and use a single file from the [DYJetsToLL dataset](https://cmsweb.cern.ch/das/request?input=dataset%3D%2FDYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8%2FRunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2%2FMINIAODSIM&instance=prod/global).

A copy is stored permanently on EOS at:

```output
/eos/cms/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root
```

### Test Locally First

Before running in CI, test file access on your local machine:

```bash
cd ${CMSSW_BASE}/src/AnalysisCode/ZPeakAnalysis/
cmsRun test/MyZPeak_cfg.py inputFiles=/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root
ls -l myZPeak.root
```

This verifies your grid proxy and data access setup before committing to CI.

---

## Three Approaches: Complete Examples

We show three different approaches to running your analysis in CI. Choose the one that best fits your use case.

:::::::: tab

### Approach 1: Using Personal Grid Credentials

If your project is in a personal namespace (not `cms-analysis`), use your own grid credentials stored as protected CI/CD variables:

```yaml
cmssw_run:
  image:
    name: gitlab-registry.cern.ch/cms-cloud/cmssw-docker/cc7-cms:latest
    entrypoint: [""]
  tags:
    - cvmfs
  variables:
    CMS_PATH: /cvmfs/cms.cern.ch
    EOS_MGM_URL: "root://eoscms.cern.ch"
    CMSSW_RELEASE: CMSSW_10_6_30
    SCRAM_ARCH: slc7_amd64_gcc700
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=${SCRAM_ARCH}
    - mkdir run
    - cp -r ${CMSSW_RELEASE} run/
    - chmod -R +w run/${CMSSW_RELEASE}/
    - cd run/${CMSSW_RELEASE}/src
    - cmsenv
    - mkdir -p ${HOME}/.globus
    - printf "${GRID_USERCERT}" | base64 -d > ${HOME}/.globus/usercert.pem
    - printf "${GRID_USERKEY}" | base64 -d > ${HOME}/.globus/userkey.pem
    - chmod 400 ${HOME}/.globus/userkey.pem
    - printf "${GRID_PASSWORD}" | base64 -d | voms-proxy-init --voms cms --pwstdin
    - cd AnalysisCode/ZPeakAnalysis/
    - cmsRun test/MyZPeak_cfg.py inputFiles=/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root
    - ls -l myZPeak.root
    - python3 test/check_number_events.py
    - python3 test/check_cutflows.py number_of_events.txt test/number_of_expected_events.txt
```

**Pros:** Full control; works in any namespace.  
**Cons:** Requires managing your own credentials; higher security risk if exposed.


### Approach 2: Using CAT EOS File Service

If your project is in `cms-analysis`, use the CAT EOS file service for simple file access:

```yaml
stages:
  - compile
  - run

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

cmssw_run_eos_service:
  needs:
    - job: cmssw_compile
      artifacts: true
  stage: run
  image:
    name: gitlab-registry.cern.ch/cms-cloud/cmssw-docker/cc7-cms:latest
    entrypoint: [""]
  tags:
    - k8s-cvmfs
  id_tokens:
    MY_JOB_JWT:
      aud: "cms-cat-ci-datasets.app.cern.ch"
  variables:
    EOSPATH: '/eos/cms/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root'
    EOS_MGM_URL: "root://eoscms.cern.ch"
  before_script:
    - 'XrdSecsssENDORSEMENT=$(curl -H "Authorization: ${MY_JOB_JWT}" "https://cms-cat-ci-datasets.app.cern.ch/api?eospath=${EOSPATH}" | tr -d \")'
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=${SCRAM_ARCH}
    - mkdir run
    - cp -r ${CMSSW_RELEASE} run/
    - chmod -R +w run/${CMSSW_RELEASE}/
    - cd run/${CMSSW_RELEASE}/src
    - cmsenv
    - cd AnalysisCode/ZPeakAnalysis/
    - cmsRun test/MyZPeak_cfg.py inputFiles="${EOS_MGM_URL}/${EOSPATH}?authz=${XrdSecsssENDORSEMENT}&xrd.wantprot=unix"
    - ls -l myZPeak.root
    - python3 test/check_number_events.py
    - python3 test/check_cutflows.py number_of_events.txt test/number_of_expected_events.txt
```

**Pros:** No personal credential management; secure; requires no CI/CD variables.  
**Cons:** Only works in `cms-analysis` namespace; limited to CAT-hosted files.


### Approach 3: Using CAT VOMS Proxy Service

For maximum flexibility, use the CAT VOMS proxy service to access any CMS data:

```yaml
stages:
  - compile
  - run

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

cmssw_run_proxy_service:
  needs:
    - job: cmssw_compile
      artifacts: true
  stage: run
  image:
    name: gitlab-registry.cern.ch/cms-cloud/cmssw-docker/cc7-cms:latest
    entrypoint: [""]
  tags:
    - k8s-cvmfs
  id_tokens:
    MY_JOB_JWT:
      aud: "cms-cat-grid-proxy-service.app.cern.ch"
  variables:
    EOS_MGM_URL: "root://eoscms.cern.ch"
    EOSPATH: '/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root'
  before_script:
    - 'proxy=$(curl -H "Authorization: ${MY_JOB_JWT}" "https://cms-cat-grid-proxy-service.app.cern.ch/api" | tr -d \")'
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=${SCRAM_ARCH}
    - printf "${proxy}" | base64 -d > myproxy
    - export X509_USER_PROXY=$(pwd)/myproxy
    - export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates/
    - voms-proxy-info
    - mkdir run
    - cp -r ${CMSSW_RELEASE} run/
    - chmod -R +w run/${CMSSW_RELEASE}/
    - cd run/${CMSSW_RELEASE}/src
    - cmsenv
    - cd AnalysisCode/ZPeakAnalysis/
    - cmsRun test/MyZPeak_cfg.py inputFiles=${EOSPATH}
    - ls -l myZPeak.root
    - python3 test/check_number_events.py
    - python3 test/check_cutflows.py number_of_events.txt test/number_of_expected_events.txt
```

**Pros:** Maximum flexibility; works for any CMS dataset; no credential storage.  
**Cons:** Only works in `cms-analysis` namespace; slightly more complex setup.

:::::::::::::::

## Challenge: Create Your Complete Pipeline

:::::: challenge

Choose one of the three approaches above and implement a complete `.gitlab-ci.yml` file that:

1. Compiles your CMSSW analysis code.
2. Obtains authentication (using your chosen method).
3. Runs the analysis on the example file.
4. Validates the output.

Commit and push to GitLab, then check the **CI/CD > Pipelines** page to see it run. What happens? Did it succeed?

::::::

:::::::: callout

Congratulations! You have now built a complete, production-ready CI/CD pipeline for CMS analysis using GitLab. You can extend this pattern to multiple datasets, batch processing, and complex workflows.

::::::::
