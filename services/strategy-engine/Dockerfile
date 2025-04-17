FROM python:3.10-slim
WORKDIR /app
ENV PYTHONPATH=/app
COPY . .
RUN pip install pandas pytest
CMD ["pytest"]