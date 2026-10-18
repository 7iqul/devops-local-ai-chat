# DevOps Field Guide with Local AI

An English-language DevOps learning website with a chat assistant in the lower-right corner. The website assistant uses local Ollama models and a safe local calculator. The project also includes an optional Dockerized **Hermes Agent** CLI, which can use the same Ollama service. No hosted AI API is required for the website or for a correctly configured local Hermes setup.

## Features

- Responsive guide covering DevOps principles, Git and GitHub, Docker, CI/CD, Infrastructure as Code, and the delivery loop.
- Lower-right chat widget that answers questions about the guide.
- Two selectable local website models: Qwen 2.5 3B and Llama 3.2 3B.
- Safe deterministic arithmetic for basic expressions such as `125 * 24`.
- Docker Compose services for the website and Ollama, with model data kept in a named volume.
- Optional Hermes Agent Docker service, isolated behind the `hermes` Compose profile so the ordinary website setup does not download its image.
- Continue configuration for using local models in VS Code.
- Prepared for an offline demo after all required images and models have been downloaded once.

## Important: Hermes Agent and the website chat are separate

Hermes Agent is an interactive agent CLI, not an Ollama model. The website's floating chat continues to talk directly to Ollama. Hermes Agent is an additional containerized tool and does not replace or power the website chat in this version. It is not started or downloaded by the normal Compose command. Start it explicitly using the instructions below; it will then appear in Docker Desktop while its command is running.

## Architecture

```text
Browser
  └── DevOps Field Guide + floating chat (:8000)
        └── Python app ──> Ollama (:11434 inside Compose)
                              ├── qwen2.5:3b
                              └── llama3.2:3b

Optional interactive agent
  └── Hermes Agent container (Compose profile: hermes)
        └── Ollama OpenAI-compatible API: http://ollama:11434/v1

VS Code (optional)
  └── Continue ──> Ollama published on host port :11435
```

The app and Ollama communicate over the private Compose network. Ollama's API is published as host port `11435` to avoid conflicting with a native Ollama installation on `11434`. Hermes Agent uses the internal service address `http://ollama:11434/v1`.

## Project files

| File | Purpose |
|---|---|
| `index.html` | English DevOps guide and lower-right chat widget |
| `app.py` | Local HTTP API, guide-specific prompt, model selection, safe arithmetic evaluator |
| `Dockerfile` | Python web app image |
| `docker-compose.yml` | Website and Ollama services plus optional Hermes Agent service/profile |
| `prepare.ps1` | Starts the default stack and downloads the two website models |
| `.continue/config.yaml` | Qwen and Llama model definitions for Continue in VS Code |
| `.vscode/extensions.json` | Recommends Continue when opening this workspace |

## Requirements

- Windows 10/11 with Docker Desktop, or Linux/macOS with Docker Engine and the Docker Compose plugin.
- 8 GB RAM minimum in practice; 16 GB is recommended, especially when running Hermes Agent with a 64K context.
- Free disk space for Docker images and two Ollama models (several GB). Hermes Agent's image is an additional download on first use.
- Internet access for the first image/model downloads. Afterward, the prepared website, models, and Hermes CLI can run offline.
- VS Code and the Continue extension are optional.

## First-time setup: website and local models

On Windows, start Docker Desktop and wait for its engine to report **Running**. Open PowerShell in this repository directory and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\prepare.ps1
```

The script builds the website image, starts the website and Ollama containers, and downloads `qwen2.5:3b` and `llama3.2:3b` into the persistent `ollama_data` volume. The first setup needs internet and may take several minutes.

Open [http://localhost:8000](http://localhost:8000), click the chat button in the lower-right corner, try both models, and ask `What is 125 times 24?` to demonstrate the local calculator.

Useful commands:

```powershell
docker compose ps
docker compose exec ollama ollama list
docker compose logs -f app
docker compose logs -f ollama
docker compose down
```

`docker compose down` preserves model files. Avoid `docker compose down -v` unless you intend to delete the downloaded Ollama models and Hermes data.

## Add and run Hermes Agent in Docker

The Hermes Agent service is already declared in `docker-compose.yml` under the `hermes` profile. It is intentionally optional: normal setup does not download the Hermes image. On first use, while internet is available, run this from the project folder:

```powershell
docker compose --profile hermes run --rm hermes-agent setup
```

In the setup/model wizard, choose **Custom endpoint (self-hosted / VLLM / etc.)** and enter:

- **Base URL:** `http://ollama:11434/v1`
- **API key:** leave empty (Ollama does not require one)
- **Model:** `llama3.2:3b` (or `qwen2.5:3b`)
- **Context length:** at least `65536`

Hermes Agent requires at least a 64K context. The Compose Ollama service sets `OLLAMA_CONTEXT_LENGTH=65536` for this purpose. Larger context can use substantially more RAM when the model is loaded. The laptop must have enough available memory; if Hermes or Ollama reports an out-of-memory error, close other apps or do not run Hermes during the demo.

After setup, launch the interactive Hermes terminal UI with:

```powershell
docker compose --profile hermes run --rm hermes-agent --tui
```

The Hermes container runs interactively and is removed when you exit; its settings persist in the `hermes_data` volume. The image is downloaded once and cached, so the configured CLI can be used offline afterward. If you need to use it offline on another computer, prepare/download the image and Ollama model on that computer in advance. Hermes Agent is separate from the website widget; the widget remains an Ollama chat.

Official Hermes references: [Quickstart](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/getting-started/quickstart.md), [Ollama provider setup](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/integrations/providers.md), [Windows Docker Compose example](https://github.com/NousResearch/hermes-agent/blob/main/docker-compose.windows.yml).

## Offline presentation

While online, finish the website setup and, if you plan to demonstrate Hermes, run its setup command once. Confirm the Ollama models are present with `docker compose exec ollama ollama list`. Test the website chat with both models. Test Hermes separately with its `--tui` command. Then disconnect Wi-Fi and repeat both demos. Keep Docker Desktop running.

Start the prepared website stack with:

```powershell
docker compose up -d
```

Open [http://localhost:8000](http://localhost:8000). Docker images and model weights are not stored in this GitHub repository; each presentation computer must have downloaded them beforehand. If Hermes is part of the offline demo, its image and persistent `hermes_data` configuration must also be available on that computer.

## Use the local models in VS Code

1. Install the **Continue** extension from the VS Code Marketplace while online.
2. Open this project folder in VS Code.
3. Start the website/Ollama stack and wait for Ollama to become healthy.
4. In Continue, select `Qwen 2.5 3B (Local)` or `Llama 3.2 3B (Local)`.
5. Keep the Compose Ollama service running. Continue connects to `http://localhost:11435`.

The workspace configuration is `.continue/config.yaml`. If your Continue version does not read workspace configuration, copy it to `%USERPROFILE%\.continue\config.yaml`. Extension installation requires internet; model inference uses local Ollama.

## Presentation walkthrough

1. Introduce the site as a short guide to DevOps and its delivery workflow.
2. Explain collaboration, automation, and continuous learning from **The Principles**.
3. Point out Git/GitHub, Docker, CI/CD, and Infrastructure as Code in **The Toolkit**.
4. Open the website chat and ask `What is DevOps?`, `How is CI different from CD?`, and `Why use Docker?`.
5. Switch between Qwen and Llama to compare local responses.
6. Ask `What is 125 times 24?` and explain that the deterministic calculator answers arithmetic locally.
7. If you have prepared Hermes, open a second PowerShell window and start its TUI. Explain that Hermes Agent is a separate local agent container configured to use the Ollama service.
8. Turn off Wi-Fi and repeat the prepared demos to show offline operation.

## Troubleshooting

- **Website does not open:** run `docker compose ps`, then inspect `docker compose logs -f app`.
- **Ollama is not ready:** inspect `docker compose logs -f ollama` and wait for its health check.
- **A website model is missing:** while online, run `docker compose exec ollama ollama pull qwen2.5:3b` or `docker compose exec ollama ollama pull llama3.2:3b`.
- **Hermes image is missing:** run the Hermes setup command above while online; Docker downloads its image on first use.
- **Hermes cannot connect to Ollama:** use `http://ollama:11434/v1` from inside the Hermes container, not `localhost`; verify `docker compose ps` shows Ollama healthy.
- **Hermes rejects the context size:** confirm `OLLAMA_CONTEXT_LENGTH=65536` in the Ollama container and recreate it with `docker compose up -d --force-recreate ollama`; then check the running model's context using `docker compose exec ollama ollama ps`.
- **Hermes or Ollama runs out of memory:** the 64K context uses more RAM. Close other applications or skip the Hermes live demo on a memory-limited laptop.
- **Continue cannot connect:** check the Compose stack, open `http://localhost:11435/api/tags`, and ensure model names in `.continue/config.yaml` match `ollama list`.

## GitHub

Repository: [github.com/7iqul/devops-local-ai-chat](https://github.com/7iqul/devops-local-ai-chat)

```powershell
git clone https://github.com/7iqul/devops-local-ai-chat.git
cd devops-local-ai-chat
```

The repository contains source and setup instructions, not model weights or Docker image layers. Never commit model weights, credentials, or local environment files.

## License

This project is provided for learning and demonstration. Review the application, model, and Hermes Agent license terms before redistribution.
