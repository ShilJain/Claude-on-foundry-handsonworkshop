# Claude on Microsoft Foundry — Agent Framework sample

A simple [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) agent that chats with an Anthropic **Claude** model deployed on **Microsoft Foundry**.

## Prerequisites

- Python 3.10+
- A Claude model deployment in a Microsoft Foundry project

## Setup

1. Create and activate a virtual environment, then install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copy `.env.template` to `.env` and fill in your Foundry Claude deployment values:

   | Variable | Description |
   |----------|-------------|
   | `FOUNDRY_MODEL_DEPLOYMENT` | The Claude model deployment name |
   | `FOUNDRY_API_KEY` | API key for the Foundry endpoint |
   | `FOUNDRY_ENDPOINT` | Base URL of the Foundry endpoint |

## Run

```powershell
python agent.py
```

Type your messages at the prompt; enter `exit` or `quit` to stop.

You can also press **F5** in VS Code to run/debug the agent.
