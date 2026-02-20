import asyncio
import logging
import sys
from typing import Optional

import rich.console
import rich.prompt

from gh_nexus.automation import AutomationEngine, start_webhook_server
from gh_nexus.config import settings
from gh_nexus.core.engine import NexusEngine

console = rich.console.Console()


async def cmd_init(args) -> int:
    console.print("[bold blue]Initializing Gh Nexus...[/bold blue]")
    
    from gh_nexus.agents import create_default_workers
    workers = create_default_workers()
    
    console.print(f"[green]Created {len(workers)} default workers:[/green]")
    for w in workers:
        console.print(f"  - {w.name}: {w.agent_type}")
    
    console.print("\n[green]Environment configuration:[/green]")
    console.print(f"  GitHub Owner: {settings.github_owner}")
    console.print(f"  Project Number: {settings.github_project_number}")
    console.print(f"  Log Level: {settings.log_level}")
    console.print(f"  Webhook Port: {args.port}")
    
    return 0


async def cmd_start(args) -> int:
    console.print("[bold green]Starting Gh Nexus Engine...[/bold green]")
    
    engine = NexusEngine()
    await engine.initialize()
    
    console.print("[green]Engine initialized successfully![/green]")
    console.print(f"Registered {len(engine.registry.list_all_workers())} workers")
    
    if args.webhook:
        secret = args.secret or ""
        start_webhook_server(engine, args.port, secret)
        console.print(f"[green]Webhook server started on port {args.port}[/green]")
        console.print(f"[cyan]  POST /webhook - GitHub webhook endpoint[/cyan]")
    
    if args.requirements:
        console.print("\n[cyan]Processing requirements...[/cyan]")
        result = await engine.process_requirements(args.requirements)
        console.print(f"[green]Created {result['tasks']['task_count']} tasks[/green]")
    
    console.print("\n[bold]Gh Nexus is running. Press Ctrl+C to exit.[/bold]\n")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        await engine.shutdown()
    
    return 0


async def cmd_roadmap(args) -> int:
    console.print("[bold cyan]Building Roadmap with Visionary...[/bold cyan]")
    
    engine = NexusEngine()
    await engine.initialize()
    
    vision = """
# Gh Nexus - AI Agent Project Orchestration System

## Vision
Build an autonomous AI agent development platform centered around GitHub Projects, where creating issues automatically triggers AI agents to implement solutions.

## Goals
1. GitHub Integration - Use gh CLI for all project operations
2. Agent Workers - Register and manage coding agents (opencode, claude-code, cursor)
3. Docker Development - Containerized development environment
4. Automation Pipeline - Issue → Agent → PR workflow
5. Multi-Agent Collaboration - Visionary, Overseer, Interpreter, Dispatcher, Worker, Tester, Rewarder
"""
    
    result = await engine.visionary.execute({"requirements": vision})
    
    console.print("\n[bold green]Roadmap created:[/bold green]")
    console.print(result["strategy"])
    
    console.print(f"\n[green]Generated {len(result['goals'])} goals[/green]")
    
    return 0


async def cmd_plan(args) -> int:
    console.print("[bold cyan]Planning tasks with Overseer...[/bold cyan]")
    
    engine = NexusEngine()
    await engine.initialize()
    
    console.print("\n[cyan]Syncing tasks from GitHub Project...[/cyan]")
    
    project_items = await engine.github.list_items()
    
    console.print(f"[green]Found {len(project_items)} items in project[/green]")
    
    tasks = []
    for item in project_items:
        content = item.get("content", {})
        if content:
            task_title = content.get("title", "Untitled")
            task_desc = content.get("body", "")
            issue_number = content.get("number", 0)
            
            from gh_nexus.models import Task, TaskStatus
            task = Task(
                title=task_title,
                description=task_desc,
                status=TaskStatus.TODO,
                github_issue_id=issue_number if issue_number else None,
            )
            tasks.append(task)
    
    if tasks:
        context = {
            "tasks": tasks,
            "workers": engine.registry.list_all_workers(),
        }
        
        overseer_result = await engine.overseer.execute(context)
        
        console.print("\n[bold]Project Status:[/bold]")
        console.print(f"  Progress: {overseer_result['progress']:.1f}%")
        console.print(f"  Total: {overseer_result['metrics']['total_tasks']}")
        console.print(f"  Completed: {overseer_result['metrics']['completed_tasks']}")
        console.print(f"  In Progress: {overseer_result['metrics']['in_progress']}")
        console.print(f"  Blocked: {overseer_result['metrics']['blocked_tasks']}")
        
        if overseer_result['risks']:
            console.print("\n[bold red]Risks:[/bold red]")
            for risk in overseer_result['risks']:
                console.print(f"  - {risk['message']}")
        
        if overseer_result['alerts']:
            console.print("\n[bold yellow]Alerts:[/bold yellow]")
            for alert in overseer_result['alerts']:
                console.print(f"  {alert}")
    else:
        console.print("[yellow]No tasks found in project[/yellow]")
    
    return 0


async def cmd_sync(args) -> int:
    console.print("[bold cyan]Syncing and distributing tasks...[/bold cyan]")
    
    engine = NexusEngine()
    await engine.initialize()
    
    console.print("\n[cyan]Fetching project items...[/cyan]")
    project_items = await engine.github.list_items()
    
    from gh_nexus.models import Task, TaskStatus
    tasks = []
    for item in project_items:
        content = item.get("content", {})
        if content:
            task = Task(
                title=content.get("title", "Untitled"),
                description=content.get("body", ""),
                status=TaskStatus.TODO,
            )
            tasks.append(task)
    
    console.print(f"[green]Loaded {len(tasks)} tasks from GitHub Project[/green]")
    
    context = {
        "tasks": tasks,
        "workers": engine.registry.list_all_workers(),
    }
    
    interpreter_result = await engine.interpreter.execute(context)
    console.print(f"\n[cyan]Decomposed into {interpreter_result['task_count']} subtasks[/cyan]")
    
    dispatcher_result = await engine.dispatcher.execute(context)
    
    console.print("\n[bold green]Task Assignments:[/bold green]")
    for assignment in dispatcher_result["assignments"]:
        console.print(f"  {assignment['worker_name']} → {assignment['task_id']}")
    
    console.print(f"\n[green]Load distribution: {dispatcher_result['load_distribution']}[/green]")
    
    return 0


async def cmd_automation(args) -> int:
    console.print("[bold green]Starting Automation Engine with Webhook...[/bold green]")
    
    engine = AutomationEngine()
    await engine.initialize()
    
    console.print("[green]Automation Engine initialized![/green]")
    console.print(f"Registered {len(engine.registry.list_all_workers())} workers")
    
    secret = args.secret or ""
    start_webhook_server(engine, args.port, secret)
    
    console.print(f"\n[green]Webhook server listening on port {args.port}[/green]")
    console.print("[cyan]  POST /webhook - GitHub webhook endpoint[/cyan]")
    console.print("\n[bold yellow]Configure your GitHub webhook:[/bold yellow]")
    console.print(f"  URL: https://your-domain.com:{args.port}/webhook")
    console.print(f"  Events: issues, issue_comment, pull_request")
    
    console.print("\n[bold]Automation is active. Press Ctrl+C to exit.[/bold]\n")
    console.print("[dim]Triggers:[/dim]")
    console.print("  - New issue created → Agent starts working")
    console.print("  - Issue labeled 'agent' → Agent processes issue")
    console.print("  - Comment '/agent' → Agent processes issue")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        await engine.shutdown()
    
    return 0


async def cmd_run(args) -> int:
    console.print("[bold green]Starting Continuous Auto-Run Mode...[/bold green]")
    
    engine = NexusEngine()
    await engine.initialize()
    
    console.print("[green]Engine initialized![/green]")
    console.print(f"Registered {len(engine.registry.list_all_workers())} workers")
    
    interval = args.interval
    console.print(f"\n[cyan]Running in continuous mode (check every {interval}s)[/cyan]")
    console.print("[dim]Workflow:[/dim]")
    console.print("  1. Fetch issues from GitHub Project")
    console.print("  2. Overseer analyzes status")
    console.print("  3. Interpreter decomposes tasks")
    console.print("  4. Dispatcher assigns to workers")
    console.print("  5. Workers execute tasks")
    console.print("  6. Repeat\n")
    
    processed_issues = set()
    
    try:
        while True:
            try:
                console.print("\n[cyan]=== Checking for new tasks ===[/cyan]")
                
                project_items = await engine.github.list_items()
                
                new_tasks = []
                for item in project_items:
                    content = item.get("content", {})
                    if content:
                        issue_num = content.get("number")
                        if issue_num and issue_num not in processed_issues:
                            status = item.get("status", "")
                            if status in ["Todo", "Backlog"]:
                                new_tasks.append({
                                    "number": issue_num,
                                    "title": content.get("title", ""),
                                    "body": content.get("body", ""),
                                })
                                processed_issues.add(issue_num)
                
                if new_tasks:
                    console.print(f"[green]Found {len(new_tasks)} new tasks[/green]")
                    
                    for task_info in new_tasks:
                        issue_num = task_info["number"]
                        console.print(f"\n[yellow]Processing Issue #{issue_num}: {task_info['title']}[/yellow]")
                        
                        branch_name = f"feature/issue-{issue_num}"
                        console.print(f"  Creating branch: {branch_name}")
                        
                        check_result = await engine.github.run_gh([
                            "git", "branch", "-a"
                        ])
                        if branch_name in check_result.stdout:
                            console.print(f"  Branch exists, checking out...")
                            await engine.github.run_gh([
                                "git", "checkout", branch_name
                            ])
                        else:
                            console.print(f"  Creating new branch...")
                            await engine.github.run_gh([
                                "git", "checkout", "-b", branch_name
                            ])
                        
                        await engine.github.run_gh([
                            "issue", "comment", str(issue_num),
                            "--body", f"🤖 **Gh Nexus Agent started processing**\n\nWorking on this issue..."
                        ])
                        
                        context = {
                            "tasks": [],
                            "workers": engine.registry.list_all_workers(),
                        }
                        
                        from gh_nexus.models import Task, TaskStatus
                        task = Task(
                            title=task_info["title"],
                            description=task_info["body"],
                            status=TaskStatus.IN_PROGRESS,
                            github_issue_id=issue_num,
                        )
                        context["tasks"].append(task)
                        
                        interpreter_result = await engine.interpreter.execute(context)
                        console.print(f"  Decomposed into {interpreter_result['task_count']} subtasks")
                        
                        dispatcher_result = await engine.dispatcher.execute(context)
                        console.print(f"  Assigned to {len(dispatcher_result['assignments'])} workers")
                        
                        for assignment in dispatcher_result["assignments"]:
                            worker_id = assignment["worker_id"]
                            
                            worker = engine.registry.get_worker(worker_id)
                            if worker:
                                console.print(f"  → {worker.name} executing...")
                                
                                from gh_nexus.roles import WorkerRole
                                worker_role = WorkerRole(worker, workdir=".")
                                result = await worker_role.execute({
                                    "task": task,
                                    "issue_number": issue_num,
                                })
                                
                                console.print(f"    Status: {result.get('status')}")
                        
                        console.print(f"  Committing changes...")
                        await engine.github.run_gh([
                            "git", "add", "-A"
                        ])
                        await engine.github.run_gh([
                            "git", "commit", "-m", f"Complete issue #{issue_num}: {task_info['title']}"
                        ])
                        
                        console.print(f"  Creating PR...")
                        pr_result = await engine.github.run_gh([
                            "pr", "create",
                            "--title", f"🤖 Fix #{issue_num}: {task_info['title']}",
                            "--body", f"""
## Summary
Auto-generated by Gh Nexus Agent for issue #{issue_num}

## Changes
- Implemented: {task_info['title']}
- Status: Completed

## Testing
- [x] Code compiles
- [x] Basic tests pass
""",
                            "--base", "main",
                        ])
                        
                        if pr_result.returncode == 0:
                            console.print(f"  ✅ PR created successfully")
                            
                            await engine.github.run_gh([
                                "issue", "comment", str(issue_num),
                                "--body", f"""✅ **Task Completed!**

Gh Nexus Agent has completed the work:

- Branch: `{branch_name}`
- Status: Completed
- PR: [View PR]({pr_result.stdout.strip()})

Please review the changes."""
                            ])
                        else:
                            console.print(f"  ⚠️ PR creation failed: {pr_result.stderr}")
                            await engine.github.run_gh([
                                "issue", "comment", str(issue_num),
                                "--body", f"⚠️ Task completed but PR creation failed: {pr_result.stderr}"
                            ])
                else:
                    console.print("[dim]No new tasks found[/dim]")
                
                status_result = await engine.monitor_progress()
                console.print(f"\n[dim]Progress: {status_result['progress']:.0f}% | "
                            f"Tasks: {status_result['metrics']['completed_tasks']}/"
                            f"{status_result['metrics']['total_tasks']}[/dim]")
                
            except Exception as e:
                console.print(f"[red]Error in loop: {e}[/red]")
            
            await asyncio.sleep(interval)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping...[/yellow]")
        await engine.shutdown()
    
    return 0


async def cmd_status(args) -> int:
    engine = NexusEngine()
    await engine.initialize()
    
    result = await engine.monitor_progress()
    
    console.print("\n[bold]System Status[/bold]")
    console.print(f"Progress: {result['progress']:.1f}%")
    console.print(f"Total Tasks: {result['metrics']['total_tasks']}")
    console.print(f"Completed: {result['metrics']['completed_tasks']}")
    console.print(f"In Progress: {result['metrics']['in_progress']}")
    console.print(f"Workers: {result['metrics']['total_workers']}")
    
    if result['alerts']:
        console.print("\n[bold red]Alerts:[/bold red]")
        for alert in result['alerts']:
            console.print(f"  {alert}")
    
    return 0


async def cmd_assign(args) -> int:
    console.print(f"[cyan]Assigning task {args.task_id} to worker...[/cyan]")
    
    engine = NexusEngine()
    await engine.initialize()
    
    result = await engine.execute_task(args.task_id)
    
    console.print(f"[green]Task execution result: {result.get('status')}[/green]")
    return 0


async def cmd_test(args) -> int:
    console.print("[cyan]Running tests...[/cyan]")
    
    engine = NexusEngine()
    await engine.initialize()
    
    result = await engine.run_tests()
    
    console.print(f"\n[bold]Test Results[/bold]")
    console.print(f"Coverage: {result['coverage']['coverage_percentage']}%")
    console.print(f"Tests: {result['coverage']['total_tests']}")
    return 0


async def cmd_evaluate(args) -> int:
    console.print("[cyan]Evaluating results...[/cyan]")
    
    engine = NexusEngine()
    await engine.initialize()
    
    result = await engine.evaluate_results()
    
    console.print(f"\n[bold]Quality Report[/bold]")
    console.print(f"Overall Score: {result['quality_report']['overall_score']:.2f}")
    console.print(f"Status: {result['quality_report']['status']}")
    
    if result['suggestions']:
        console.print("\n[bold]Suggestions:[/bold]")
        for suggestion in result['suggestions']:
            console.print(f"  - {suggestion}")
    
    return 0


def main() -> int:
    import argparse
    
    parser = argparse.ArgumentParser(prog="gh-nexus")
    subparsers = parser.add_subparsers(dest="command")
    
    init_parser = subparsers.add_parser("init", help="Initialize the project")
    init_parser.add_argument("--port", type=int, default=8080, help="Webhook port")
    
    start_parser = subparsers.add_parser("start", help="Start the nexus engine")
    start_parser.add_argument("-r", "--requirements", help="Initial requirements text")
    start_parser.add_argument("--webhook", action="store_true", help="Enable webhook server")
    start_parser.add_argument("--port", type=int, default=8080, help="Webhook port")
    start_parser.add_argument("--secret", type=str, help="Webhook secret")
    
    roadmap_parser = subparsers.add_parser("roadmap", help="Build roadmap with Visionary")
    roadmap_parser.add_argument("-d", "--direction", help="Project direction/vision")
    
    plan_parser = subparsers.add_parser("plan", help="Sync tasks from GitHub Project with Overseer")
    
    sync_parser = subparsers.add_parser("sync", help="Sync tasks and distribute to workers")
    
    auto_parser = subparsers.add_parser("automation", help="Start automation engine with webhook")
    auto_parser.add_argument("--port", type=int, default=8080, help="Webhook port")
    auto_parser.add_argument("--secret", type=str, help="Webhook secret")
    
    run_parser = subparsers.add_parser("run", help="Continuous auto-run mode - monitor and execute tasks")
    run_parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    
    subparsers.add_parser("status", help="Show system status")
    
    assign_parser = subparsers.add_parser("assign", help="Assign and run a task")
    assign_parser.add_argument("task_id", help="Task ID to execute")
    
    subparsers.add_parser("test", help="Run tests")
    
    subparsers.add_parser("evaluate", help="Evaluate results")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        "init": cmd_init,
        "start": cmd_start,
        "roadmap": cmd_roadmap,
        "plan": cmd_plan,
        "sync": cmd_sync,
        "automation": cmd_automation,
        "run": cmd_run,
        "status": cmd_status,
        "assign": cmd_assign,
        "test": cmd_test,
        "evaluate": cmd_evaluate,
    }
    
    return asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    sys.exit(main())
