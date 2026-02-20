import asyncio
import logging
import sys

import rich.console
import rich.prompt

from gh_nexus.config import settings
from gh_nexus.core.engine import NexusEngine

console = console = rich.console.Console()


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
    
    return 0


async def cmd_start(args) -> int:
    console.print("[bold green]Starting Gh Nexus Engine...[/bold green]")
    
    engine = NexusEngine()
    await engine.initialize()
    
    console.print("[green]Engine initialized successfully![/green]")
    console.print(f"Registered {len(engine.registry.list_all_workers())} workers")
    
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
    
    start_parser = subparsers.add_parser("start", help="Start the nexus engine")
    start_parser.add_argument("-r", "--requirements", help="Initial requirements text")
    
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
        "status": cmd_status,
        "assign": cmd_assign,
        "test": cmd_test,
        "evaluate": cmd_evaluate,
    }
    
    return asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    sys.exit(main())
