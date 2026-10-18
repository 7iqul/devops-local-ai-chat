# DevOps Field Guide

DevOps Field Guide is a small, English-language learning website about DevOps. A floating chat assistant in the lower-right corner answers questions about the guide. The chat runs against local Ollama models; it does not require a hosted AI API or API key. Basic arithmetic is handled by a safe local calculator.

## Project goals

- Explain DevOps concepts in a clear, student-friendly way.
- Keep the assistant available as a chat widget on every section of the site.
- Run the web app and Ollama with Docker Compose.
- Support two selectable local models: Qwen 2.5 3B and Llama 3.2 3B.
- Prepare the site and models before a presentation so the demo can run without internet.
- Configure the same local models in VS Code through Continue.

## What the site covers

- DevOps as a collaborative way of working, rather than one product or job title.
- Shared ownership, automation, continuous feedback, and learning.
- Source control with Git and GitHub.
- Containers with Docker.
- Continuous Integration and Continuous Delivery (CI/CD).
- Infrastructure as Code.
- A delivery loop: plan and code, build and test, release and deploy, then operate and learn.

The chat assistant receives this site-specific reference in its system prompt. It is designed to explain or compare these concepts and politely redirect questions outside the guide. It does not inspect live infrastructure or claim to perform real deployments.

## Architecture

```text
Browser
  ├── DevOps Field Guide and floating chat widget (:8000)
  │      └── Python HTTP app → local arithmetic calculator
  └── VS Code + Continue (optional)
          └── Ollama API published on host :11435
                 ├── qwen2.5:3b
                 └── llama3.2:3b

Docker Compose runs the web app and Ollama and stores model files in a named volume. Inside Docker's Compose network, the app reaches Ollama at `http://ollama:11434`. The container publishes its API on host port `11435` so it can coexist with a native Ollama installation that uses port `11434`.
```

| File | Purpose |
|---|---|
| `index.html` | Responsive English DevOps guide and lower-right chat widget |
| `app.py` | Local HTTP API, guide-specific model prompt, model list, safe arithmetic evaluator |
| `Dockerfile` | Minimal Python image for the website/API |
| `docker-compose.yml` | Website and Ollama services with persistent model storage |
| `prepare.ps1` | Starts Compose, waits for Ollama, and downloads missing models |
| `.continue/config.yaml` | Local Qwen and Llama models for Continue in VS Code |
| `.vscode/extensions.json` | Recommends the Continue extension when the project is opened |

## Requirements

- Windows 10/11 with Docker Desktop, or Linux/macOS with Docker Engine and the Docker Compose plugin.
- 8 GB RAM minimum in practice; 16 GB is recommended for smoother model inference.
- About 6 GB or more of free disk space for the application image and both model files.
- Internet access for the first Docker image and model downloads only.
- VS Code and the Continue extension are optional.

## First-time setup

On Windows, start Docker Desktop and wait for its engine to report **Running**. Open PowerShell in this project directory and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\prepare.ps1
```

The script builds the website image, starts both services, and pulls any missing Ollama models into the persistent `ollama_data` volume. The first setup requires internet and downloads several gigabytes. Leave the process running until the script reports success.

Open [http://localhost:8000](http://localhost:8000). Use the floating chat button in the lower-right corner. Try the quick prompts, ask a DevOps question, switch between Qwen and Llama, or ask `What is 125 times 24?` to see the deterministic local calculator.

Useful commands:

```powershell
docker compose ps
docker compose exec ollama ollama list
docker compose logs -f app
docker compose logs -f ollama
docker compose down
```

`docker compose down` preserves model files. Avoid `docker compose down -v` unless you intend to remove the Ollama volume and its downloaded models.

## Prepare and demonstrate offline

Complete the first-time setup while online. Confirm `docker compose exec ollama ollama list` shows both models, and ask the chat widget one question with each model. Then turn off Wi-Fi and repeat the questions. The website, Python API, model inference, and calculator use local services; the GitHub repository does not contain model weights.

Keep Docker Desktop running during the presentation. Start the already-prepared project with:

```powershell
docker compose up -d
```

Open `http://localhost:8000`. Both the Docker image and models must have been prepared on that computer before internet access is removed. If presenting on another computer, prepare or transfer the image and model data there in advance.

## Use the local models in VS Code

1. Install the **Continue** extension from the VS Code Marketplace while online.
2. Open this project folder in VS Code.
3. Start the Compose stack and wait for setup to finish.
4. Open Continue and select `Qwen 2.5 3B (Local)` or `Llama 3.2 3B (Local)`.
5. Keep the Compose Ollama service running. Continue connects to `http://localhost:11435`.

The project config is in `.continue/config.yaml`. Continue also supports a user-level config at `%USERPROFILE%\.continue\config.yaml`; copy the project config there if the installed Continue version does not pick up the workspace config. Inference uses the local Ollama container. Marketplace installation itself requires internet.

## Presentation walkthrough

1. Introduce the site as a short guide to DevOps and its delivery workflow.
2. Explain collaboration, automation, and learning from the **Principles** section.
3. Point out Git/GitHub, Docker, CI/CD, and Infrastructure as Code in **The Toolkit**.
4. Open the lower-right assistant and ask: `What is DevOps?`, `How is CI different from CD?`, or `Why use Docker?`
5. Switch models and ask the same question to compare local responses.
6. Ask `What is 125 times 24?` and explain that arithmetic is evaluated by the local calculator.
7. If required, disconnect the internet and repeat a question after confirming the stack and both models were prepared beforehand.

## Troubleshooting

- **The website does not open:** run `docker compose ps`, then inspect `docker compose logs -f app`.
- **Ollama is not ready:** check `docker compose logs -f ollama` and give it a moment to start.
- **A model is missing:** while online, run `docker compose exec ollama ollama pull qwen2.5:3b` or `docker compose exec ollama ollama pull llama3.2:3b`.
- **The chat reports that Ollama is unavailable:** confirm the Ollama service is running and the selected model appears in `ollama list`.
- **Responses are slow:** 3B models still need system memory. Close other applications and wait for the first model load to finish.
- **Continue cannot connect:** check that the Compose stack is running, open `http://localhost:11435/api/tags`, and confirm that the model tags in `.continue/config.yaml` match the downloaded models.

## GitHub

Create a repository, then set its URL and push the project from this folder:

```powershell
git add .
git commit -m "Build offline DevOps learning site with local AI chat"
git branch -M main
git remote add origin https://github.com/USERNAME/devops-local-ai-chat.git
git push -u origin main
```

Replace `USERNAME` with the account that owns the repository. Never commit model weights, API keys, or local environment files. The `.gitignore` excludes common local-only files.

## License

The project code is provided for learning and demonstration. Review the model publishers' license terms before redistributing model weights.
