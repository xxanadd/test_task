FROM python:3.9-slim-buster
LABEL authors="xxanadd"
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]