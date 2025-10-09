import os
from dotenv import load_dotenv


def main():
    # Load env from project root .env if present
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", ".env")
    env_path = os.path.abspath(env_path)
    if os.path.exists(env_path):
        load_dotenv(env_path)

    # Print minimal info
    print("Running MT5 trade executor once...")

    # Import and run job
    from worker.mt5_jobs import job_mt5_trade_executor
    job_mt5_trade_executor()


if __name__ == "__main__":
    main()


