---
title: Setup
---

## Software Setup

To work with CERN GitLab CI/CD, you need to have Git installed on your local machine and set up SSH keys for secure communication with the GitLab server.

---

### Adding Your SSH Key to CERN GitLab

To push code to your GitLab repository using SSH, you need to add your public SSH key to your CERN GitLab account.

#### Step 1: Check for an existing SSH key

Open a terminal and run:

```bash
ls ~/.ssh/id_rsa.pub
```

If the file exists, you already have an SSH key. If not, generate one with:

```bash
ssh-keygen -t rsa -b 4096 -C "your.email@cern.ch"
```

Press Enter to accept the default file location and set a passphrase if you wish.

#### Step 2: Copy your public SSH key

Run:

```bash
cat ~/.ssh/id_rsa.pub
```

Copy the entire output (the key).

#### Step 3: Add the SSH key to CERN GitLab

1. Go to [CERN GitLab SSH Keys page](https://gitlab.cern.ch/-/user_settings/ssh_keys).
2. Paste your public key into the **Key** field.
3. Optionally, add a title (e.g., "My Laptop").
4. Click **Add key**.

You can now use SSH to interact with your GitLab repositories.

:::::::::: instructor

#### Windows

We dont have instructions for windows. Do you want to add some? Follow [CONTRIBUTING.md](../.CONTRIBUTING.md) guidelines to propose a change.

:::::::::::::::::::::::::

---

### Create a New GitLab Project to Follow Along

To get the most out of this tutorial, create your own GitLab project and follow each step hands-on.

#### Step 1: Create a new project on GitLab

1. Go to [GitLab CERN New Project][gitlab-newproject].
2. Click **"Create blank project"**.
3. Enter a project name, for example: `cmsdas-gitlab-cms`.
4. In Project URL, ensure it reads something like `gitlab.cern.ch/YOUR_USERNAME/cmsdas-gitlab-cms`.
5. Set the project visibility. The default **Private** is fine for this tutorial.
6. Click **"Create project"**.

#### Step 2: Clone your new project locally

We recommend working in a directory called `cmsdas` in your home folder. Replace `${USER}` with your CERN username if it differs from your local username.

```bash
mkdir -p ~/cmsdas
cd ~/cmsdas
git clone ssh://git@gitlab.cern.ch:7999/${USER}/cmsdas-gitlab-cms.git
cd cmsdas-gitlab-cms
```

You are now ready to start adding files and configuring your project.
