from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.evaluation.dataset import EvalDataset, EvalTestCase
from app.evaluation.metrics import (
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_mrr,
    calculate_answer_relevance,
    calculate_faithfulness,
    calculate_citation_correctness
)
from app.services.query_service import RAGQueryService
from app.core.logging import logger


class RAGEvaluator:
    """Evaluation framework running experiments over RAG pipelines."""

    def __init__(self, db: Session):
        self.db = db
        self.query_service = RAGQueryService(db)

    def evaluate_dataset(
        self,
        dataset: EvalDataset,
        top_k: int = 25,
        rerank_k: int = 10,
        context_budget: int = 4000,
        eval_k: int = 5
    ) -> Dict[str, Any]:
        """Runs evaluation over all test cases in the dataset and computes aggregate metrics."""
        results = []
        precision_scores = []
        recall_scores = []
        mrr_scores = []
        relevance_scores = []
        faithfulness_scores = []
        citation_scores = []
        latencies = []

        for test_case in dataset.test_cases:
            res = self.query_service.process_query(
                query=test_case.question,
                top_k=top_k,
                rerank_k=rerank_k,
                context_budget=context_budget
            )

            answer = res.get("answer", "")
            sources = res.get("sources", [])
            retrieved_src_names = [s.get("document", "") for s in sources]
            retrieval_debug = res.get("retrieval_debug", {})

            # Compute Metrics
            p_at_k = calculate_precision_at_k(retrieved_src_names, test_case.expected_sources, k=eval_k)
            r_at_k = calculate_recall_at_k(retrieved_src_names, test_case.expected_sources, k=eval_k)
            mrr = calculate_mrr(retrieved_src_names, test_case.expected_sources)
            ans_rel = calculate_answer_relevance(answer, test_case.expected_answer)

            # Build context string representation from sources for faithfulness
            context_summary = " ".join(retrieved_src_names)
            faithfulness = calculate_faithfulness(answer, context_summary)
            cit_correctness = calculate_citation_correctness(sources, test_case.expected_sources)

            latency = retrieval_debug.get("total_latency_ms", 0.0)

            precision_scores.append(p_at_k)
            recall_scores.append(r_at_k)
            mrr_scores.append(mrr)
            relevance_scores.append(ans_rel)
            faithfulness_scores.append(faithfulness)
            citation_scores.append(cit_correctness)
            latencies.append(latency)

            results.append({
                "test_id": test_case.id,
                "question": test_case.question,
                "answer": answer,
                "retrieved_sources": retrieved_src_names,
                "expected_sources": test_case.expected_sources,
                "metrics": {
                    "precision_at_k": p_at_k,
                    "recall_at_k": r_at_k,
                    "mrr": mrr,
                    "answer_relevance": ans_rel,
                    "faithfulness": faithfulness,
                    "citation_correctness": cit_correctness,
                    "latency_ms": latency
                }
            })

        avg_precision = round(sum(precision_scores) / max(len(precision_scores), 1), 4)
        avg_recall = round(sum(recall_scores) / max(len(recall_scores), 1), 4)
        avg_mrr = round(sum(mrr_scores) / max(len(mrr_scores), 1), 4)
        avg_relevance = round(sum(relevance_scores) / max(len(relevance_scores), 1), 4)
        avg_faithfulness = round(sum(faithfulness_scores) / max(len(faithfulness_scores), 1), 4)
        avg_citation = round(sum(citation_scores) / max(len(citation_scores), 1), 4)
        avg_latency = round(sum(latencies) / max(len(latencies), 1), 2)

        summary = {
            "dataset_name": dataset.name,
            "total_test_cases": len(dataset.test_cases),
            "experiment_params": {
                "top_k": top_k,
                "rerank_k": rerank_k,
                "context_budget": context_budget,
                "eval_k": eval_k
            },
            "aggregate_metrics": {
                "precision_at_k": avg_precision,
                "recall_at_k": avg_recall,
                "mrr": avg_mrr,
                "answer_relevance": avg_relevance,
                "faithfulness": avg_faithfulness,
                "citation_correctness": avg_citation,
                "average_latency_ms": avg_latency
            },
            "test_case_results": results
        }

        logger.log_observability("rag_evaluation_run", summary["aggregate_metrics"])
        return summary
