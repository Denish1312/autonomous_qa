"""
This module defines the stateful, multi-step workflow using LangGraph.
It orchestrates the autonomous QA process from test generation to bug reporting.
"""

import json
import os
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from .tools import create_test_suite, execute_playwright_test, create_jira_ticket

# Define the state for our graph
class AgentState(TypedDict):
    user_story: str
    messages: List
    test_suite: List[dict]
    test_results: dict
    bugs_to_report: List[dict]

class AutonomousQAAgent:
    def __init__(self):
        """Initialize the agent with necessary components and build the workflow graph."""
        self.llm = ChatOpenAI(model="gpt-4")  # Fixed typo in model name
        self.tools = [create_test_suite, execute_playwright_test, create_jira_ticket]
        self.model_with_tools = self.llm.bind_tools(self.tools)
        self.qdrant = Qdrant.from_existing_collection(
            embedding=OpenAIEmbeddings(),
            collection_name="historical_defects",
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        )
        self.retriever = self.qdrant.as_retriever()
        self.graph = self.build_graph()

    def build_graph(self):
        """Build the workflow graph defining the agent's behavior."""
        workflow = StateGraph(AgentState)

        workflow.add_node("retrieve_context", self.retrieve_context)
        workflow.add_node("generate_tests", self.generate_tests)
        workflow.add_node("execute_tests", self.execute_tests)
        workflow.add_node("report_bugs", self.report_bugs)

        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "generate_tests")
        workflow.add_edge("generate_tests", "execute_tests")
        workflow.add_edge("execute_tests", "report_bugs")
        workflow.add_edge("report_bugs", END)
        
        return workflow.compile()

    def retrieve_context(self, state: AgentState):
        """Retrieve relevant historical context for the user story."""
        print("--- RETRIEVING HISTORICAL CONTEXT ---")
        user_story = state["user_story"]
        retrieved_docs = self.retriever.invoke(user_story)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        messages = [
            SystemMessage(content="You are an expert QA engineer. Generate a comprehensive test suite based on the user story and historical context."),
            HumanMessage(content=f"User Story:\n{user_story}\n\nHistorical Context:\n{context}")
        ]
        return {"messages": messages}

    def generate_tests(self, state: AgentState):
        """Generate test cases based on the user story and historical context."""
        print("--- GENERATING TEST SUITE ---")
        response = self.model_with_tools.invoke(state["messages"])
        test_suite_json = response.tool_calls[0].args['test_suite']
        test_suite = json.loads(test_suite_json)['test_suite']
        return {"test_suite": test_suite}

    def execute_tests(self, state: AgentState):
        """Execute the generated test cases and identify failures."""
        print("--- EXECUTING TESTS ---")
        test_suite = state["test_suite"]
        results = {}
        bugs = []
        
        for test in test_suite:
            result = execute_playwright_test.invoke(json.dumps(test))
            results[test['id']] = result
            if "FAIL" in result:
                bugs.append({"test": test, "reason": result})
        
        return {"test_results": results, "bugs_to_report": bugs}

    def report_bugs(self, state: AgentState):
        """Report any test failures as bugs in Jira."""
        print("--- REPORTING BUGS ---")
        bugs = state["bugs_to_report"]
        for bug in bugs:
            summary = f"Test Failure: {bug['test']['id']} - {bug['test']['title']}"
            description = f"Test failed with reason: {bug['reason']}\n\nSteps to Reproduce:\n"
            for i, step in enumerate(bug['test']['steps']):
                description += f"{i+1}. {step}\n"
            description += f"\nExpected Result: {bug['test']['expected_result']}"
            
            create_jira_ticket.invoke({
                "project_key": os.getenv("JIRA_PROJECT_KEY", "QA"),
                "summary": summary,
                "description": description
            })
        return {}
