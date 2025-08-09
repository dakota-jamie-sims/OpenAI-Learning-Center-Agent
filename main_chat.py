#!/usr/bin/env python3
"""
Main entry point for Dakota Learning Center Article Generation
Using Chat Completions API with Vector Store Integration
"""
import asyncio
import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.pipeline.chat_orchestrator import ChatOrchestrator
from src.config_enhanced import *
from openai import OpenAI
import random
from datetime import datetime

console = Console()


def generate_topic():
    """Generate a relevant topic based on current trends and Dakota's focus areas"""
    
    # Topic categories aligned with Dakota's expertise
    categories = {
        "Market Trends": [
            "impact of rising interest rates on",
            "opportunities in",
            "navigating volatility in",
            "the future of",
            "institutional perspectives on"
        ],
        "Investment Strategies": [
            "optimizing portfolio construction with",
            "risk management through",
            "alpha generation using",
            "the role of",
            "evaluating"
        ],
        "Asset Classes": [
            "private equity",
            "hedge funds",
            "real estate investment trusts",
            "infrastructure investments",
            "alternative investments",
            "ESG investing",
            "factor-based investing",
            "multi-asset strategies",
            "fixed income",
            "emerging markets"
        ],
        "Current Themes": [
            "artificial intelligence in portfolio management",
            "climate risk and investment decisions",
            "demographic shifts and investment implications",
            "central bank policy impacts",
            "geopolitical risk management",
            "digital assets and institutional adoption",
            "inflation hedging strategies",
            "supply chain resilience investments"
        ]
    }
    
    # Try to use AI for smarter topic generation
    try:
        client = OpenAI()
        
        # Get current month/season for relevance
        month = datetime.now().strftime("%B %Y")
        
        prompt = f"""Generate a highly relevant article topic for Dakota's institutional investor audience.
        
Consider:
- Current month: {month}
- Audience: Institutional investors, family offices, RIAs
- Focus: Actionable insights, data-driven analysis
- Areas: Alternative investments, portfolio construction, risk management

Generate ONE specific, timely topic that would be valuable right now.
Format: Just the topic title, no explanation."""

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=50
        )
        
        return response.choices[0].message.content.strip().strip('"')
        
    except:
        # Fallback to random generation
        category = random.choice(list(categories.keys()))
        if category in ["Market Trends", "Investment Strategies"]:
            prefix = random.choice(categories[category])
            asset = random.choice(categories["Asset Classes"])
            theme = random.choice(categories["Current Themes"])
            
            templates = [
                f"The {prefix} {asset} in the Era of {theme}",
                f"{prefix.title()} {asset}: Navigating {theme}",
                f"How {theme} is Reshaping {asset} Strategies"
            ]
            return random.choice(templates)
        else:
            # Simple combination
            asset = random.choice(categories["Asset Classes"])
            theme = random.choice(categories["Current Themes"])
            return f"The Intersection of {asset.title()} and {theme.title()}"


@click.group()
def cli():
    """Dakota Learning Center - Chat Completions API Version"""
    pass


@cli.command()
@click.argument('topic', required=False)
@click.option('--model', default=None, help='Override default model')
@click.option('--debug', is_flag=True, help='Enable debug output')
@click.option('--no-kb', is_flag=True, help='Skip knowledge base search')
@click.option('--words', type=int, default=None, help='Target word count (default: 2000)')
@click.option('--quick', is_flag=True, help='Quick mode: 500-word article, fewer sources')
@click.option('--auto', is_flag=True, help='Auto-generate a trending topic')
def generate(topic: str, model: str, debug: bool, no_kb: bool, words: int, quick: bool, auto: bool):
    """Generate an article on the specified TOPIC using Chat Completions API"""
    
    console.print(Panel.fit(
        "[bold blue]Dakota Learning Center Article Generator[/bold blue]\n"
        "[dim]Chat Completions API with Vector Store Integration[/dim]",
        border_style="blue"
    ))
    
    # Handle topic generation
    if not topic and not auto:
        console.print("[red]Error: Please provide a topic or use --auto flag[/red]")
        console.print("\nExamples:")
        console.print('  python main_chat.py generate "Your topic here"')
        console.print("  python main_chat.py generate --auto")
        console.print("  python main_chat.py generate --auto --quick")
        return
    
    if auto or not topic:
        console.print("\n[yellow]Generating relevant topic...[/yellow]")
        topic = generate_topic()
        console.print(f"[green]Selected topic:[/green] {topic}\n")
    
    # Determine word count and sources
    if quick:
        target_words = 500
        min_sources = 5
        article_type = "Quick Brief"
    elif words:
        target_words = words
        # Scale sources with word count
        min_sources = max(5, min(15, words // 200))  # 5-15 sources
        article_type = "Custom Length"
    else:
        target_words = MIN_WORD_COUNT
        min_sources = MIN_SOURCES
        article_type = "Full Article"
    
    # Show configuration
    table = Table(title="Configuration", show_header=False)
    table.add_column("Setting", style="cyan", width=20)
    table.add_column("Value", style="green")
    
    table.add_row("Topic", topic)
    table.add_row("Article Type", article_type)
    table.add_row("Target Words", f"{target_words:,}")
    table.add_row("Min Sources", str(min_sources))
    table.add_row("Knowledge Base", "Disabled" if no_kb else "Vector Store")
    table.add_row("Max Iterations", str(MAX_ITERATIONS))
    
    console.print(table)
    console.print()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]❌ Error: OPENAI_API_KEY not found in environment[/red]")
        console.print("Please add it to your .env file")
        return
    
    # Check for vector store
    if not no_kb and not os.getenv("VECTOR_STORE_ID"):
        console.print("[yellow]⚠️  Warning: No vector store ID found[/yellow]")
        console.print("Run [cyan]python setup_vector_store.py[/cyan] to initialize")
        if not click.confirm("Continue without knowledge base?"):
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
            # Pass custom parameters to orchestrator
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
        table.add_row("Quality Report", results['quality_report'])
        
        if results.get('proof_path'):
            table.add_row("Evidence Pack", results['proof_path'])
            
        if results.get('distribution'):
            for asset, path in results['distribution'].items():
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
def setup():
    """Initialize vector store for knowledge base"""
    import subprocess
    subprocess.run([sys.executable, "setup_vector_store.py"])


@cli.command()
def benchmark():
    """Compare performance between API modes"""
    console.print("[yellow]Benchmark mode not yet implemented[/yellow]")
    console.print("\nPlanned features:")
    console.print("• Compare Chat Completions vs Assistants API")
    console.print("• Measure token usage and costs")
    console.print("• Test parallel execution performance")


@cli.command()
def config():
    """Show current configuration"""
    table = Table(title="Dakota Learning Center Configuration")
    table.add_column("Category", style="cyan")
    table.add_column("Setting", style="yellow")
    table.add_column("Value", style="green")
    
    # API Configuration
    table.add_row("API", "Mode", "Chat Completions")
    table.add_row("API", "Default Model", DEFAULT_MODELS.get("writer", "gpt-4"))
    table.add_row("API", "Vector Store", "✅" if os.getenv("VECTOR_STORE_ID") else "❌")
    
    # Quality settings
    table.add_row("Quality", "Min Word Count", f"{MIN_WORD_COUNT:,}")
    table.add_row("Quality", "Min Sources", str(MIN_SOURCES))
    table.add_row("Quality", "Max Iterations", str(MAX_ITERATIONS))
    table.add_row("Quality", "Min Reading Time", f"{MIN_READING_TIME} minutes")
    
    # Research settings
    table.add_row("Research", "Max Web Calls", str(MAX_WEB_CALLS))
    table.add_row("Research", "Max KB Searches", str(MAX_FILE_CALLS))
    
    # Features
    table.add_row("Features", "Evidence Tracking", "✅" if ENABLE_EVIDENCE else "❌")
    table.add_row("Features", "Claim Checking", "✅" if ENABLE_CLAIM_CHECK else "❌")
    table.add_row("Features", "SEO Optimization", "✅" if ENABLE_SEO else "❌")
    table.add_row("Features", "Distribution Assets", "✅" if ENABLE_SOCIAL else "❌")
    
    # Token caps
    table.add_row("Tokens", "Synthesis Max", f"{OUTPUT_TOKEN_CAPS['synth_max_tokens']:,}")
    table.add_row("Tokens", "Article Max", "4,000 per section")
    
    console.print(table)


@cli.command()
def topics():
    """Generate topic suggestions"""
    console.print("[bold]Dakota Learning Center - Topic Generator[/bold]\n")
    
    console.print("Generating topic suggestions...\n")
    
    # Generate multiple topics
    topics_list = []
    for i in range(5):
        topic = generate_topic()
        topics_list.append(topic)
        console.print(f"{i+1}. [cyan]{topic}[/cyan]")
    
    console.print("\n[dim]To use a topic:[/dim]")
    console.print('python main_chat.py generate "Topic from above"')
    console.print("\n[dim]Or generate a random topic:[/dim]")
    console.print("python main_chat.py generate --auto")


@cli.command()
def test():
    """Run a test article generation"""
    test_topic = "The Role of Factor Investing in Modern Portfolio Construction"
    
    console.print(f"[yellow]Running test generation[/yellow]")
    console.print(f"Topic: {test_topic}\n")
    
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(generate, [test_topic, '--debug'])
    
    if result.exit_code == 0:
        console.print("[green]✅ Test completed successfully![/green]")
    else:
        console.print("[red]❌ Test failed![/red]")
        if result.exception:
            console.print(f"Exception: {result.exception}")


if __name__ == '__main__':
    cli()