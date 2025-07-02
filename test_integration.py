"""
Test script to demonstrate the integration between main.py and main2.py
This shows how the captcha solving workflow works.
"""

import os
import json


def create_test_session_state():
    """Create a test session state file to simulate captcha detection"""
    test_state = {
        "url": "https://www.google.com",
        "cookies": [],
        "task": "solve_captcha",
    }

    with open("session_state.json", "w") as f:
        json.dump(test_state, f)

    print("Test session state created!")


def cleanup_test_files():
    """Clean up test files"""
    files_to_remove = [
        "session_state.json",
        "captcha_solution.json",
        "page_source.html",
    ]

    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed {file}")


if __name__ == "__main__":
    print("=== Integration Test ===")
    print("1. Creating test session state...")
    create_test_session_state()

    print("\n2. Now run: python main2.py")
    print("   This will solve the captcha using Bright Data")

    print("\n3. After main2.py completes, check captcha_solution.json")
    print("   This file contains the solution data for main.py")

    print("\n4. To clean up test files, run this script again with 'cleanup' argument")

    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_test_files()
