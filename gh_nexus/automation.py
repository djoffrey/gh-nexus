import asyncio
import hashlib
import hmac
import json
import logging
import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import aiohttp

from gh_nexus.config import settings
from gh_nexus.github import GitHubProject
from gh_nexus.models import Task, TaskResult, TaskStatus

if TYPE_CHECKING:
    from gh_nexus.core.engine import NexusEngine

logger = logging.getLogger(__name__)


def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not signature:
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


class WebhookHandler(BaseHTTPRequestHandler):
    engine: Optional["NexusEngine"] = None
    webhook_secret: str = ""

    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")

    def do_POST(self):
        if self.path != "/webhook":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(content_length)

        signature = self.headers.get("X-Hub-Signature-256", "")

        if self.webhook_secret:
            if not verify_github_signature(payload, signature, self.webhook_secret):
                self.send_error(403, "Invalid signature")
                return

        try:
            event = self.headers.get("X-GitHub-Event", "")
            data = json.loads(payload)
            
            logger.info(f"Received GitHub event: {event}")

            if event == "issues":
                self.handle_issue_event(data)
            elif event == "issue_comment":
                self.handle_comment_event(data)
            elif event == "pull_request":
                self.handle_pr_event(data)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            self.send_error(500, str(e))

    def handle_issue_event(self, data: dict):
        action = data.get("action")
        issue = data.get("issue", {})
        
        if action == "opened":
            title = issue.get("title", "")
            body = issue.get("body", "")
            number = issue.get("number")
            
            logger.info(f"New issue #{number}: {title}")
            
            asyncio.create_task(self.process_new_issue(title, body, number))
        
        elif action == "labeled":
            labels = [l.get("name") for l in issue.get("labels", [])]
            if "agent" in labels or "auto" in labels:
                number = issue.get("number")
                logger.info(f"Issue #{number} labeled for agent processing")
                asyncio.create_task(self.trigger_agent_for_issue(issue))

    def handle_comment_event(self, data: dict):
        comment = data.get("comment", {})
        body = comment.get("body", "").strip()
        
        if body.startswith("/agent "):
            issue = data.get("issue", {})
            logger.info(f"Comment command for issue #{issue.get('number')}")
            asyncio.create_task(self.trigger_agent_for_issue(issue))

    def handle_pr_event(self, data: dict):
        action = data.get("action")
        pr = data.get("pull_request", {})
        
        if action == "opened" or action == "synchronize":
            logger.info(f"PR #{pr.get('number')}: {pr.get('title')}")

    async def process_new_issue(self, title: str, body: str, number: int):
        if self.engine:
            await self.engine.process_issue_from_github(title, body, number)

    async def trigger_agent_for_issue(self, issue: dict):
        if self.engine:
            await self.engine.trigger_agent_for_issue(issue)


class GitHubWebhookServer:
    def __init__(self, engine: "NexusEngine", port: int = 8080, secret: str = ""):
        self.engine = engine
        self.port = port
        self.webhook_secret = secret
        self.server: Optional[HTTPServer] = None

    def start(self):
        WebhookHandler.engine = self.engine
        WebhookHandler.webhook_secret = self.webhook_secret
        
        self.server = HTTPServer(("0.0.0.0", self.port), WebhookHandler)
        logger.info(f"Webhook server listening on port {self.port}")
        self.server.serve_forever()

    def start_async(self):
        import threading
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        return self


class WorktreeManager:
    def __init__(self, base_path: str = "/tmp/gh-nexus-workspaces"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def create_worktree(self, repo_path: str, branch: str, worktree_name: str) -> Path:
        worktree_path = self.base_path / worktree_name
        
        cmd = ["git", "worktree", "add", str(worktree_path), "-b", f"agent/{worktree_name}"]
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {result.stderr}")
        
        logger.info(f"Created worktree at {worktree_path}")
        return worktree_path

    async def cleanup_worktree(self, worktree_name: str) -> bool:
        worktree_path = self.base_path / worktree_name
        
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree_path)], capture_output=True)
        
        logger.info(f"Removed worktree at {worktree_path}")
        return True

    async def list_worktrees(self) -> list[dict]:
        result = subprocess.run(
            ["git", "worktree", "list", "--json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []


class AutomationEngine:
    def __init__(self):
        from gh_nexus.core.engine import NexusEngine
        from gh_nexus.agents import AgentExecutor, AgentRegistry, create_default_workers
        from gh_nexus.roles import (
            Dispatcher,
            Interpreter,
            Overseer,
            Rewarder,
            Tester,
            Visionary,
            WorkerRole,
        )
        
        self.github = GitHubProject()
        self.registry = AgentRegistry()
        self.executor = AgentExecutor(self.registry)
        
        self.visionary = Visionary()
        self.overseer = Overseer()
        self.interpreter = Interpreter()
        self.dispatcher = Dispatcher()
        self.tester = Tester()
        self.rewarder = Rewarder()
        
        self.tasks: dict[str, Task] = {}
        self.results: dict[str, TaskResult] = {}
        self.goals: dict[str, "ProjectGoal"] = {}
        
        self.worktree_manager = WorktreeManager()
        self.webhook_server: Optional[GitHubWebhookServer] = None

    async def initialize(self):
        logger.info("Initializing Gh Nexus Automation Engine...")
        
        from gh_nexus.agents import create_default_workers
        workers = create_default_workers()
        for worker in workers:
            self.registry.register_worker(worker)
        
        logger.info(f"Registered {len(workers)} workers")

    async def process_requirements(self, requirements: str) -> dict:
        from gh_nexus.roles import Visionary, Interpreter, Dispatcher
        
        logger.info("Processing requirements through pipeline...")
        
        context = {"requirements": requirements}
        
        vision_result = await self.visionary.execute(context)
        self.goals = {str(g["id"]): Task(**g) for g in vision_result["goals"]}
        
        context["goals"] = list(self.goals.values())
        task_result = await self.interpreter.execute(context)
        self.tasks = {str(t["id"]): Task(**t) for t in task_result["tasks"]}
        
        context["tasks"] = list(self.tasks.values())
        context["workers"] = self.registry.list_all_workers()
        
        dispatch_result = await self.dispatcher.execute(context)
        
        await self._sync_to_github()
        
        return {
            "goals": vision_result,
            "tasks": task_result,
            "assignments": dispatch_result,
        }

    async def process_issue_from_github(self, title: str, body: str, number: int):
        logger.info(f"Processing GitHub issue #{number}: {title}")
        
        requirements = f"""
Issue #{number}: {title}

{body}

Please analyze this issue and implement the required changes.
"""
        
        result = await self.process_requirements(requirements)
        
        await self.github.create_issue(
            title=f"[Agent] {title}",
            body=f"Agent processing started for issue #{number}\n\n{body}",
            labels=["agent-processing"]
        )
        
        logger.info(f"Issue #{number} processed, created {result['tasks']['task_count']} tasks")

    async def trigger_agent_for_issue(self, issue: dict):
        from gh_nexus.roles import WorkerRole
        
        number = issue.get("number")
        title = issue.get("title", "")
        body = issue.get("body", "")
        
        logger.info(f"Triggering agent for issue #{number}")
        
        worktree_name = f"issue-{number}"
        
        try:
            worktree_path = await self.worktree_manager.create_worktree(
                repo_path=str(Path.cwd()),
                branch="main",
                worktree_name=worktree_name
            )
            
            worker = self.registry.get_available_workers()[0]
            if not worker:
                logger.error("No available workers")
                return
            
            self.registry.update_worker_status(str(worker.id), "working")
            
            task = Task(
                title=f"Process issue #{number}: {title}",
                description=body,
                status=TaskStatus.IN_PROGRESS,
                worker_id=worker.id,
            )
            self.tasks[str(task.id)] = task
            
            agent = WorkerRole(worker)
            result = await agent.execute({
                "task": task,
                "workdir": str(worktree_path),
                "issue": issue,
            })
            
            if result.get("status") == "completed":
                await self._create_pull_request(worktree_name, title, number)
                
                await self.github.run_gh([
                    "issue", "comment", str(number),
                    "--body", f"Agent completed the work. Please review the changes."
                ])
            
            await self.worktree_manager.cleanup_worktree(worktree_name)
            
        except Exception as e:
            logger.error(f"Error in agent automation: {e}")
            await self.github.run_gh([
                "issue", "comment", str(number),
                "--body", f"Agent encountered an error: {str(e)}"
            ])

    async def _create_pull_request(self, branch: str, title: str, issue_number: int) -> dict:
        pr_body = f"""
## Summary
Automated PR created by Gh Nexus Agent for issue #{issue_number}

## Changes
- Implemented the requested feature/fix

## Testing
- [ ] Tests pass
- [ ] Code follows project conventions
"""
        
        result = await self.github.run_gh([
            "pr", "create",
            "--title", f"[Agent] {title}",
            "--body", pr_body,
            "--head", branch,
            "--base", "main",
        ])
        
        if result.returncode == 0:
            logger.info(f"Created PR for issue #{issue_number}")
            return {"status": "created", "output": result.stdout}
        
        logger.warning(f"Failed to create PR: {result.stderr}")
        return {"status": "failed", "error": result.stderr}

    async def _sync_to_github(self) -> None:
        logger.info("Syncing tasks to GitHub Project...")
        
        for task in self.tasks.values():
            issue_body = f"""
{task.description}

**Status:** {task.status.value}
"""
            await self.github.create_issue(
                title=task.title,
                body=issue_body,
                labels=[task.status.value.lower().replace(" ", "-")],
            )

    async def monitor_progress(self) -> dict:
        from gh_nexus.roles import Overseer
        
        context = {
            "tasks": list(self.tasks.values()),
            "workers": self.registry.list_all_workers(),
        }
        return await self.overseer.execute(context)

    async def shutdown(self) -> None:
        logger.info("Shutting down Gh Nexus...")
        
        for worker_id in list(self.executor.processes.keys()):
            await self.executor.kill_worker(worker_id)


def start_webhook_server(engine, port: int = 8080, secret: str = ""):
    server = GitHubWebhookServer(engine, port, secret)
    server.start_async()
    return server
