#!/usr/bin/env python3
"""Entry point. Run: python main.py [--ingest]"""
import sys


def main():
    if "--ingest" in sys.argv:
        from persona.ingest import ingest_directory
        ingest_directory()
        return

    from bot.telegram_bot import run
    run()


if __name__ == "__main__":
    main()
