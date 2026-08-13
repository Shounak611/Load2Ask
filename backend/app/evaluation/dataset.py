import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class EvalTestCase(BaseModel):
    id: Optional[str] = None
    question: str = Field(..., description="User evaluation question")
    expected_answer: str = Field(..., description="Ground truth answer")
    expected_sources: List[str] = Field(default_factory=list, description="Expected source document names or IDs")


class EvalDataset(BaseModel):
    name: str = "Benchmark Evaluation Dataset"
    test_cases: List[EvalTestCase]

    @classmethod
    def load_from_file(cls, file_path: str) -> "EvalDataset":
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Evaluation dataset file not found: {file_path}")
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            test_cases = [EvalTestCase(**item) for item in data]
            return cls(name=path.stem, test_cases=test_cases)
        elif isinstance(data, dict):
            return cls(**data)
        else:
            raise ValueError(f"Invalid dataset JSON structure in {file_path}")
