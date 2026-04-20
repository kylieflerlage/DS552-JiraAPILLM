import json
import re
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from langchain_ollama import ChatOllama
from requests.auth import HTTPBasicAuth
import streamlit as st
import requests

from langchain_core.tools import BaseTool

import streamlit as st

jira_token = ''
auth = ''
base_url = ''
def get_runtime():
    runtime = st.session_state.get("jira_config", None)
    if runtime is None:
        raise ValueError("Jira configuration not found in session state. Please set up your Jira connection.")
    jira_token = runtime.api_token
    auth = HTTPBasicAuth(runtime.email, jira_token)
    base_url = runtime.base_url
    return base_url, auth

from langchain.tools import tool
from typing import Optional

def _fetch_jira_from_api(jql: str, fields: str = "*all", expand: str = None) -> str:
    base_url, auth = get_runtime()
    payload = {
          "jql": jql,
          "fields": fields,
          "expand": expand
     }
    response = requests.get(
        base_url + "/rest/api/3/search/jql",
        params=payload,
        auth=auth,
        headers={"Accept": "application/json",
                 "Content-Type": "application/json"}
    )
    print(f"Jira API response status: {response.content}")
    return response.json()

def _post_jira_from_api(summary: str, issuetype: str, project_key: str) -> str:
    base_url, auth = get_runtime()
    payload = {
        "fields": {
            "summary": summary,
            "issuetype": {"name": issuetype},
            "project": {"key": project_key}
        }
    }
    response = requests.post(
        base_url + "/rest/api/3/issue",
        json=payload,
        auth=auth,
        headers={"Accept": "application/json",
                 "Content-Type": "application/json"}
    )
    print(f"Jira API response status: {response.content}")
    return response.json()

def _update_jira_from_api(issue_key: str, summary: Optional[str] = None, description: Optional[str] = None, priority: Optional[str] = None, assignee: Optional[str] = None) -> str:
    base_url, auth = get_runtime()
    payload = {
        "fields": {}
    }
    if summary is not None:
        payload["fields"]["summary"] = summary
    if description is not None:
        payload["fields"]["description"] = description
    if priority is not None:
        payload["fields"]["priority"] = {"name": priority}
    if assignee is not None:
        payload["fields"]["assignee"] = {"name": assignee}

    response = requests.put(
        base_url + "/rest/api/3/issue/" + issue_key,
        json=payload,
        auth=auth,
        headers={"Accept": "application/json",
                 "Content-Type": "application/json"}
    )
    print(f"Jira API response status: {response.status_code}")
    return ("success" if response.status_code == 204 else "failure", response.json())

@tool
def get_jira_ticket(jql: str, fields: str = "summary,status,assignee,priority,description,issuetype,reporter,created", expand: str = None) -> str:
    """
    Search for Jira tickets based on a natural language query.

    Convert the user request into a valid JQL query before calling this tool.
    Unless the user specifies otherwise, return a summary of matching tickets including key details like ticket ID, summary, status, and assignee. If the user asks for specific fields or details, include those in the response.
    
    Statuses: Note, Jira status names should be returned with quotes
    To Do : Issues that are new and have not been started yet (e.g., To Do, Open, Backlog).
    In Progress : Issues being actively worked on or waiting for review (e.g., In Progress, Under Review, In Testing).
    Done : Issues where all work has been completed (e.g., Resolved, Closed, Done).

    Examples:
    - "Show my open bugs" → assignee = currentUser() AND status = "To Do" AND issuetype = 'Bug'
    - "Tickets in project ABC" → project = 'ABC'
    - "High priority issues" → priority = 'High'
    - For fields, provide a comma delimmited list of fields to return or *all to return all fields. Ex: "Show my open bugs with details" → jql = assignee = currentUser() AND status = 'ToDo' AND issuetype = 'Bug', fields = '*all'
    - To see ticket history, append "?expand=changelog" to the end of the query. Ex: "Show me the history of ticket ABC-123" → jql = 'ABC-123', expand = 'changelog'
    """
    return _fetch_jira_from_api(jql,fields,expand)

@tool
def create_jira_ticket(summary: str,  issuetype: str, project_key: str) -> str:
    """
    Create a new Jira ticket based on a natural language query.
    Convert the user request into the required parameters before calling this tool.

    Field rules:
    - summary: short and clear
    - description: detailed explanation
    - priority: one of [Low, Medium, High]
    - assignee: username or account ID

    Examples:
    - "Create a bug in project ABC with summary 'Login issue' and description 'Users cannot log in after update'"
      → summary: "Login issue",, issuetype: "Bug", project_key: "ABC"
    - "I need a new task for the frontend team about updating the homepage"
        → No tool call, respond with "what should the project key be?" and wait for user to respond with project key before calling tool with summary: "Updating homepage", issuetype: "Task", project_key: user_response
    
    """
    return _post_jira_from_api(summary, issuetype, project_key)

@tool
def update_jira_ticket( issue_key: str, summary: Optional[str] = None, description: Optional[str] = None, priority: Optional[str] = None, assignee: Optional[str] = None) -> str:
    """
    Update an existing Jira ticket based on a natural language query.
    Convert the user request into the required parameters before calling this tool.

    You MUST:
    - Provide a valid issue_key (e.g., ABC-123)
        - It is the project code and id number of the ticket, separated by a hyphen
    - Only include fields explicitly mentioned in the user request
    Field rules:
    - summary: short and clear
    - description: detailed explanation
    - priority: one of [Low, Medium, High]
    - assignee: username or account ID
    Examples:
    - "Update ABC-123 summary to fix login bug"
      → issue_key: "ABC-123", summary: "Fix login bug"
    - "Set priority of ABC-123 to High"
      → issue_key: "ABC-123", priority: "High"
    """
    return _update_jira_from_api(issue_key, summary, description, priority, assignee)

@tool
def get_jira_projects(search: str = None) -> str:
    """
    Retrieve a list of Jira projects to help users identify valid project keys for ticket creation.

    This tool can be called when the user wants to create a ticket but does not know the project key. It can also be used to provide additional context about available projects in the system.

    Example usage:
    - User: "I want to create a new bug but I'm not sure which project it belongs to."
    - Assistant: "I can help with that! Here are some of the projects in our Jira system: [list of project names and keys]. Which project should I use for this ticket?"
    """
    base_url, auth = get_runtime()
    return requests.get(auth = auth,
                        url = f"{base_url}/rest/api/3/project/search")

@tool
def get_jira_statuses(search: str = None) -> str:
    """
    Retrieve a list of Jira statuses to help users identify valid status values for ticket updates.

    This tool can be called when the user wants to update a ticket but does not know the valid status values. It can also be used to provide additional context about available statuses in the system.

    Example usage:
    - *No available tickerts under the user's current query*
    - Assistant: "I couldn't find any tickets matching your query. Should I show you the available statuses in our Jira system to help refine your search?"
    - User: "Yes, show me the statuses."
    - Assistant: "Here are the statuses in our Jira system: [list of status names and categories]. Which status should I use for your search?"
    """
    base_url, auth = get_runtime()
    return requests.get(auth = auth,
                        url = f"{base_url}/rest/api/3/status")

