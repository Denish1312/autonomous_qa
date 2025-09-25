"""
Main application entrypoint for the Autonomous QA Agent API.

This module provides a FastAPI application that exposes the agent's functionality
through HTTP endpoints. It handles both the QA workflow execution and data ingestion
for the RAG system.
"""

from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .agent.graph import AutonomousQAAgent
from .rag.ingestion import ingest_data
from .review.api import router as review_router

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Autonomous QA Agent API",
    description="An API to trigger the AI-driven QA workflow.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include the review system router
app.include_router(review_router)

# Initialize the QA agent
agent = AutonomousQAAgent()

class TestRequest(BaseModel):
    """
    Request model for the QA workflow endpoint.
    
    Attributes:
        user_story (str): The user story or requirement to generate and execute tests for.
    """
    user_story: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_story": "As a premium user, I want to export my dashboard as a PDF."
            }
        }

class WorkflowResponse(BaseModel):
    """
    Response model for the QA workflow endpoint.
    
    Attributes:
        message (str): Status message about the workflow execution.
        test_results (dict): Results of the test execution.
    """
    message: str
    test_results: Dict[str, Any]

class IngestionResponse(BaseModel):
    """
    Response model for the data ingestion endpoint.
    
    Attributes:
        message (str): Status message about the ingestion process.
    """
    message: str

@app.post("/run-qa-workflow", response_model=WorkflowResponse)
async def run_qa_workflow(request: TestRequest) -> WorkflowResponse:
    """
    Triggers the full QA workflow for a given user story.
    
    This endpoint:
    1. Takes a user story as input
    2. Generates test cases using the RAG system and LLM
    3. Executes the tests using Playwright
    4. Reports any failures to Jira
    
    Args:
        request (TestRequest): The request containing the user story.
        
    Returns:
        WorkflowResponse: The workflow execution results.
        
    Raises:
        HTTPException: If the workflow execution fails.
    """
    try:
        inputs = {"user_story": request.user_story}
        result = agent.graph.invoke(inputs)
        
        return WorkflowResponse(
            message="QA workflow completed successfully.",
            test_results=result.get("test_results", {})
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"QA workflow failed: {str(e)}"
        )

@app.post("/ingest-data", response_model=IngestionResponse)
async def run_ingestion() -> IngestionResponse:
    """
    Triggers the data ingestion process for the RAG system.
    
    This endpoint:
    1. Loads historical defect data from the data directory
    2. Processes and splits the documents
    3. Embeds the chunks using OpenAI
    4. Stores the embeddings in Qdrant
    
    Returns:
        IngestionResponse: The ingestion status message.
        
    Raises:
        HTTPException: If the ingestion process fails.
    """
    try:
        ingest_data()
        return IngestionResponse(message="Data ingestion completed successfully.")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Data ingestion failed: {str(e)}"
        )

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Simple health check endpoint to verify the API is running.
    
    Returns:
        dict: A status message indicating the API is healthy.
    """
    return {"status": "healthy"}
