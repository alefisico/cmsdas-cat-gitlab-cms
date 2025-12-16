---
title: "Compiling a CMSSW package"
teaching: 10
exercises: 5
questions:
- "How can I compile my CMSSW package using GitLab CI?"
- "How do I add other CMSSW packages?"
objectives:
- "Successfully compile CMSSW example analysis code in GitLab CI"
keypoints:
- "For code to be compiled in CMSSW, it needs to reside within the work area's `src` directory."
- "The analysis code from the Git repository is copied to the CMSSW work area in the CI script."
- "When using commands such as `git cms-addpkg`, the git configuration needs to be adjusted/set first."
---
Now that you know how to get a CMSSW environment, it is time to do something useful with it.

## Compiling code within the repository

For your analysis to be compiled with CMSSW, it needs to reside in the
workarea's `src` directory, and in there follow the directory structure of
two subdirectories (e.g. `AnalysisCode/MyAnalysis`) within which there can be
`src`, `interface`, `plugin` and further directories. Your analysis code
(under version control in GitLab/GitHub) will usually not contain the
CMSSW workarea. The git repository will either
contain the analysis code at the lowest level or have a subdirectory 
for the analysis code, to disentangle it from your configuration files such as the
`.gitlab-ci.yml` file.

We will use an example analysis, which selects pairs of electrons and muons.
[Download the zip file containing the analysis](../files/ZPeakAnalysis.zip)
and extract it now. The analysis code is
in a directory called `ZPeakAnalysis` within which `plugins` (the C++ code)
and `test` (the python config) directories reside.
Add this directory to your repository:

~~~
# unzip ZPeakAnalysis.zip
# mv ZPeakAnalysis ~/awesome-workshop/awesome-gitlab-cms/
cd ~/awesome-workshop/awesome-gitlab-cms/
git add ZPeakAnalysis
git commit -m "Add ZPeakAnalysis"
~~~
{: .language-bash}

When compiling the code in a GitLab pipeline, the `ZPeakAnalysis` needs
to be copied into the CMSSW workarea, and it's advisable to use environment
variables for this purpose. This would be achieved like this:

~~~
mkdir ${CMSSW_BASE}/src/AnalysisCode
cp -r "${CI_PROJECT_DIR}/ZPeakAnalysis" "${CMSSW_BASE}/src/AnalysisCode/"
~~~
{: .language-bash}

With these two commands we will now be able to extend the `.gitlab-ci.yml`
file such that we can compile our analysis code in GitLab. To improve the
readability of the file, the `CMSSW_RELEASE` is defined as a variable:

~~~
cmssw_compile:
  image: registry.cern.ch/docker.io/cmssw/el7:x86_64
  tags:
    - cvmfs
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
    - cp -r "${CI_PROJECT_DIR}/ZPeakAnalysis" "${CMSSW_BASE}/src/AnalysisCode/"
    - scram b
~~~
{: language-yaml}

> ## Exercise: Test that compilation works
>
> Commit the updated `.gitlab-ci.yml` file and check whether the GitLab pipeline succeeds.
>
{: .challenge}

## Adding CMSSW packages

> ## Always add CMSSW packages before compiling analysis code!
>
> Adding CMSSW packages has to happen *before* compiling analysis code in the
> repository, since `git cms-addpkg` will call `git cms-init` for the
> `$CMSSW_BASE/src` directory, and `git init` doesn't work if the directory
> already contains files.
{: .callout}

When developing CMSSW code, you will sometimes find yourself in the situation where you need
to rebuild one of the CMSSW packages. 
This need can arise either from the fact you are modifying this package, 
or from the fact that another CMSSW package depends on the one you are developing
and thus needs to be rebuilt.

Assuming that you would like to check out CMSSW packages using the commands
described in the [CMSSW FAQ][cmssw-faq-addpkg], a couple of additional settings need
to be applied. For instance, try running the following command in GitLab CI
after having set up CMSSW:

~~~
git cms-addpkg PhysicsTools/PatExamples
~~~
{: .language-bash}

This will fail:

~~~
Cannot find your details in the git configuration.
Please set up your full name via:
    git config --global user.name '<your name> <your last name>'
Please set up your email via:
    git config --global user.email '<your e-mail>'
Please set up your GitHub user name via:
    git config --global user.github <your github username>
~~~
{: .output}

There are a couple of options to make things work:

- set the config as described above,
- alternatively, create a `.gitconfig` in your repository and use it as described [here][custom-gitconfig],
- run `git cms-init --upstream-only` before `git cms-addpkg` to disable setting up a user remote.

For simplicity, and since we do not need to commit anything back to CMSSW from
GitLab, we will use the latter approach.
A complete `yaml` fragment that checks out a CMSSW package after having set up
CMSSW and then compiles the code looks as follows:

~~~
cmssw_addpkg:
  image: registry.cern.ch/docker.io/cmssw/el7:x86_64
  tags:
    - cvmfs
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
    # If within CERN, we can speed up interaction with CMSSW:
    - export CMSSW_MIRROR=https://:@git.cern.ch/kerberos/CMSSW.git
    # This is another trick to speed things up independent of your location:
    - export CMSSW_GIT_REFERENCE=/cvmfs/cms.cern.ch/cmssw.git.daily
    # Important: run git cms-init with --upstream-only flag to not run into
    # problems with git config
    - git cms-init --upstream-only
    - git cms-addpkg PhysicsTools/PatExamples
    - scram b
~~~
{: language-yaml}

The additional two variables that are exported here, `CMSSW_MIRROR` and
`CMSSW_GIT_REFERENCE` can speed up interaction with git, in particular
faster package checkouts. The `CMSSW_MIRROR` points to a GitHub mirror within the CERN network,
accessible only from machines within the same network, which is the case for the GitLab runners.
Settings these variables is *not* mandatory.

> ## Bonus: have you tried putting both `cmssw_compile` and `cmssw_addpkg` in the same `.gitlab-ci.yml` file?
> If you do that, the two jobs will run in parallel.
> GitLab CI also allows running jobs in stages. Stages define group of jobs running together.
> To assign a job to a stage, just add `stage: some_name` in its definition.
> Stages run in sequence according to the order typically defined at the beginning of your `.gitlab-ci.yml`.
> If any job in a stage fails, the next stage will not run.
{: .testimonial}

> ## Exercise: can you put `cmssw_compile` and `cmssw_addpkg` in two stages?
> 
{: .challenge}

> ## Solution
> ~~~
> stages:
> - compile
> - addpackage
> 
> variables:
>   CMS_PATH: /cvmfs/cms.cern.ch
>   CMSSW_RELEASE: CMSSW_10_6_30
>   SCRAM_ARCH: slc7_amd64_gcc700
>
> cmssw_compile:
>   stage: compile 
>   image: registry.cern.ch/docker.io/cmssw/el7:x86_64
>   tags:
>     - cvmfs
>   script:
>     - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
>     - export SCRAM_ARCH=${SCRAM_ARCH}
>     - cmsrel ${CMSSW_RELEASE}
>     - cd ${CMSSW_RELEASE}/src
>     - cmsenv
>     - mkdir -p AnalysisCode
>     - cp -r "${CI_PROJECT_DIR}/ZPeakAnalysis" "${CMSSW_BASE}/src/AnalysisCode/"
>     - scram b
> 
> cmssw_addpkg:
>   stage: addpackage 
>   image: registry.cern.ch/docker.io/cmssw/el7:x86_64
>   tags:
>     - cvmfs
>   script:
>     - set +u && source ${CMS_PATH}/cmsset_default.sh; set -u
>     - export SCRAM_ARCH=${SCRAM_ARCH}
>     - cmsrel ${CMSSW_RELEASE}
>     - cd ${CMSSW_RELEASE}/src
>     - cmsenv
>     # If within CERN, we can speed up interaction with CMSSW:
>     - export CMSSW_MIRROR=https://:@git.cern.ch/kerberos/CMSSW.git
>     # This is another trick to speed things up independent of your location:
>     - export CMSSW_GIT_REFERENCE=/cvmfs/cms.cern.ch/cmssw.git.daily
>     # Important: run git cms-init with --upstream-only flag to not run into
>     # problems with git config
>     - git cms-init --upstream-only
>     - git cms-addpkg PhysicsTools/PatExamples
>     - scram b
> ~~~
> {: language-yaml}
> In the solution above you will also notice that we have moved the definition of some variables
> outside of the job definition, because they are used by both jobs.
{: .solution}


{% include links.md %}

[cmssw-faq-addpkg]: https://cms-sw.github.io/faq.html#how-do-i-checkout-one-or-more-packages
[custom-gitconfig]: https://stackoverflow.com/a/18330114/11743654
