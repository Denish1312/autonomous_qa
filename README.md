# Autonomous QA System

An AI-powered QA automation system that combines LLMs, RAG, and automated testing to create a fully autonomous testing workflow.

## System Architecture

The system consists of three main components:

1. **Cognitive Core (Test Generation)**
   - LLM-powered test case generation
   - Historical context integration via RAG
   - Comprehensive test suite creation

2. **Intelligence & Autonomy (RAG Pipeline)**
   - Qdrant vector database for knowledge storage
   - Semantic search for relevant test context
   - OpenAI embeddings for document processing

3. **CI/CD Integration**
   - GitHub Actions workflow automation
   - Playwright test execution
   - Jira integration for bug reporting

## Prerequisites

- Python 3.11+
- Docker (for Qdrant)
- OpenAI API Key
- Jira credentials (for bug reporting)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd autonomous_qa
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Install Playwright browsers:
```bash
playwright install --with-deps chromium
```

## Configuration

1. Start Qdrant:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

2. Create a `.env` file:
```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Qdrant Configuration
QDRANT_URL=http://localhost:6333

# Jira Configuration
JIRA_URL=your_jira_url_here
JIRA_USERNAME=your_username
JIRA_PASSWORD=your_password
JIRA_PROJECT_KEY=your_project_key
```

## Running the System

1. Start the FastAPI server:
```bash
uvicorn src.main:app --reload
```

2. Ingest historical data (via API):
```bash
curl -X POST http://localhost:8000/ingest-data
```

3. Run QA workflow (via API):
```bash
curl -X POST http://localhost:8000/run-qa-workflow \
  -H "Content-Type: application/json" \
  -d '{"user_story": "As a premium user, I want to export my dashboard as a PDF."}'
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

1. **POST /run-qa-workflow**
   - Triggers the full QA workflow
   - Input: User story
   - Output: Test results and status

2. **POST /ingest-data**
   - Triggers RAG data ingestion
   - Output: Ingestion status

3. **GET /health**
   - Health check endpoint
   - Output: API status

## CI/CD Integration

The system automatically runs on pull requests to the main branch:

1. Sets up test environment
2. Starts Qdrant service
3. Ingests test data
4. Runs QA workflow on sample user stories
5. Reports results and uploads artifacts

## Project Structure

```
autonomous_qa/
├── src/
│   ├── agent/
│   │   ├── prompts.py    # LLM prompts
│   │   ├── tools.py      # Agent tools
│   │   └── graph.py      # Workflow graph
│   ├── rag/
│   │   └── ingestion.py  # RAG pipeline
│   └── main.py           # FastAPI app
├── tests/
├── .github/
│   └── workflows/
│       └── playwright.yml # CI/CD config
└── requirements.txt
```

## Development

1. **Adding New Test Types**
   - Extend `tools.py` with new test functions
   - Update the agent's workflow in `graph.py`

2. **Customizing Test Generation**
   - Modify prompts in `prompts.py`
   - Adjust the RAG pipeline in `ingestion.py`

3. **Extending the API**
   - Add new endpoints in `main.py`
   - Update the workflow graph as needed

## Troubleshooting

1. **Qdrant Connection Issues**
   - Verify Docker container is running
   - Check QDRANT_URL in .env
   - Ensure port 6333 is available

2. **OpenAI API Issues**
   - Verify API key in .env
   - Check API rate limits
   - Monitor usage quotas

3. **Playwright Test Failures**
   - Check browser installation
   - Verify test environment setup
   - Review test artifacts in CI/CD

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License
