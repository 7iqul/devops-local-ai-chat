FROM python:3.12-slim
WORKDIR /app
COPY app.py index.html ./
ENV PORT=8000 OLLAMA_URL=http://ollama:11434 PYTHONDONTWRITEBYTECODE=1
EXPOSE 8000
CMD ["python", "app.py"]
