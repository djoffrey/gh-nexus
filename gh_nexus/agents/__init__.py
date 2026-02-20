import asyncio
import logging
import subprocess
from typing import Optional

from gh_nexus.config import settings
from gh_nexus.models import AgentType, Worker

logger = logging.getLogger(__name__)


class AgentRegistry:
    def __init__(self):
        self.workers: dict[str, Worker] = {}

    def register_worker(self, worker: Worker) -> None:
        self.workers[str(worker.id)] = worker
        logger.info(f"Registered worker: {worker.name} ({worker.agent_type})")

    def unregister_worker(self, worker_id: str) -> None:
        if worker_id in self.workers:
            del self.workers[worker_id]
            logger.info(f"Unregistered worker: {worker_id}")

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        return self.workers.get(worker_id)

    def get_available_workers(self) -> list[Worker]:
        return [w for w in self.workers.values() if w.is_available]

    def get_worker_by_type(self, agent_type: AgentType) -> list[Worker]:
        return [w for w in self.workers.values() if w.agent_type == agent_type]

    def update_worker_status(self, worker_id: str, status: str) -> None:
        if worker_id in self.workers:
            self.workers[worker_id].status = status

    def list_all_workers(self) -> list[Worker]:
        return list(self.workers.values())


class AgentExecutor:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.processes: dict[str, asyncio.subprocess.Process] = {}

    async def execute_task(
        self,
        worker_id: str,
        task_description: str,
        working_dir: Optional[str] = None,
    ) -> dict:
        worker = self.registry.get_worker(worker_id)
        if not worker:
            return {"status": "error", "message": "Worker not found"}
        
        try:
            if worker.agent_type == AgentType.OPENCODE:
                result = await self._execute_opencode(task_description, working_dir)
            elif worker.agent_type == AgentType.CLAUDE_CODE:
                result = await self._execute_claude_code(task_description, working_dir)
            elif worker.agent_type == AgentType.CURSOR:
                result = await self._execute_cursor(task_description, working_dir)
            else:
                result = await self._execute_custom(worker, task_description, working_dir)
            
            self.registry.update_worker_status(worker_id, "idle")
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.registry.update_worker_status(worker_id, "error")
            return {"status": "error", "message": str(e)}

    async def _execute_opencode(self, task: str, workdir: Optional[str]) -> dict:
        cmd = ["opencode", "--prompt", task]
        if workdir:
            cmd.extend(["--dir", workdir])
        
        result = await self._run_command(cmd, workdir or ".")
        return {
            "status": "completed" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr,
        }

    async def _execute_claude_code(self, task: str, workdir: Optional[str]) -> dict:
        cmd = ["claude", "--dangerously-skip-permissions", "--print", task]
        
        result = await self._run_command(cmd, workdir or ".")
        return {
            "status": "completed" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr,
        }

    async def _execute_cursor(self, task: str, workdir: Optional[str]) -> dict:
        cmd = ["cursor", "--task", task]
        
        result = await self._run_command(cmd, workdir or ".")
        return {
            "status": "completed" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr,
        }

    async def _execute_custom(self, worker: Worker, task: str, workdir: Optional[str]) -> dict:
        if not worker.endpoint:
            return {"status": "error", "message": "No endpoint configured for custom worker"}
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                worker.endpoint,
                json={"task": task, "workdir": workdir},
                headers={"Authorization": f"Bearer {worker.api_key}"} if worker.api_key else {},
            )
            return {
                "status": "completed" if response.status_code == 200 else "failed",
                "output": response.text,
            }

    async def _run_command(
        self,
        cmd: list[str],
        cwd: str,
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise
        
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=proc.returncode,
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else "",
        )

    async def kill_worker(self, worker_id: str) -> None:
        if worker_id in self.processes:
            self.processes[worker_id].kill()
            del self.processes[worker_id]


def create_default_workers() -> list[Worker]:
    workers = []
    
    for agent in settings.agent_workers.split(","):
        agent = agent.strip()
        if not agent:
            continue
        
        agent_type = AgentType(agent.lower())
        
        workers.append(Worker(
            name=agent.title(),
            agent_type=agent_type,
            capabilities=_get_capabilities(agent_type),
        ))
    
    return workers


def _get_capabilities(agent_type: AgentType) -> list[str]:
    capabilities_map = {
        AgentType.OPENCODE: ["code_generation", "refactoring", "file_operations"],
        AgentType.CLAUDE_CODE: ["code_generation", "reasoning", "analysis"],
        AgentType.CURSOR: ["code_generation", "autocomplete", "refactoring"],
        AgentType.WIND_SURF: ["code_generation", "autocomplete"],
        AgentType.GITHUB_COPILOT: ["code_completion", "suggestions"],
    }
    return capabilities_map.get(agent_type, ["general"])
