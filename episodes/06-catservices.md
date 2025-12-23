---
title: "CAT services for GitLab CI"
teaching: 10
exercises: 10
---

::::::::  questions

- How can I access CMS data stored on EOS from GitLab CI without managing my own grid certificates?
- What are CAT services and why do they only work in the `cms-analysis` namespace?
- How do I request authentication tokens for EOS access and VOMS proxies in CI jobs?

::::::::

:::::::: objectives

- Understand the purpose and security model of CAT services for GitLab CI.
- Use the CAT EOS file service to access CMS data on EOS via JWT-authenticated tokens.
- Use the CAT VOMS proxy service to obtain a grid proxy for the CMS VO without storing personal certificates.

::::::::

:::::::: discussion

## Did you find it difficult to access CMS data in GitLab CI/CD?

Accessing CMS data stored on EOS or using grid resources in GitLab CI/CD can be challenging, especially for newcomers. You must manage authentication, permissions, and complex data access methods. The Common Analysis Tools (CAT) group in CMS provides services to simplify these tasks.

::::::::::::::::::::::

::::::::: discussion

## Why CERN GitLab Instead of GitHub?

CERN GitLab is tailored for the CERN community and offers seamless integration with CERN infrastructure: CVMFS, EOS storage, and grid computing resources. This makes it ideal for CMS analysts working with large datasets and complex workflows.

If you host your analysis on GitHub, you must manually set up access to CMS resources—a cumbersome and error-prone process. CERN GitLab lets you leverage **CAT services** that simplify data access and authentication, so you can focus on analysis rather than infrastructure.

::::::::::::::::::::::

## The [cms-analysis][cms-analysis] user code space

The Common Analysis Tools (CAT) group maintains a dedicated CERN GitLab namespace called [cms-analysis][cms-analysis], where any CMS member can store their analysis code. It is documented in the [CAT documentation pages][cat-docs].

The namespace is organized into groups and subgroups following the CMS Physics Coordination structure. You can request an area in the PAG-specific group that best matches your analysis.

### Request an Area Anytime

Keep your analysis code under version control from the start. You can request an area at any stage (in fact we invite you to do so):

- You can create an area with a temporary name initially, then rename it to match your CADI line when the analysis matures.
- Request an area for your analysis at [cms-analysis][cms-analysis].

### The services described here only work in [cms-analysis][cms-analysis]

For security reasons, the services described here **only work if your project is in the `cms-analysis` namespace**.

To move your current project:

1. Go to **Settings > General > Advanced > Transfer project**.
2. Select `cms-analysis/CMSDAS/CAT-tutorials` as the new namespace (for testing).
3. For production work, select the relevant POG/PAG subgroup.

---

## Using the CAT EOS file service

CAT maintains a service account, `cmscat`, that has CMS VO membership and can access EOS. CAT provides a service to request short-lived EOS tokens in CI jobs, allowing you to access CMS files on behalf of the `cmscat` service account.

**Files accessible:** `/eos/cms/store/group/cat`

For detailed documentation, see the [CAT CI dataset service](https://cms-analysis.docs.cern.ch/code/services/#usage-of-gitlab-ci-dataset-service).

### The file you need is not there?

If the file you need is not in `/eos/cms/store/group/cat`, request it by creating a merge request to [cms-analysis/services/ci-dataset-files](https://gitlab.cern.ch/cms-analysis/services/ci-dataset-files/-/blob/master/datasets.txt).

### How the Service Works

Two steps are required:

**Step 1:** Configure your job to create a JWT (JSON Web Token) for authentication:

```yaml
id_tokens:
  MY_JOB_JWT:
    aud: "cms-cat-ci-datasets.app.cern.ch"
```

**Step 2:** Query the CAT service to get a short-lived EOS token:

```bash
XrdSecsssENDORSEMENT=$(curl -H "Authorization: ${MY_JOB_JWT}" "https://cms-cat-ci-datasets.app.cern.ch/api?eospath=${EOSPATH}" | tr -d \")
```

Then access the file using:

```bash
root://eoscms.cern.ch/${EOSPATH}?authz=${XrdSecsssENDORSEMENT}&xrd.wantprot=unix
```

Where `EOSPATH` is a variable holding a path of a file on EOS.
Now you can access the file with a path that includes the newly generated token at the end, as: `root://eoscms.cern.ch/${EOSPATH}?authz=${XrdSecsssENDORSEMENT}&xrd.wantprot=unix`.

::::::: challenge

### Exercise: Copy a File Using the CAT EOS Service

Try copying this file from the CAT storage:

```bash
/eos/cms/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root
```

:::::::: solution


```yaml
test_eos_service:
  image:
    name: registry.cern.ch/docker.io/cmssw/el7:x86_64
  tags:
    - cvmfs
  id_tokens:
    MY_JOB_JWT:
      aud: "cms-cat-ci-datasets.app.cern.ch"
  variables:
    EOSPATH: '/eos/cms/store/group/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root'
    EOS_MGM_URL: root://eoscms.cern.ch
  before_script:
    - 'XrdSecsssENDORSEMENT=$(curl -H "Authorization: ${MY_JOB_JWT}" "https://cms-cat-ci-datasets.app.cern.ch/api?eospath=${EOSPATH}" | tr -d \")'
  script:
    - xrdcp "${EOS_MGM_URL}/${EOSPATH}?authz=${XrdSecsssENDORSEMENT}&xrd.wantprot=unix" test.root
    - ls -l test.root
```

::::::::
::::::::::::::::

---

## Using the CAT VOMS Proxy Service

The `cmscat` service account is a CMS VO member and can request VOMS proxies. If your project is in `cms-analysis`, it can request a VOMS proxy from a service at `cms-cat-grid-proxy-service.app.cern.ch`, in much the same way as the CAT EOS service requests a proxy to `cms-cat-ci-datasets.app.cern.ch` above.

The proxy is returned as a `base64`-encoded string with a lifetime matching your CI job duration.

### Exercise: Set up a CI Job to Obtain a Grid Proxy

Set up a CI job that retrieves and validates a VOMS proxy from the CAT service.

**Step 1:** Configure your job to create a JWT:

```yaml
id_tokens:
  MY_JOB_JWT:
    aud: "cms-cat-grid-proxy-service.app.cern.ch"
```

**Step 2:** Query the CAT service to get a proxy:

```bash
proxy=$(curl --fail-with-body -H "Authorization: ${MY_JOB_JWT}" "https://cms-cat-grid-proxy-service.app.cern.ch/api" | tr -d \")
```

**Step 3:** Decode and store the proxy:

```yaml
  - printf $proxy | base64 -d > myproxy
  - export X509_USER_PROXY=$(pwd)/myproxy
```

### Important: CVMFS and Environment Variables

Your image **must have CVMFS mounted** (e.g., `tags: [cvmfs]`). Depending on the image environment, you may also need to export grid security variables:

```yaml
  - export X509_VOMS_DIR=/cvmfs/grid.cern.ch/etc/grid-security/vomsdir/
  - export VOMS_USERCONF=/cvmfs/grid.cern.ch/etc/grid-security/vomses/
  - export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates/
```

:::::::: spoiler

### Solution: CAT VOMS Proxy Service

```yaml
test_proxy_service:
  image:
    name: registry.cern.ch/docker.io/cmssw/el7:x86_64
  tags:
    - cvmfs
  id_tokens:
    MY_JOB_JWT:
      aud: "cms-cat-grid-proxy-service.app.cern.ch"
  before_script:
    - 'proxy=$(curl -H "Authorization: ${MY_JOB_JWT}" "https://cms-cat-grid-proxy-service.app.cern.ch/api" | tr -d \")'
  script:
    - printf $proxy | base64 -d > myproxy
    - export X509_USER_PROXY=$(pwd)/myproxy
    - export X509_CERT_DIR=/cvmfs/grid.cern.ch/etc/grid-security/certificates/
    - voms-proxy-info
```

::::::::

---

:::::: callout

With both CAT services in place, you now have automatic, secure access to CMS data and grid resources in your CI pipeline—no manual certificate management required!

::::::

:::::: keypoints

- CAT services simplify CMS resource access in GitLab CI by eliminating manual certificate and credential management.
- CAT services only work in the `cms-analysis` namespace for security; move your project there via **Settings > General > Advanced > Transfer project**.
- The CAT EOS file service provides JWT-authenticated access to datasets in `/eos/cms/store/group/cat` via the `cmscat` service account.
- The CAT VOMS proxy service provides short-lived grid proxies without storing personal certificates; proxies are returned as base64-encoded strings.
- Both services require configuring `id_tokens` in `.gitlab-ci.yml` and querying CAT endpoints to retrieve authentication tokens.

::::::
