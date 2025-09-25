"""
This module contains the tools that the agent can use to perform various QA-related actions.
"""

import json
from langchain_core.tools import tool
from atlassian import Jira
from github import Github
import os

@tool
def create_test_suite(user_story: str, historical_context: str) -> str:
    """
    Generates a comprehensive test suite in JSON format based on a user story and historical context.
    This tool should be used to create the initial set of tests.
    """
    # In a real implementation, this would call the LLM with the TEST_GENERATION_PROMPT.
    # For this example, we'll return a mock response to simulate the generation.
    print(f"--- Generating test suite for: {user_story} ---")
    mock_suite = {
        "test_suite": [
            {
                "id": "TC-001",
                "category": "Positive",
                "title": "Premium user can export dashboard to PDF",
                "steps": [
                    "Log in as a premium user",
                    "Navigate to the dashboard",
                    "Click the 'Export to PDF' button"
                ],
                "expected_result": "A PDF file of the dashboard is successfully downloaded."
            },
            {
                "id": "TC-002",
                "category": "Negative",
                "title": "Verify non-premium user cannot export PDF",
                "steps": [
                    "Log in as a standard (non-premium) user.",
                    "Navigate to the dashboard."
                ],
                "expected_result": "The 'Export to PDF' button is not visible or is disabled."
            }
        ]
    }
    return json.dumps(mock_suite, indent=2)

@tool
def execute_playwright_test(test_case_json: str) -> str:
    """
    Executes a single test case using Playwright.
    The input must be a JSON string representing a single test case.
    Returns 'PASS' or a detailed 'FAIL' message.
    """
    # This is a placeholder. In a real system, this would invoke a Playwright runner.
    try:
        test_case = json.loads(test_case_json)
        print(f"--- Executing test: {test_case['id']} - {test_case['title']} ---")
        # Simulate a test failure for demonstration purposes
        if "non-premium" in test_case["title"]:
            raise Exception("Test Failed: 'Export to PDF' button was visible for non-premium user.")
        return "PASS"
    except Exception as e:
        return f"FAIL: {str(e)}"

@tool
def create_jira_ticket(project_key: str, summary: str, description: str, issue_type: str = "Bug") -> str:
    """
    Creates a bug report in Jira.
    """
    print(f"--- Creating Jira Ticket in project {project_key} ---")
    print(f"Summary: {summary}")
    
    try:
        jira = Jira(
            url=os.environ.get('JIRA_URL'),
            username=os.environ.get('JIRA_USERNAME'),
            password=os.environ.get('JIRA_PASSWORD')
        )
        
        jira.issue_create(
            fields={
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }
        )
        return f"Successfully created Jira ticket in project {project_key}."
    except Exception as e:
        return f"Failed to create Jira ticket. Error: {str(e)}"
