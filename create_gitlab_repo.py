import gitlab
import requests
import os
import re
import sys

# Function to validate environment variables
def validate_environment():
    # Validate BRANCHING_STRATEGY
    branching_strategy = os.getenv("BRANCHING_STRATEGY")
    if not branching_strategy:
        print("Error: BRANCHING_STRATEGY is not set. It must be either 'gitflow' or 'trunk'.")
        sys.exit(1)

    if branching_strategy not in ["gitflow", "trunk"]:
        print("Error: Invalid BRANCHING_STRATEGY value. It must be either 'gitflow' or 'trunk'.")
        sys.exit(1)

    # Validate and process REPO_NAME to kebab-case (retain hyphens, lowercase)
    repo_name = os.getenv("REPO_NAME")
    if not repo_name:
        print("Error: REPO_NAME is not set.")
        sys.exit(1)

    repo_name = re.sub(r"[^a-zA-Z0-9-]", "-", repo_name).lower()
    print(f"Validated environment variables. REPO_NAME = {repo_name}, BRANCHING_STRATEGY = {branching_strategy}")

    return repo_name, branching_strategy

# Validate environment variables
REPO_NAME, BRANCHING_STRATEGY = validate_environment()

# Initialize other environment variables
GROUP_PATH = os.getenv('GROUP_PATH')
GITLAB_URL = os.getenv('GITLAB_URL')
PRIVATE_TOKEN = os.getenv('GITLAB_API_TOKEN')

# Initialize the GitLab connection
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)

def create_repo(group_id, repo_name):
    try:
        repo = gl.projects.create({'name': repo_name, 'namespace_id': group_id})
        print(f"Repository '{repo_name}' created successfully.")
        return repo
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"Error creating repository '{repo_name}': {e}")
        return None

def create_branch(project, branch_name, ref):
    try:
        project.branches.create({'branch': branch_name, 'ref': ref})
        print(f"Branch '{branch_name}' created successfully.")
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"Error creating branch '{branch_name}': {e}")

def set_default_branch(project, branch_name):
    try:
        project.default_branch = branch_name
        project.auto_close_referenced_issues = False  # Disable auto-close referenced issues
        project.save()
        print(f"Default branch set to '{branch_name}'.")
    except gitlab.exceptions.GitlabUpdateError as e:
        print(f"Error setting default branch to '{branch_name}': {e}")

def configure_protected_branches(project):
    try:
        # Remove existing rules for the master branch
        try:
            master_rule = project.protectedbranches.get('master')
            master_rule.delete()
            print("Existing rules for 'master' branch removed.")
        except gitlab.exceptions.GitlabGetError:
            print("No existing rules for 'master' branch found.")

        if BRANCHING_STRATEGY == 'gitflow':
            # Create protected branches for gitflow
            project.protectedbranches.create({
                'name': 'develop',
                'merge_access_level': gitlab.const.AccessLevel.DEVELOPER,
                'push_access_level': gitlab.const.AccessLevel.MAINTAINER,
                'allow_force_push': True,
                'code_owner_approval_required': True
            })
            project.protectedbranches.create({
                'name': 'master',
                'push_access_level': gitlab.const.AccessLevel.MAINTAINER,
                'allow_force_push': True,
                'code_owner_approval_required': True
            })
            project.protectedbranches.create({
                'name': 'release*',
                'merge_access_level': gitlab.const.AccessLevel.DEVELOPER,
                'push_access_level': gitlab.const.AccessLevel.MAINTAINER,
                'allow_force_push': True,
                'code_owner_approval_required': True
            })
            print("Protected branches configured for gitflow.")
        elif BRANCHING_STRATEGY == 'trunk':
            # Create protected branch for trunk
            project.protectedbranches.create({
                'name': 'master',
                'merge_access_level': gitlab.const.AccessLevel.DEVELOPER,
                'push_access_level': gitlab.const.AccessLevel.MAINTAINER,
                'allow_force_push': True,
                'code_owner_approval_required': True
            })
            print("Protected branch rules updated for trunk.")
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"Error configuring protected branches: {e}")

def add_webhooks(project):
    try:
        webhooks = [
            {
                "url": "https://example.com/rest/bitbucket/1.0/webhook/gitlab",
                "push_events": True,
                "merge_requests_events": False,
                "enable_ssl_verification": True
            },
            {
                "url": "https://example.com/rest/bitbucket/1.0/webhook/gitlab",
                "push_events": False,
                "merge_requests_events": True,
                "enable_ssl_verification": True
            }
        ]
        for webhook in webhooks:
            project.hooks.create(webhook)
            print(f"Webhook added successfully: {webhook['url']}")
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"Error adding webhook: {e}")

def configure_merge_request_settings(project):
    try:
        # Enable merge checks
        project.merge_pipelines_enabled = True
        project.only_allow_merge_if_pipeline_succeeds = True
        project.only_allow_merge_if_all_discussions_are_resolved = True
        project.save()
        print("Merge checks enabled.")

        # Add approval rules using direct API calls
        approval_rules = [
            {"name": "CoreReviewer", "approvals_required": 1, "user_ids": [], "group_ids": [], "rule_type": "regular"},
            {"name": "SeniorDevs", "approvals_required": 1, "user_ids": [], "group_ids": [], "rule_type": "regular"},
        #    {"name": "GitFlow Compliance", "approvals_required": 1, "user_ids": [1234], "group_ids": [], "target_branch": "master", "rule_type": "regular"}
        ]
        for rule in approval_rules:
            url = f"{GITLAB_URL}/api/v4/projects/{project.id}/approval_rules"
            headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN, "Content-Type": "application/json"}
            response = requests.post(url, headers=headers, json=rule)

            if response.status_code == 201:
                print(f"Approval rule '{rule['name']}' added successfully.")
            else:
                print(f"Error adding approval rule '{rule['name']}': {response.text}")

        # Configure approval settings
        project.approvals_before_merge = 1
        project.reset_approvals_on_push = False
        project.disable_overriding_approvers_per_merge_request = True
        project.save()
        print("Approval settings configured.")
    except Exception as e:
        print(f"Error configuring merge request settings: {e}")

if __name__ == "__main__":
    try:
        group = gl.groups.get(GROUP_PATH)
        print(f"Group '{GROUP_PATH}' found.")
    except gitlab.exceptions.GitlabGetError:
        print(f"Group '{GROUP_PATH}' not found.")
        exit(1)

    group_id = group.id

    # Create a new repository
    new_repo = create_repo(group_id, REPO_NAME)
    if not new_repo:
        exit(1)

    # Configure branching strategy
    if BRANCHING_STRATEGY == 'gitflow':
        # Create develop branch and make it default
        create_branch(new_repo, 'develop', 'master')
        set_default_branch(new_repo, 'develop')
    elif BRANCHING_STRATEGY == 'trunk':
        # Create only master branch
        create_branch(new_repo, 'master', 'master')
        set_default_branch(new_repo, 'master')

    # Configure protected branches
    configure_protected_branches(new_repo)

    # Add webhooks
    add_webhooks(new_repo)

    # Configure merge request settings
    configure_merge_request_settings(new_repo)

    print(f"Repository '{REPO_NAME}' created and configured successfully.")
