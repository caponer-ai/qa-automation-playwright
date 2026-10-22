# Official Playwright image: browsers and system deps are already inside
FROM mcr.microsoft.com/playwright/python:v1.64.0-noble

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd -m tester && chown -R tester /app
USER tester

CMD ["pytest", "-m", "not perf", "-n", "auto"]
