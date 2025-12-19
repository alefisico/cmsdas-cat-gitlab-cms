---
title: "A simple CMSSW example"
teaching: 10
exercises: 10
---

:::::: questions

- How can I compile my CMSSW analysis code?
- What is the correct way to add and organize my analysis code in a CMSSW work area?
- How can I verify that my code changes produce the expected results?

::::::

:::::: objectives

- Successfully set up and compile example analysis code in a CMSSW environment.
- Understand how to organize and add your analysis code to the CMSSW work area.
- Learn how to test and compare analysis results after making code or selection changes.

::::::

## A Simple Example with CMSSW

Let’s walk through a basic example for CMSSW-based analyses. We’ll use a simple analysis code that selects pairs of electrons and muons, compile it in a CMSSW environment, and run it on a small dataset. This workflow is typical for HEP analysis at CERN. For you to understand the workflow, we will first try to run the analysis code on your "local" machine (cmslpc, lxplus, university machine).

:::::::: checklist

What You’ll Do:

- [ ] Set up a CMSSW environment.
- [ ] Add example analysis code.
- [ ] Run the analysis code on a few events and create a ROOT file with histograms.
- [ ] Create a text file with the number of processed events.
- [ ] Modify the selection criteria and compare the results with the previous run.
:::::::::::::::::::::::::::::::

### Step 1: Set Up Your CMSSW Environment

For this local test, create a new CMSSW work area **outside your GitLab repository**:

```bash
# Go to a folder outside your gitlab repository
cmsrel CMSSW_15_1_0
cd CMSSW_15_1_0/src
cmsenv
```
This sets up a fresh CMSSW work area.

If your analysis depends on other CMSSW packages, add them using:

```bash
git cms-addpkg PhysicsTools/PatExamples
```
This ensures all necessary packages are available.

:::::::: spoiler

### If the previous command fails

If you see an error about missing git configuration, set your name and email:

```bash
Cannot find your details in the git configuration.
Please set up your full name via:
    git config --global user.name '<your name> <your last name>'
Please set up your email via:
    git config --global user.email '<your e-mail>'
Please set up your GitHub user name via:
    git config --global user.github <your github username>
```

There are a couple of options to make things work:

- set the config as described above,
- alternatively, create a `.gitconfig` in your repository and use it as described [here][custom-gitconfig],
- run `git cms-init --upstream-only` before `git cms-addpkg` to disable setting up a user remote.
:::::::::::

:::::::::::: callout

#### Always add CMSSW packages before compiling or adding analysis code

Adding CMSSW packages has to happen *before* adding or compiling analysis code in the repository, since `git cms-addpkg` will call `git cms-init` for the `$CMSSW_BASE/src` directory, and `git init` doesn't work if the directory already contains files.
::::::::::::

---

### Step 2: Add Analysis Code to Your CMSSW Work Area

Your analysis code must be placed inside the work area’s `src` directory, following the standard CMSSW structure (e.g., `AnalysisCode/MyAnalysis`). Usually, your Git repository contains only your analysis code, not the full CMSSW work area.

In this example, we’ll use a sample analysis that selects pairs of electrons and muons. The code is provided as a [zip file](episodes/files/ZPeakAnalysis.zip), containing a `ZPeakAnalysis` directory with `plugins` (C++ code) and `test` (Python config).

Download and extract the code:

```bash
# Go to your project folder from lesson 1
cd ~/nobackup/cmsdas/cmsdas-gitlab-cms/   # Use ~/nobackup for cmslpc users
wget https://alefisico.github.io/cmsdas-cat-gitlab-cms/files/ZPeakAnalysis.zip
unzip ZPeakAnalysis.zip
```

Copy the analysis code into your CMSSW work area:

```bash
cd ${CMSSW_BASE}/src/
mkdir -p AnalysisCode
cp -r ~/cmsdas/cmsdas-gitlab-cms/ZPeakAnalysis AnalysisCode/
```

Now your code is in the right place for CMSSW to find and compile it.

---

### Step 3: Compile the Code

Compile the analysis code:

```bash
cd ${CMSSW_BASE}/src/
scram b -j 4
```
The `-j 4` flag uses 4 CPU cores for faster compilation.

---

### Step 4: Run the Analysis Code Locally

Now that the code is compiled, run it on a small dataset to test it:

```bash
cmsenv   # Good practice to ensure the environment is set
cd ${CMSSW_BASE}/src/AnalysisCode/ZPeakAnalysis/
cmsRun test/MyZPeak_cfg.py
```

```output
19-Dec-2025 15:46:09 CST  Initiating request to open file root://cmseos.fnal.gov//store/user/cmsdas/2026/short_exercises/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root
19-Dec-2025 15:46:15 CST  Successfully opened file root://cmseos.fnal.gov//store/user/cmsdas/2026/short_exercises/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root
Begin processing the 1st record. Run 1, Event 15930998, LumiSection 5897 on stream 0 at 19-Dec-2025 15:46:15.905 CST
Begin processing the 1001st record. Run 1, Event 15933554, LumiSection 5897 on stream 0 at 19-Dec-2025 15:46:32.266 CST
Begin processing the 2001st record. Run 1, Event 15936188, LumiSection 5898 on stream 0 at 19-Dec-2025 15:46:32.534 CST
Begin processing the 3001st record. Run 1, Event 130736047, LumiSection 48385 on stream 0 at 19-Dec-2025 15:46:32.809 CST
....
Begin processing the 54001st record. Run 1, Event 1743339, LumiSection 646 on stream 0 at 19-Dec-2025 15:46:48.177 CST
19-Dec-2025 15:46:48 CST  Closed file root://cmseos.fnal.gov//store/user/cmsdas/2026/short_exercises/cat/datasets/MINIAODSIM/RunIISummer20UL17MiniAODv2-106X_mc2017_realistic_v9-v2/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/2C5565D7-ADE5-2C40-A0E5-BDFCCF40640E.root
```

If everything went well, you should see an output file called `myZPeak.root`. You can open it with ROOT to check the histograms.

---

### Step 5: Check the Number of Events

To check the number of events in your histograms, run:

```bash
python3 test/check_number_events.py
```

This creates a text file called `number_of_events.txt` with output like:

```output
muonMult: 54856.0
eleMult:  54856.0
mumuMass: 16324.0
```

---

### Step 6: Modify the Selection and Compare Results

Now, let’s modify the selection criteria and compare the results:

1. Rerun the analysis with a modified selection:
   ```bash
   cmsRun test/MyZPeak_cfg.py minPt=40
   ```
   This changes the minimum muon transverse momentum to 40 GeV.

2. Check the number of events again:
   ```bash
   cp number_of_events.txt number_of_events_old.txt
   python3 test/check_number_events.py
   ```

3. Compare the two results:
   ```bash
   python3 test/check_cutflows.py number_of_events.txt test/number_of_expected_events.txt
   ```
   You should see a difference in the number of selected events due to the modified selection. For reference, expected results are provided in `test/number_of_expected_events.txt`.

---

:::::: testimonial

#### Why Compare results?

**Creating a test to compare results is vital in analysis development!**

As you develop your analysis, you’ll often modify selection criteria and code. This can lead to unintended changes in the number of selected events. By creating tests to compare results after each modification, you ensure your changes have the intended effect and do not introduce errors. This practice is crucial for maintaining the integrity of your analysis as it evolves.
::::::::::::::::::::::

:::::: keypoints

- CMSSW analysis code must be placed inside the `src` directory of your CMSSW work area to be compiled.
- Always add required CMSSW packages before copying or compiling your analysis code.
- Running and testing your analysis locally helps catch issues before automating with CI.
- Comparing results after code or selection changes is essential for reliable and reproducible analyses.

::::::
