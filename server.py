#!/usr/bin/env python3
import os
import sys

# Ensure backend directory is on sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_dir)

from app import run

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    run(port=port)
