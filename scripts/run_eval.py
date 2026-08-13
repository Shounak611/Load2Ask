#!/usr/bin/env python3
"""
CLI Script for running RAG Evaluation Experiments
Usage:
    python scripts/run_eval.py --top-k 25 --rerank-k 10 --context-budget 4000
"""

import sys
import os
import json
import argparse

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database.session import init_db, SessionLocal
from app.evaluation.dataset import EvalDataset
from app.evaluation.evaluator import RAGEvaluator


def main():
    parser = argparse.ArgumentParser(description="Run RAG Evaluation Experiments")
    parser.add_argument("--dataset", type=str, default=None, help="Path to evaluation dataset JSON")
    parser.add_argument("--top-k", type=int, default=25, help="Retrieval Top K")
    parser.add_argument("--rerank-k", type=int, default=10, help="Rerank Top K")
    parser.add_argument("--context-budget", type=int, default=4000, help="Context Token Budget")

    args = parser.parse_args()

    init_db()
    db = SessionLocal()

    default_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app", "evaluation", "datasets", "sample_eval_dataset.json"))
    target_path = args.dataset or default_path

    print(f"==================================================")
    print(f"Running RAG Evaluation Experiment")
    print(f"Dataset: {target_path}")
    print(f"Parameters: top_k={args.top_k}, rerank_k={args.rerank_k}, context_budget={args.context_budget}")
    print(f"==================================================\n")

    dataset = EvalDataset.load_from_file(target_path)
    evaluator = RAGEvaluator(db)

    summary = evaluator.evaluate_dataset(
        dataset=dataset,
        top_k=args.top_k,
        rerank_k=args.rerank_k,
        context_budget=args.context_budget
    )

    print("\n--- AGGREGATE EVALUATION METRICS ---")
    for metric, score in summary["aggregate_metrics"].items():
        print(f"  {metric:<22}: {score}")

    print("\nEvaluation Complete.")
    db.close()


if __name__ == "__main__":
    main()
