# DS552-JiraAPILLM
# Jira LLM Assistant (Local)

## Overview

This application integrates a Large Language Model (LLM) with the Jira API to enable natural language interaction with your Jira workspace. Users can query, summarize, and reason over Jira issues using conversational prompts.

The app is designed to run **locally** and leverages:

* **Ollama** for local LLM hosting
* **LangChain (ChatOllama)** for model interaction
* Jira API for data retrieval and operations

---

## Features

* Query Jira tickets using natural language
* Summarize issues, statuses, and priorities
* Perform reasoning tasks (e.g., identifying risks, prioritization)
* Local-first: no external LLM APIs required

---

## Requirements

Before running the app, ensure you have:

* Python 3.9+
* Ollama installed
* A pulled Ollama model (e.g., `qwen3`,`llama3`, `mistral`, etc.)
* Jira API access (API token + base URL)

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Install and Run Ollama

Download and install Ollama from: https://ollama.com


### 3. Pull a Model

Pull the model you want to use locally:

```bash
ollama pull qwen3
```

> You can replace `qwen3` with any supported model, note this will have to be changed in app.py.


### 4. Run the Application
```bash
streamlit run app.py
```
---

### 5. Configure Environment Variables
Access the side bar to add and test connection before conversation.

---

## Usage

* Enter a natural language query (e.g., “Show my open tickets from last week”)
* The app retrieves Jira data and uses the LLM to generate a response
* Responses may include summaries, insights, or suggested actions

---

## Notes

* This app is intended for **local use only**
* Ensure your Jira credentials are kept secure
* Model performance depends on the selected Ollama model and hardware constraints

