# Imagem da API para o Render ou o Fly.io. Construa a partir da raiz do repositório:
#   docker build -f apps/api/Dockerfile -t music-tutor-api .
# A API lê o currículo, os templates e as aulas publicadas da árvore do repositório.
FROM python:3.11-slim

WORKDIR /app
COPY apps/api/pyproject.toml apps/api/
COPY apps/api/music_tutor apps/api/music_tutor
COPY curriculo curriculo
COPY templates-aula templates-aula
COPY aulas-exemplo aulas-exemplo
RUN pip install --no-cache-dir -e apps/api

WORKDIR /app/apps/api
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn music_tutor.app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
