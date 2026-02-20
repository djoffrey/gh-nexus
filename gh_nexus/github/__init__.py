import asyncio
import json
import subprocess
from typing import Optional

from gh_nexus.config import settings
from gh_nexus.models import Task, TaskPriority, TaskStatus


class GitHubProject:
    def __init__(self, owner: Optional[str] = None, project_number: Optional[int] = None):
        self.owner = owner or settings.github_owner
        self.project_number = project_number or settings.github_project_number
        self.token = settings.github_token

    async def run_gh(self, args: list[str]) -> subprocess.CompletedProcess:
        cmd = ["gh"] + args
        env = {**subprocess.os.environ, "GH_TOKEN": self.token}
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await proc.communicate()
        result = subprocess.CompletedProcess(
            args=cmd,
            returncode=proc.returncode,
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else "",
        )
        return result

    async def list_items(self) -> list[dict]:
        result = await self.run_gh([
            "project", "item-list", str(self.project_number),
            "--owner", self.owner,
            "--format", "json",
        ])
        
        if result.returncode != 0:
            return []
        
        try:
            data = json.loads(result.stdout)
            return data.get("items", [])
        except json.JSONDecodeError:
            return []

    async def get_issue(self, issue_number: int) -> Optional[dict]:
        result = await self.run_gh([
            "issue", "view", str(issue_number),
            "--repo", f"{self.owner}/project",
            "--json", "title,body,state,labels,number",
        ])
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None

    async def create_issue(self, title: str, body: str = "", labels: list[str] = None) -> Optional[dict]:
        args = ["issue", "create", "--title", title, "--body", body]
        if labels:
            for label in labels:
                args.extend(["--label", label])
        
        result = await self.run_gh(args)
        if result.returncode == 0:
            return {"title": title, "body": body}
        return None

    async def add_issue_to_project(self, issue_node_id: str) -> bool:
        query = """
        mutation($projectId: ID!, $issueId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $issueId}) {
            item { id }
          }
        }
        """
        project_id = await self._get_project_id()
        if not project_id:
            return False
        
        result = await self.run_gh([
            "api", "graphql",
            "-f", f"projectId={project_id}",
            "-f", f"issueId={issue_node_id}",
            "-f", f"query={query}",
        ])
        return result.returncode == 0

    async def _get_project_id(self) -> Optional[str]:
        query = """
        query($owner: String!, $number: Int!) {
          projectV2(owner: $owner, number: $number) {
            id
          }
        }
        """
        result = await self.run_gh([
            "api", "graphql",
            "-f", f"owner={self.owner}",
            "-f", f"number={self.project_number}",
            "-f", f"query={query}",
        ])
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                return data.get("data", {}).get("projectV2", {}).get("id")
            except json.JSONDecodeError:
                pass
        return None

    async def update_item_field(self, item_id: str, field_name: str, value: str) -> bool:
        field_id = await self._get_field_id(field_name)
        if not field_id:
            return False
        
        query = f"""
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {{
          updateProjectV2ItemFieldValue(input: {{
            projectId: $projectId
            itemId: $itemId
            fieldId: $fieldId
            value: {{ text: $value }}
          }}) {{
            projectV2Item {{ id }}
          }}
        }}
        """
        project_id = await self._get_project_id()
        if not project_id:
            return False
        
        result = await self.run_gh([
            "api", "graphql",
            "-f", f"projectId={project_id}",
            "-f", f"itemId={item_id}",
            "-f", f"fieldId={field_id}",
            "-f", f"value={value}",
            "-f", f"query={query}",
        ])
        return result.returncode == 0

    async def _get_field_id(self, field_name: str) -> Optional[str]:
        query = """
        query($owner: String!, $number: Int!) {
          projectV2(owner: $owner, number: $number) {
            fields(first: 20) {
              nodes {
                name
                id
              }
            }
          }
        }
        """
        result = await self.run_gh([
            "api", "graphql",
            "-f", f"owner={self.owner}",
            "-f", f"number={self.project_number}",
            "-f", f"query={query}",
        ])
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                fields = data.get("data", {}).get("projectV2", {}).get("fields", {}).get("nodes", [])
                for field in fields:
                    if field.get("name") == field_name:
                        return field.get("id")
            except json.JSONDecodeError:
                pass
        return None
