#!/usr/bin/env python3
"""
Main entry point for Dakota Learning Center Article Generation
Uses OpenAI Chat Completions API with parallel execution
"""
import asyncio
import click
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.pipeline.chat_orchestrator import ChatOrchestrator
from src.config import settings

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
@click.option('--words', type=int, default=None, help='Target word count (default: 2000)')
@click.option('--quick', is_flag=True, help='Quick mode: 500-word article, fewer sources')
def generate(topic: str, model: str, no_validation: bool, debug: bool, words: int, quick: bool):
    """Generate an article on the specified TOPIC"""
    
    console.print(Panel.fit(
        "[bold blue]Dakota Learning Center Article Generator[/bold blue]\n"
        "[dim]Chat Completions API Version[/dim]",
        border_style="blue"
    ))
    
    # Determine word count and sources
    if quick:
        target_words = 500
        min_sources = 5
        article_type = "Quick Brief"
    elif words:
        target_words = words
        min_sources = max(5, min(15, words // 200))
        article_type = "Custom Length"
    else:
        target_words = settings.MIN_WORD_COUNT
        min_sources = settings.MIN_SOURCES
        article_type = "Full Article"
    
    # Show configuration
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Topic", topic)
    table.add_row("Article Type", article_type)
    table.add_row("Target Words", f"{target_words:,}")
    table.add_row("Min Sources", str(min_sources))
    table.add_row("Max Iterations", str(settings.MAX_ITERATIONS))
    table.add_row("API Mode", "Chat Completions")
    
    console.print(table)
    console.print()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]❌ Error: OPENAI_API_KEY not found in environment[/red]")
        console.print("Please add it to your .env file")
        return
    
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
            orchestrator = ChatOrchestrator()
            
            progress.update(task, description="Setting up agents...")
            await orchestrator.initialize_agents()
            
            progress.update(task, description="Running pipeline...")
            results = await orchestrator.run_pipeline(
                topic,
                min_words=target_words,
                min_sources=min_sources
            )
            
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
        table.add_row("Metadata", results.get('metadata_path', 'metadata.md'))
        
        if results.get('summary_path'):
            table.add_row("Summary", results['summary_path'])
        
        if results.get('social_path'):
            table.add_row("Social Media", results['social_path'])
            
        if results.get('distribution'):
            for asset, path in results['distribution'].items():
                if asset not in ['summary_writer', 'social_promoter']:
                    table.add_row(f"{asset.replace('_', ' ').title()}", path)
        
        table.add_row("Run Directory", results['run_dir'])
        
        console.print(table)
        
        # Token usage
        console.print(f"\n[bold]Token Usage:[/bold]")
        console.print(f"Total tokens: [green]{results.get('total_tokens', 0):,}[/green]")
        console.print(f"Generation time: [green]{results['elapsed_time']}[/green]")
        console.print(f"Iterations required: [green]{results['iterations']}[/green]")
        
        # Show token breakdown
        if debug and results.get('token_usage'):
            console.print("\n[dim]Token breakdown by agent:[/dim]")
            for agent, usage in results['token_usage'].items():
                console.print(f"  {agent}: {usage.get('total_tokens', 0):,} tokens")
        
    else:
        console.print(f"[bold red]❌ Generation failed![/bold red]")
        console.print(f"[red]Reason: {results.get('reason', 'Unknown error')}[/red]")
        
        if results.get('error'):
            console.print(f"\n[red]Error: {results['error']}[/red]")
            
        if results.get('issues'):
            console.print("\n[yellow]Issues found:[/yellow]")
            for issue in results['issues']:
                console.print(f"  • {issue}")
                
        if debug and results.get('traceback'):
            console.print("\n[dim]Traceback:[/dim]")
            console.print(results['traceback'])


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
    table.add_row("Quality", "Min Word Count", str(settings.MIN_WORD_COUNT))
    table.add_row("Quality", "Min Sources", str(settings.MIN_SOURCES))
    table.add_row("Quality", "Max Iterations", str(settings.MAX_ITERATIONS))
    table.add_row("Quality", "Min Reading Time", f"{MIN_READING_TIME} minutes")
    
    # Research settings
    table.add_row("Research", "Max Web Calls", str(settings.MAX_WEB_CALLS))
    table.add_row("Research", "Max File Calls", str(settings.MAX_FILE_CALLS))
    
    # Features
    table.add_row("Features", "Evidence Tracking", "✅" if settings.ENABLE_EVIDENCE else "❌")
    table.add_row("Features", "Claim Checking", "✅" if settings.ENABLE_CLAIM_CHECK else "❌")
    table.add_row("Features", "SEO Optimization", "✅" if settings.ENABLE_SEO else "❌")
    table.add_row("Features", "Social Media", "✅" if settings.ENABLE_SOCIAL else "❌")
    
    console.print(table)


@cli.command()
def test():
    """Run a test article generation"""
    test_topic = "The Role of Factor Investing in Modern Portfolio Construction"
    
    console.print(f"[yellow]Running test generation[/yellow]")
    console.print(f"Topic: {test_topic}\n")
    
    from click.testing import CliRunner
    runner = CliRunner()
    # Use quick mode for faster testing
    result = runner.invoke(generate, [test_topic, '--quick'], input='y\n')
    
    if result.exit_code == 0:
        console.print("[green]✅ Test completed successfully![/green]")
    else:
        console.print("[red]❌ Test failed![/red]")
        if result.exception:
            console.print(f"Exception: {result.exception}")


if __name__ == '__main__':
    cli()