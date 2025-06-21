#!/usr/bin/env python3
"""
Main execution file for AI Newsletter Summary
This file orchestrates the pipeline and app execution
"""

import subprocess
import sys
import logging
from datetime import datetime
import pytz
import os
import platform

# Determine the base directory and create logs directory if it doesn't exist
if platform.system() == 'Windows':
    # For Windows (testing)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(base_dir, 'logs')
else:
    # For Linux (production)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(base_dir, 'logs')

os.makedirs(logs_dir, exist_ok=True)

# Set up logging
log_file = os.path.join(logs_dir, 'main.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set timezone
EST = pytz.timezone('US/Eastern')


def run_pipeline():
    """Execute the pipeline.py script"""
    logger.info("🔄 Starting pipeline execution...")

    try:
        # Run pipeline.py
        result = subprocess.run([
            sys.executable, 'pipeline.py'
        ], capture_output=True, text=True, cwd=base_dir)

        if result.returncode == 0:
            logger.info("✅ Pipeline executed successfully!")
            logger.info(f"Pipeline output: {result.stdout}")
            return True
        else:
            logger.error(f"❌ Pipeline failed with return code {result.returncode}")
            logger.error(f"Pipeline error: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"❌ Error running pipeline: {e}")
        return False


def run_app():
    """Execute the app.py script"""
    logger.info("🚀 Starting Streamlit app...")

    try:
        if platform.system() != 'Windows':
            # Kill any existing streamlit processes (Linux only)
            subprocess.run(['pkill', '-f', 'streamlit'], capture_output=True)

        # Start streamlit app in background
        if platform.system() == 'Windows':
            # For Windows testing
            process = subprocess.Popen([
                sys.executable, '-m', 'streamlit', 'run', 'app.py',
                '--server.port=8501',
                '--server.address=localhost'
            ], cwd=base_dir)
        else:
            # For Linux production
            process = subprocess.Popen([
                sys.executable, '-m', 'streamlit', 'run', 'app.py',
                '--server.port=8501',
                '--server.address=0.0.0.0',
                '--server.headless=true'
            ], cwd=base_dir)

        logger.info(f"✅ Streamlit app started with PID: {process.pid}")

        # Save PID for later management
        pid_file = os.path.join(base_dir, 'streamlit.pid')
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))

        return True

    except Exception as e:
        logger.error(f"❌ Error starting app: {e}")
        return False


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("🚀 Starting AI Newsletter Summary System")
    logger.info(f"⏰ Current EST time: {datetime.now(EST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("=" * 60)

    # Step 1: Run pipeline to fetch and process articles
    pipeline_success = run_pipeline()

    if not pipeline_success:
        logger.error("❌ Pipeline failed. Stopping execution.")
        return 1

    # Step 2: Start the Streamlit app
    app_success = run_app()

    if not app_success:
        logger.error("❌ App startup failed.")
        return 1

    logger.info("✅ AI Newsletter Summary System started successfully!")
    logger.info("📱 App should be accessible at your domain/IP on port 8501")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())