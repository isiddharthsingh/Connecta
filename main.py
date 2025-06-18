#!/usr/bin/env python3
"""
Personal AI Assistant - Main Entry Point

A comprehensive personal assistant that integrates with Gmail, GitHub, 
Calendar, and other services to help you stay organized and productive.

Usage:
    python main.py interactive    # Start interactive mode
    python main.py query "text"   # Process single query
    python main.py status         # Check system status
    python main.py setup          # Initial setup guide
"""

import sys
import os
import logging
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Configure logging
def setup_logging():
    """Configure logging for the application."""
    from src.config import config
    
    log_level = getattr(logging, config.get("logging.level", "INFO").upper())
    log_format = config.get(
        "logging.format", 
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(logs_dir / "assistant.log"),
            logging.StreamHandler(sys.stdout) if config.debug else logging.NullHandler()
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("github").setLevel(logging.WARNING)

def main():
    """Main entry point."""
    try:
        # Setup logging
        setup_logging()
        
        # Import and run CLI
        from src.cli.interface import app
        app()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 