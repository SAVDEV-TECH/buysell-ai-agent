import os
import sys

# Ensure src directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import uvicorn

if __name__ == "__main__":
    port_str = os.environ.get("PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        port = 8080
    
    print(f"Starting BuySell Agent API on port {port}...")
    uvicorn.run("buysell_agent.api:app", host="0.0.0.0", port=port)
