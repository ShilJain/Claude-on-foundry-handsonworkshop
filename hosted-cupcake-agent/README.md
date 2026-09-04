# Cupcake Store Hosted Agent

This folder packages Sparkles as a Microsoft Foundry hosted agent using the Responses protocol. It uses Claude on Microsoft Foundry and connects to the Cupcake Store and Foundry IQ knowledge-base MCP endpoints.

## Configure locally

1. Copy `src/cupcake-agent/.env.template` to `src/cupcake-agent/.env`.
2. Populate the five required values without committing the file.
3. Create and activate a virtual environment inside `src/cupcake-agent`.
4. Run `azd ai agent run --no-client` from this project folder.
5. In another terminal, run `azd ai agent invoke cupcake-agent --local "hello, are you up?"`.

The VS Code launch configuration starts `main.py` directly with `debugpy`. The current `agent-dev-cli` beta is not included because it requires Agent Framework Core earlier than 1.3, while this hosted agent uses the current 1.14 API.

## Publish

This project follows the current `agent-framework/responses/01-basic` Foundry sample: the complete hosted-agent definition is in `azure.yaml`, direct code deployment uses Python 3.13, and the agent exposes Responses protocol 2.0.0.

Set the five required runtime settings in the active azd environment, then deploy from this folder:

```powershell
$env:AZURE_DEV_USER_AGENT = 'microsoft_foundry_skill'
azd deploy cupcake-agent --no-prompt
azd ai agent show --output json
azd ai agent invoke cupcake-agent "hello, are you up?"
```

The `.agentignore` file prevents local secrets and development files from entering the deployment package. Actual secret values belong in the ignored azd environment or a Foundry connection, never in `azure.yaml`.