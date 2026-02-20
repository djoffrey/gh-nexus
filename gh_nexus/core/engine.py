import asyncio
import logging
from typing import Optional

from gh_nexus.agents import AgentExecutor, AgentRegistry, create_default_workers
from gh_nexus.config import settings
from gh_nexus.github import GitHubProject
from gh_nexus.models import ProjectGoal, Task, TaskResult, Worker
from gh_nexus.roles import (
    Dispatcher,
    Interpreter,
    Overseer,
    Rewarder,
    Tester,
    Visionary,
    WorkerRole,
)

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class NexusEngine:
    def __init__(self):
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
        self.goals: dict[str, ProjectGoal] = {}

    async def initialize(self) -> None:
        logger.info("Initializing Gh Nexus Engine...")
        
        workers = create_default_workers()
        for worker in workers:
            self.registry.register_worker(worker)
        
        logger.info(f"Registered {len(workers)} workers")

    async def process_requirements(self, requirements: str) -> dict:
        logger.info("Processing requirements through pipeline...")
        
        context = {"requirements": requirements}
        
        vision_result = await self.visionary.execute(context)
        self.goals = {str(g["id"]): ProjectGoal(**g) for g in vision_result["goals"]}
        
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

    async def execute_task(self, task_id: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"status": "error", "message": "Task not found"}
        
        if not task.worker_id:
            return {"status": "error", "message": "Task not assigned to any worker"}
        
        worker = self.registry.get_worker(str(task.worker_id))
        if not worker:
            return {"status": "error", "message": "Worker not found"}
        
        worker_role = WorkerRole(worker)
        result = await worker_role.execute({"task": task, "workers": self.registry.list_all_workers()})
        
        task_result = TaskResult(
            task_id=task.id,
            worker_id=worker.id,
            status=result.get("status", "unknown"),
            output=result.get("output", ""),
            quality_score=result.get("quality_score", 0.0),
        )
        self.results[str(task.id)] = task_result
        
        if result.get("status") == "completed":
            task.mark_done()
        
        return result

    async def run_tests(self) -> dict:
        context = {
            "tasks": list(self.tasks.values()),
            "results": list(self.results.values()),
        }
        return await self.tester.execute(context)

    async def evaluate_results(self) -> dict:
        context = {"results": list(self.results.values())}
        return await self.rewarder.execute(context)

    async def monitor_progress(self) -> dict:
        context = {
            "tasks": list(self.tasks.values()),
            "workers": self.registry.list_all_workers(),
        }
        return await self.overseer.execute(context)

    async def _sync_to_github(self) -> None:
        logger.info("Syncing tasks to GitHub Project...")
        
        for task in self.tasks.values():
            issue_body = f"""
{task.description}

**Status:** {task.status.value}
**Priority:** {task.priority.value}
"""
            await self.github.create_issue(
                title=task.title,
                body=issue_body,
                labels=[task.status.value.lower().replace(" ", "-"), task.priority.value.lower()],
            )

    async def shutdown(self) -> None:
        logger.info("Shutting down Gh Nexus...")
        
        for worker_id in list(self.executor.processes.keys()):
            await self.executor.kill_worker(worker_id)
