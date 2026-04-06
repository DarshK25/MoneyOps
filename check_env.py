from pathlib import Path
import os

config_path = Path(r"c:\Users\Paarth kothari\OneDrive\Desktop\Projects\moneyops\Moneyops\ai-gateway\app\config.py")
root_env = config_path.resolve().parents[2] / ".env"
print(f"Searching for .env at: {root_env}")
print(f"File exists: {root_env.exists()}")

current_env = Path(r"c:\Users\Paarth kothari\OneDrive\Desktop\Projects\moneyops\.env")
print(f"Root .env exists: {current_env.exists()}")

gateway_env = Path(r"c:\Users\Paarth kothari\OneDrive\Desktop\Projects\moneyops\Moneyops\ai-gateway\.env")
print(f"Gateway .env exists: {gateway_env.exists()}")
