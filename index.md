---
site: sandpaper::sandpaper_site
---

In this lesson you will learn how to run jobs that require a CMS-specific software stack and how to access protected files in GitLab CI using the GitLab installation at CERN.
We will use the use case of running [CMS software (CMSSW)][cmssw] jobs as an example.

:::::::::::::::::::::::::::::::::::: prereq

Basic understanding of the purpose of GitLab CI and of its use.
Basic understanding of using and developing in [CMSSW][cmssw].
::::::::::::::::::::::::::::::::::::::::

:::::: keypoints

- "Special GitLab CVMFS runners are required to run CI jobs that need CVMFS, e.g. to run CMSSW."
- "If the setup script tries to access unset variables, then that can cause the CI to fail when using strict shell scripting checks."
::::::
