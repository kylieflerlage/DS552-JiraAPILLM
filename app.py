from logging import config
import json
import logging
import streamlit as st
import os
import sys
import requests
from config import Config
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
import streamlit as st
from langchain_ollama import ChatOllama
from requests.auth import HTTPBasicAuth

from JiraLLM import get_jira_ticket, create_jira_ticket, update_jira_ticket, get_jira_projects, get_jira_statuses


local_model = ChatOllama(model="qwen3", max_tokens=500)
tools = [get_jira_ticket, create_jira_ticket, update_jira_ticket, get_jira_projects, get_jira_statuses]
chat_with_tools = local_model.bind_tools(tools)

st.sidebar.title("Jira Settings")

base_url = st.sidebar.text_input(
    "Jira Base URL",
    value=""
)
email = st.sidebar.text_input(
    "Jira Email",
    value=""
)
api_token = st.sidebar.text_input(
    "Jira API Token",
    type="password",
    value=""
)

st.session_state["base_url"] = base_url
st.session_state["email"] = email
st.session_state["api_token"] = api_token

def connection_ready():
    return all([
        st.session_state.get("base_url"),
        st.session_state.get("email"),
        st.session_state.get("api_token")
    ])

if st.sidebar.button("Test Jira Connection"):
    try:

        auth = HTTPBasicAuth(
            st.session_state["email"],
            st.session_state["api_token"]
        )

        url = f"{st.session_state['base_url']}/rest/api/3/project"
        r = requests.get(url, auth=auth)
        if r.status_code == 200 and connection_ready():
            st.sidebar.success("Jira connection successful!")

        else:
            st.sidebar.error(f"Failed: {r.status_code} - {r.text}")
    except Exception as e:
        st.sidebar.error(str(e))

if all(k in st.session_state for k in ["base_url", "email", "api_token"]):
    st.session_state["jira_config"] = Config(
        base_url=st.session_state["base_url"],
        email=st.session_state["email"],
        api_token=st.session_state["api_token"]
    )


if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "You are an AI assistant that helps users interact with a Jira ticketing system through natural language. You can create, update, search, retrieve, and summarize Jira tickets using available tools. Your primary role is to translate valid user intent into structured Jira actions using tool calls.\n RULES: Only respond to requests related to tickets and ticket calling. \n - If the input is ambiguous or unrelated, politely guide the user back to Jira related requests.\n - Only perform actions asked by the user.\n - If creating or updating a ticket, confirm details with user before utilizing tool.  \n - If the user asks for a summary of tickets, provide a concise overview of key details like ticket ID, summary, status, and assignee."
        }
    ]

st.title("Jira Chat Assistant")

import streamlit as st



for msg in st.session_state.messages:
    if msg["role"] != "system" and msg["role"] != "tool":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

user_input = st.chat_input("Configure Jira... " if not connection_ready() else "Ask about Jira...", disabled=not connection_ready())

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.write(user_input)
    if not connection_ready():
        with st.chat_message("assistant"):
            st.warning(
                "⚠️ Jira is not configured. Please enter your Base URL, Email, and API Token in the sidebar before using the assistant."
            )
        st.stop()
    
    while True :
        response = chat_with_tools.invoke(st.session_state.messages)

        if not response.tool_calls:
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.content
            })

            with st.chat_message("assistant"):
                st.write(response.content)

            break
        
        if response.content and response.content.strip():
            st.session_state.messages.append({
            "role": "assistant",
            "content": response.content,
            "tool_calls": response.tool_calls
        })

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            
            print(f"Tool call: {tool_name} with args {tool_args}")
            
            if tool_name == "create_jira_ticket":
                result = create_jira_ticket.invoke(tool_args)
                if result.get("status") == "success":
                    result = {"id": result.get("issue_key")}
            elif tool_name == "get_jira_ticket":
                result = get_jira_ticket.invoke(tool_args)
                if result.get("status") == "success":
                    result = {"id": result.get("issue_key")}
            elif tool_name == "update_jira_ticket":
                result = update_jira_ticket.invoke(tool_args)
                if result.get("status") == "success":
                    result = {"id": result.get("issue_key")}
            elif tool_name == "get_jira_projects":
                result = get_jira_projects.invoke("")
            elif tool_name == "get_jira_statuses":
                result = get_jira_statuses.invoke("")
            else:
                result = "Unknown tool"
            if isinstance(result, dict) and "id" in result:
                st.session_state.messages.append({
                "role": "assistant",
                "content": st.session_state["base_url"]+"/browse/"+result.get("key")
                })

            st.session_state.messages.append({
                "role": "tool",
                "name": tool_name,
                "content": str(result),
                "tool_call_id": tool_call_id
            })
        