import sys, asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize GPT-5 compatibility FIRST
import init_gpt5

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