import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.evaluation.dataset import EvalDataset
from app.evaluation.evaluator import RAGEvaluator

router = APIRouter(prefix="/eval", tags=["RAG Evaluation"])


@router.post("/run", status_code=status.HTTP_200_OK)
def run_evaluation(
    top_k: int = Query(25, ge=1, le=100),
    rerank_k: int = Query(10, ge=1, le=50),
    context_budget: int = Query(4000, ge=500, le=16000),
    dataset_path: Optional[str] = Query(None, description="Path to evaluation dataset JSON"),
    db: Session = Depends(get_db)
):
    """
    Execute RAG Evaluation framework on benchmark dataset.
    Tracks Precision@K, Recall@K, MRR, Answer Relevance, Faithfulness, and Citation Correctness.
    Allows experiments with top_k, rerank_k, and context_budget.
    """
    default_path = os.path.join(os.path.dirname(__file__), "..", "evaluation", "datasets", "sample_eval_dataset.json")
    target_path = dataset_path or default_path

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation dataset file '{target_path}' not found."
        )

    try:
        dataset = EvalDataset.load_from_file(target_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse dataset file: {str(e)}"
        )

    evaluator = RAGEvaluator(db)
    summary = evaluator.evaluate_dataset(
        dataset=dataset,
        top_k=top_k,
        rerank_k=rerank_k,
        context_budget=context_budget
    )

    return summary
