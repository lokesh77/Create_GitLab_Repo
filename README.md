# GitLab Repository Automation

This project automates the creation and configuration of GitLab repositories using the GitLab API. It supports both `gitflow` and `trunk` branching strategies and includes features like branch protection, webhook addition, and merge request settings configuration.


## Pipeline Execution

To execute the pipeline for repository creation, follow these steps:

1. Navigate to the **Pipeline URL**:  
   [Create_GitLab_Repo_Using_Pipeline](https://gitlab.com/lokesh7797/Create_GitLab_Repo/-/pipelines/new)

2. Select the branch:  
   Choose the `feature/Create_Repo` branch from the branch dropdown.

3. Enter the required variables:  
   - `GROUP_PATH`: The GitLab group path (e.g., `lokesh7797/Create_GitLab_Repo`).
   - `REPO_NAME`: The name of the repository to be created (e.g., `sample-repo`).
   - `BRANCHING_STRATEGY`: Set to `gitflow` for `develop` branch or `trunk` for only `master` branch.

4. Click **Run Pipeline** to start the process.

### Permissions

- **Only maintainers** are allowed to create and execute the pipeline for repository creation.  
  Ensure you have the appropriate permissions before attempting to run the pipeline.

## Branching Strategies

### Gitflow
- Creates a `develop` branch and sets it as the default branch.
- Protects `develop`, `master`, and `release*` branches.

### Trunk
- Creates only the `master` branch and sets it as the default branch.
- Protects the `master` branch.

## Manual Configuration: Merge Request Workflow

Currently, the **Merge Request Workflow settings** are not working with the current GitLab API version. These settings need to be implemented manually in the GitLab UI.


1. **Branch Name Pattern**: `feature/*`    **Target Branch**: `develop`

2. **Branch Name Pattern**: `release/*`    **Target Branch**: `master`

## Features

- **Environment Variable Validation**: Ensures required variables are set and valid.
- **Repository Creation**: Creates a new repository in the specified GitLab group.
- **Branch Management**: Supports creating branches and setting the default branch.
- **Branch Protection**: Configures branch protection rules based on the branching strategy.
- **Webhooks**: Adds predefined webhooks for external integrations.
- **Merge Request Settings**: Configures merge checks and approval rules for merge requests.
