#!/usr/bin/env python3
"""Run Weslr Test Harness and Scorecard.

Usage:
    python run_weslr_tests.py [--json] [--category SECURITY]
    python run_weslr_tests.py --scorecard --results results.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from weslr.test_harness import create_test_harness
from weslr.test_scorecard import create_scorecard, evaluate_weslr


def run_harness_only(workspace: Path = None):
    """Run test harness only."""
    print("=" * 60)
    print("WESLR TEST HARNESS")
    print("=" * 60)
    
    harness = create_test_harness(workspace_dir=workspace)
    results = harness.run_all()
    
    return results


def run_scorecard_only(results: dict = None):
    """Run scorecard evaluation."""
    print("=" * 60)
    print("WESLR RELEASE SCORECARD")
    print("=" * 60)
    
    scorecard = create_scorecard()
    
    # Use provided results or run harness
    if results is None:
        results = run_harness_only()
    
    evaluation = scorecard.evaluate(results)
    formatted = scorecard.to_scorecard_format(results)
    
    return formatted


def run_full(workspace: Path = None, output_json: bool = False):
    """Run full test suite with scorecard."""
    print("\n" + "=" * 60)
    print("WESLR TEST HARNESS + SCORECARD")
    print("=" * 60)
    
    # Run harness
    print("\n[1/2] Running test harness...")
    start_time = time.time()
    harness = create_test_harness(workspace_dir=workspace)
    results = harness.run_all()
    harness_time = time.time() - start_time
    
    # Run scorecard
    print("[2/2] Running scorecard...")
    scorecard = create_scorecard()
    evaluation = scorecard.evaluate(results)
    formatted = scorecard.to_scorecard_format(results)
    
    # Print results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if output_json:
        output = {
            "harness": results,
            "scorecard": formatted,
            "evaluation": evaluation,
            "metadata": {
                "harness_time_ms": harness_time * 1000,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\nTotal Score: {formatted['total_score']}/{formatted['max_score']}")
        print(f"Release Readiness: {formatted['release_readiness']}")
        print(f"Status: {formatted.get('readiness_status', 'unknown')}")
        
        print(f"\nCategories:")
        for cat, data in formatted['categories'].items():
            status = "✓" if data['score'] >= 80 else ("⚠" if data['score'] >= 50 else "✗")
            threshold = "✓" if data.get('passes', True) else "✗"
            print(f"  [{status}] {cat}: {data['score']}% ({data['passed']} passed, {data['failed']} failed)")
            print(f"      [{threshold}] Threshold: {data.get('threshold', 'N/A')}")
        
        print(f"\nCategory Scores:")
        for cat, score in evaluation['scores'].items():
            max_score = evaluation['details'][cat]['max_score']
            print(f"  {cat}: {score:.1f}/{max_score}")
        
        print(f"\nDuration: {harness_time * 1000:.2f}ms")
    
    return formatted


def main():
    parser = argparse.ArgumentParser(description="Weslr Test Runner")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--category", "-c", help="Filter by category")
    parser.add_argument("--workspace", "-w", help="Workspace directory")
    parser.add_argument("--results", "-r", help="Path to existing results file")
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace) if args.workspace else None
    
    if args.results:
        with open(args.results, 'r') as f:
            results = json.load(f)
        run_scorecard_only(results)
    else:
        run_full(workspace=workspace, output_json=args.json)


if __name__ == "__main__":
    main()
