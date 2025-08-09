"""
Create a Vector Store and upload files for OpenAI File Search.
Usage:
    python -m src.tools.fs_setup --glob "knowledge_base/sample/*.md"
"""
import argparse, glob as _glob
from openai import OpenAI
from dotenv import load_dotenv

def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--glob", required=True, help="File glob to upload, e.g. 'knowledge_base/sample/*.md'")
    parser.add_argument("--name", default="DakotaLearningCenterKB", help="Vector store name")
    args = parser.parse_args()

    files = _glob.glob(args.glob)
    if not files:
        print("No files matched.")
        return

    client = OpenAI()
    print("Creating vector store:", args.name)
    vs = client.vector_stores.create(name=args.name)
    print("Vector store id:", vs.id)

    streams = [open(p, "rb") for p in files]
    try:
        try:
            batch = client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vs.id,
                files=streams,
            )
        except AttributeError:
            # Backward compatibility with older SDK where vector_stores lived under beta
            batch = client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vs.id,
                files=streams,
            )
        print("Status:", batch.status, "Counts:", batch.file_counts)
    finally:
        for s in streams:
            s.close()

    print("\n✅ Done. Set VECTOR_STORE_ID in your .env to:")
    print("VECTOR_STORE_ID=", vs.id)

if __name__ == "__main__":
    main()
