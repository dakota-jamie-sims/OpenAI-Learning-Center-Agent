#!/usr/bin/env python3
"""
Main entry point for Dakota Learning Center Article Generation
Uses OpenAI Assistants API with parallel execution
"""
import asyncio
import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.pipeline.async_orchestrator import AsyncOrchestrator
from src.config_enhanced import *

console = Console()


@click.group()
def cli():
    """Dakota Learning Center Article Generation System"""
    pass


@cli.command()
@click.argument('topic')
@click.option('--model', default=None, help='Override default model')
@click.option('--no-validation', is_flag=True, help='Skip validation (not recommended)')
@click.option('--debug', is_flag=True, help='Enable debug output')
def generate(topic: str, model: str, no_validation: bool, debug: bool):
    """Generate an article on the specified TOPIC"""
    
    console.print(f"\n[bold blue]Dakota Learning Center Article Generator[/bold blue]")
    console.print(f"[dim]Zero-compromise quality mode enabled[/dim]\n")
    
    # Show configuration
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Topic", topic)
    table.add_row("Min Word Count", str(MIN_WORD_COUNT))
    table.add_row("Min Sources", str(MIN_SOURCES))
    table.add_row("Max Iterations", str(MAX_ITERATIONS))
    table.add_row("Validation", "Disabled" if no_validation else "Enabled")
    
    console.print(table)
    console.print()
    
    # Confirm
    if not click.confirm("Proceed with article generation?"):
        console.print("[yellow]Generation cancelled[/yellow]")
        return
    
    # Run generation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Initializing...", total=None)
        
        async def run():
            orchestrator = AsyncOrchestrator()
            
            progress.update(task, description="Setting up assistants...")
            await orchestrator.initialize_assistants()
            
            progress.update(task, description="Running pipeline...")
            results = await orchestrator.run_pipeline(topic)
            
            return results
        
        results = asyncio.run(run())
    
    # Display results
    console.print()
    if results['status'] == 'SUCCESS':
        console.print("[bold green]✅ Article generated successfully![/bold green]\n")
        
        # Results table
        table = Table(title="Generation Results")
        table.add_column("Output", style="cyan")
        table.add_column("Location", style="yellow")
        
        table.add_row("Article", results['article_path'])
        table.add_row("Quality Report", results['quality_report'])
        table.add_row("Run Directory", results['run_dir'])
        
        if results.get('distribution'):
            for asset, path in results['distribution'].items():
                table.add_row(f"{asset.title()}", path)
        
        console.print(table)
        
        console.print(f"\n[dim]Generation time: {results['elapsed_time']}[/dim]")
        console.print(f"[dim]Iterations required: {results['iterations']}[/dim]")
        
    else:
        console.print(f"[bold red]❌ Generation failed![/bold red]")
        console.print(f"[red]Reason: {results.get('reason', 'Unknown error')}[/red]")
        
        if results.get('issues'):
            console.print("\n[yellow]Issues found:[/yellow]")
            for issue in results['issues']:
                console.print(f"  • {issue}")


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
def validate(directory: str):
    """Validate an existing article"""
    console.print("[yellow]Article validation not yet implemented[/yellow]")


@cli.command()
def config():
    """Show current configuration"""
    table = Table(title="Dakota Learning Center Configuration")
    table.add_column("Category", style="cyan")
    table.add_column("Setting", style="yellow")
    table.add_column("Value", style="green")
    
    # Quality settings
    table.add_row("Quality", "Min Word Count", str(MIN_WORD_COUNT))
    table.add_row("Quality", "Min Sources", str(MIN_SOURCES))
    table.add_row("Quality", "Max Iterations", str(MAX_ITERATIONS))
    table.add_row("Quality", "Min Reading Time", f"{MIN_READING_TIME} minutes")
    
    # Research settings
    table.add_row("Research", "Max Web Calls", str(MAX_WEB_CALLS))
    table.add_row("Research", "Max File Calls", str(MAX_FILE_CALLS))
    
    # Features
    table.add_row("Features", "Evidence Tracking", "✅" if ENABLE_EVIDENCE else "❌")
    table.add_row("Features", "Claim Checking", "✅" if ENABLE_CLAIM_CHECK else "❌")
    table.add_row("Features", "SEO Optimization", "✅" if ENABLE_SEO else "❌")
    table.add_row("Features", "Social Media", "✅" if ENABLE_SOCIAL else "❌")
    
    console.print(table)


@cli.command()
def test():
    """Run a test article generation"""
    test_topic = "The Impact of ESG Investing on Long-Term Portfolio Performance"
    console.print(f"[yellow]Running test generation for: {test_topic}[/yellow]")
    
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(generate, [test_topic, '--debug'])
    
    if result.exit_code == 0:
        console.print("[green]Test completed successfully![/green]")
    else:
        console.print("[red]Test failed![/red]")
        console.print(result.output)


if __name__ == '__main__':
    cli()