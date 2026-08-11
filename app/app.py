from flask import Flask
import os

app = Flask(__name__)


@app.route("/")
def home():
    return {
        "application": "secure-ai-devsecops-platform",
        "status": "running",
        "version": os.getenv("APP_VERSION", "1.0.0")
    }


@app.route("/health")
def health():
    return {
        "status": "healthy"
    }


@app.route("/ready")
def ready():
    return {
        "status": "ready"
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)