# Containerized proof: builds the warehouse from the vendored data and runs the
# full offline suite (SQL guard, harness, golden reference SQL). CI builds and
# runs this image, so "works on my machine" is never the claim.
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["pytest", "tests/", "-v"]
