---
title: "Running a CMSSW job"
teaching: 10
exercises: 10
questions:
- "How can I run CMSSW in GitLab CI?"
- "How can avoid compiling my code for each job?"
objectives:
- "Successfully run a test job of a simplified Z to leptons analysis"
- "Use GitLab artifacts to pass compiled analysis code"
keypoints:
- "A special CMSSW image is required to successfully run CMSSW jobs"
- "Running on CMS data requires a grid proxy, or the files to be stored in the CAT managed area"
- "Several ways are available to access CMS specific files"
- "CAT provides services that avoid the danger of leaking credentials"
- "The use of artifacts allows passing results of one step to the other"
- "Since artifacts are write-protected, the directory needs to be copied before running CMSSW"
---

Being able to set up CMSSW and to compile code in GitLab, and knowing how
to access CMS data, the next step is to run test jobs to confirm that the
code yields the expected results.

> ## Fair use
> Please remember that the provided runners are shared among all users, so
> please avoid massive pipelines and CI stages with more than 5 jobs in
> parallel or that run with a parallel configuration within a job higher than 5.
>
> If you need to run these pipelines please deploy your own private runners
> to avoid affecting the rest of the users. Check the [Private GitLab Runners registration guide][gitlab-private-runner].
{: .callout}

## Requirements for running CMSSW

In most cases, you will run your tests on centrally produced files. In order
to be able to access those, you will require a grid proxy valid for the CMS
virtual organisation (VO) as described in the previous section.
For files located on EOS, please check the section on
[private information/access control][lesson-gitlab-secrets]
from the
[Continuous Integration / Continuous Development (CI/CD)][lesson-gitlab]
on how to get a Kerberos token via `kinit` (we won't be using this here).

For the analysis example provided in this lessons, we'll use a single file
from the [/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/MINIAODSIM](https://cmsweb.cern.ch/das/request?input=dataset%3D%2FDYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8%2FRunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2%2FMINIAODSIM&instance=prod/global) data set.
A copy of one file of this dataset is permanently stored on EOS in the following path: `/eos/cms/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root`.

## Ingredients for executing `cmsRun`

In principle, all we need to do is compile the code as demonstrated in
[Compiling a CMSSW package]({{ page.root }}{% link _episodes/02-compiling.md %}),
adding the grid proxy as just done in
[Obtaining a grid proxy]({{ page.root }}{% link _episodes/03-vomsproxy.md %}) or, preferably, in [CAT services for GitLab CI]({{ page.root }}{% link _episodes/04-catservices.md %})
and then execute the `cmsRun` command.
Mind that, if you tried out the example for adding CMSSW packages in the previous section, you can remove that job (`cmssw_addpkg`) from the `.gitlab-ci.yml` file, it is not needed!
Putting this together, the additional commands to run would be:

~~~
cd ${CMSSW_BASE}/src/AnalysisCode/ZPeakAnalysis/
cmsRun test/MyZPeak_cfg.py inputFiles=/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root
ls -l myZPeak.root
~~~
{: .language-bash}

where the last command just checks that an output file has been created.
However, imagine that you would like to run test jobs on more than one file
and to speed things up do this in parallel.
This would mean that you would
have to compile the code *N* times, which is a waste of resources and time.
Instead, we can pass the compiled code from the compile step to the run step
as described below.

## Using artifacts to compile code only once

[Artifacts][lesson-gitlab-artifacts] have been introduced to you as part of the
[Continuous Integration / Continuous Development (CI/CD) lesson][lesson-gitlab].
You can find more detailed information in the
[GitLab documentation for using artifacts][gitlab-artifacts].

> ## Artifacts are write-protected
> One important thing to note is that artifacts are write-protected. You
> cannot write into the artifact directory in any of the following steps.
{: .callout}

For the compiled code to be available in the subsequent steps, the directories
that should be provided need to be listed explicitly. The `yaml` code from
the compilation step in
[episode 2]({{ page.root }}{% link _episodes/02-compiling.md %})
needs to be extended as follows:

~~~
artifacts:
  # artifacts: untracked ignores configuration in the repository’s .gitignore file.
  untracked: true
  expire_in: 20 minutes
  paths:
    - ${CMSSW_RELEASE}
~~~
{: .language-yaml}

The `expire_in` is used to specify how long artifacts are to be kept before they are marked for deletion.

As path we use `${CMSSW_RELEASE}`, i.e. the full CMSSW area. Since this area
is write protected, in the subsequent steps we need to copy the whole area to a new directory and
recursively add write permissions again. In the following, this new workarea
will have to be used:

~~~
script:
  # ...
  - mkdir run
  - cp -r ${CMSSW_RELEASE} run/
  - chmod -R +w run/${CMSSW_RELEASE}/
  - cd run/${CMSSW_RELEASE}/src
  - cmsenv
~~~
{: .language-yaml}

> ## Exercise: Run CMSSW using the artifact from the compile step
>
> You should now have all required ingredients to be able to extend the
> `.gitlab-ci.yml` file such that you can reuse the compiled code in the
> `cmsRun` step.
>
{: .challenge}

> ## Solution: Run CMSSW using the artifact from the compile step (personal proxy)
>
> A possible implementation could look like this:
>
> ~~~
> cmssw_run:
  needs:
    - job: cmssw_compile
      artifacts: true
  image:
    name: gitlab-registry.cern.ch/cms-cloud/cmssw-docker/cc7-cms:latest
    entrypoint: [""]
  variables:
    CMS_PATH: /cvmfs/cms.cern.ch
    EOS_MGM_URL: "root://eoscms.cern.ch"
    CMSSW_RELEASE: CMSSW_10_6_30
    SCRAM_ARCH=slc7_amd64_gcc700
  tags:
    - cvmfs
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=${SCRAM_ARCH}
    - mkdir run
    - cp -r ${CMSSW_RELEASE} run/
    - chmod -R +w run/${CMSSW_RELEASE}/
    - cd run/${CMSSW_RELEASE}/src
    - cmsenv
    - mkdir -p ${HOME}/.globus
    - printf $GRID_USERCERT | base64 -d > ${HOME}/.globus/usercert.pem
    - printf $GRID_USERKEY | base64 -d > ${HOME}/.globus/userkey.pem
    - chmod 400 ${HOME}/.globus/userkey.pem
    - printf ${GRID_PASSWORD} | base64 -d | voms-proxy-init --voms cms --pwstdin
    - cd AnalysisCode/ZPeakAnalysis/
    - cmsRun test/MyZPeak_cfg.py inputFiles=/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root
    - ls -l myZPeak.root
> ~~~
> {: .language-yaml}
{: .solution}

> ## Solution: Run CMSSW using the artifact from the compile step (CAT EOS service)
>
> A possible implementation could look like this:
>
> ~~~
> cmssw_run_eosservice:
  needs:
    - job: cmssw_compile
      artifacts: true
  image:
    name: gitlab-registry.cern.ch/cms-cloud/cmssw-docker/cc7-cms:latest
    entrypoint: [""]
  tags:
    - cvmfs
  id_tokens:
    MY_JOB_JWT: # or any other variable name
        aud: "cms-cat-ci-datasets.app.cern.ch"
  variables:
    # File is taken from https://cms-cat-ci-datasets.web.cern.ch/
    EOSPATH: '/eos/cms/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root'
    EOS_MGM_URL: root://eoscms.cern.ch
    CMS_PATH: /cvmfs/cms.cern.ch
    EOS_MGM_URL: "root://eoscms.cern.ch"
    CMSSW_RELEASE: CMSSW_10_6_30
    SCRAM_ARCH=slc7_amd64_gcc700
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
> ~~~
> {: .language-yaml}
{: .solution}

> ## Solution: Run CMSSW using the artifact from the compile step (CAT VOMS proxy service)
>
> A possible implementation could look like this:
>
> ~~~
> cmssw_run_proxyservice:
  needs:
    - job: cmssw_compile
      artifacts: true
  image:
    name: gitlab-registry.cern.ch/cms-cloud/cmssw-docker/cc7-cms:latest
    entrypoint: [""]
  tags:
    - cvmfs
  id_tokens:
    MY_JOB_JWT: # or any other variable name
        aud: "cms-cat-grid-proxy-service.app.cern.ch"
  variables:
    # File is taken from https://cms-cat-ci-datasets.web.cern.ch/
    EOSPATH: '/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root'
    EOS_MGM_URL: root://eoscms.cern.ch
    CMS_PATH: /cvmfs/cms.cern.ch
    EOS_MGM_URL: "root://eoscms.cern.ch"
    CMSSW_RELEASE: CMSSW_10_6_30
    SCRAM_ARCH=slc7_amd64_gcc700
  before_script:
    - 'proxy=$(curl -H "Authorization: ${MY_JOB_JWT}" "https://cms-cat-grid-proxy-service.app.cern.ch/api" | tr -d \")'
  script:
    - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
    - export SCRAM_ARCH=${SCRAM_ARCH}
    - printf $proxy | base64 -d > myproxy
    - export X509_USER_PROXY=$(pwd)/myproxy
    - export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates/
    - voms-proxy-info # to test it
    - mkdir run
    - cp -r ${CMSSW_RELEASE} run/
    - chmod -R +w run/${CMSSW_RELEASE}/
    - cd run/${CMSSW_RELEASE}/src
    - cmsenv
    - cd AnalysisCode/ZPeakAnalysis/
    - cmsRun test/MyZPeak_cfg.py inputFiles=${EOSPATH}
    - ls -l myZPeak.root
> ~~~
> {: .language-yaml}
{: .solution}

In the solutions above you will notice that we have used the `needs` keyword in the yaml file to introduce dependencies between jobs.
The use of `needs` is described in the [GitLab documentation on `need`][gitlab-need].
Another possibility to introduce job dependencies is using the `dependencies` keyword, as described in the [GitLab documentation on `dependencies`][gitlab-dependencies].
The crucial difference between the two approaches is that when using `need`,
the dependent job will start as soon as the needed condition is met, regardless of the stages configuration.
The `dependencies` instead, can only be imposed between jobs in different stages,
so the dependent job will start only when all the jobs in the stage it depends on are completed.

> ## Bonus: Store the output ROOT file as artifact
>
> It could be useful to store the output ROOT file as an artifact so that you
> simply download it after job completion. Do you know how to do it?
> Hint: you need to provide the full path to it.
>
{: .testimonial}

{% include links.md %}
