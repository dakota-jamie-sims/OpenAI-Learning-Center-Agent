# Vector Store Upload Guide

## Files Ready for Upload

You have **406 total files** ready to upload to the OpenAI vector store:

- **404 Learning Center articles** in `knowledge_base_markdown/learning_center/`
- **2 Dakota Way files** in `knowledge_base_markdown/dakota_way/`

## Upload Instructions

1. **Go to OpenAI Platform**
   - Visit: https://platform.openai.com/storage/vector_stores
   - Sign in with your OpenAI account

2. **Create New Vector Store**
   - Click "Create vector store"
   - Name it: "Dakota Knowledge Base"
   - Description: "Dakota Learning Center articles and Dakota Way content"

3. **Upload Files**
   - Click "Add files"
   - Navigate to `/Users/jamiesims/Desktop/learning-center-agent-open-ai/knowledge_base_markdown/`
   - Select all files in the `learning_center` folder (404 files)
   - Then select all files in the `dakota_way` folder (2 files)
   - Click "Upload"

4. **Wait for Processing**
   - OpenAI will process the files (this may take several minutes)
   - You'll see the status change from "processing" to "completed"

5. **Copy Vector Store ID**
   - Once completed, copy the vector store ID (format: `vs_xxxxxxxxxxxxx`)
   - You'll need this ID to update your configuration

## Update Your Configuration

After uploading, update the vector store ID in your environment:

```bash
# In your .env file or environment variables:
OPENAI_VECTOR_STORE_ID=vs_xxxxxxxxxxxxx  # Replace with your actual ID
```

## File Format Benefits

Your Markdown files are optimized for vector search:
- Clean, structured format without HTML
- Proper headings and sections
- Metadata preserved at the top of each file
- No duplicate content or redundant files

## Verify Upload

After uploading, you can verify by:
1. Checking the file count shows 406 files
2. Testing a search query through the API
3. Running the system with the new vector store ID

## Troubleshooting

If you encounter issues:
- Ensure all files are .md format
- Check file sizes aren't exceeding limits
- Verify your API key has proper permissions
- Make sure the vector store status is "completed" before use