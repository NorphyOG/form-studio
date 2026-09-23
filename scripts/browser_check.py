#!/usr/bin/env python3
"""Compatibility entry point for the current v0.3 integration runner."""
from pathlib import Path
import argparse
from browser_v3 import run
if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('docs/qa-v3'))
    run(parser.parse_args().output)
