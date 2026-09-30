# Backend container - deployable to Cloud Run / Render / Railway / any container host
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ai_engine ./ai_engine
COPY cloud ./cloud
COPY backend ./backend
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT}"]
