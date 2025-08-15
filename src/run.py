import sys, asyncio, logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize GPT-5 compatibility FIRST
try:
    import init_gpt5  # noqa: F401 - imported for side effects
except Exception as exc:  # pragma: no cover - defensive
    logger.error("GPT-5 setup failed: %s", exc)

# Now import the pipeline
from src.pipeline.orchestrator import Pipeline

def main():
    if len(sys.argv) < 2:
        print('Usage: python run.py "<topic>"')
        raise SystemExit(1)
    topic = sys.argv[1]
    pipe = Pipeline(topic)
    result = asyncio.run(pipe.run_all())
    print("\n=== DONE ===")
    for k, v in result.items():
        if isinstance(v, dict):
            print(f"{k}: {v.get('decision', '')}")
        else:
            print(f"{k}: {v}")

if __name__ == "__main__":
    main()