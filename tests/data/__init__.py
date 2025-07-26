"""Examples to evaluate."""

from typing import Literal
import jsonl
from pathlib import Path

from deepeval.dataset import EvaluationDataset


_current = Path(__file__).parent.absolute()

PROMPTS_DIR: Path = _current / "prompts"
DATASETS_DIR: Path = _current / "datasets"
DOCUMENTS_DIR: Path = _current / "documents"


def load_deepeval_dataset(dataset_name: str, file_type: Literal["json"] = "json"):
    """Load an EvaluationDataset from a JSON file.
    
    Aware: JSONL is not currently supported by the deepeval library
    Parameters
    ----------
    dataset_name : str
        The base name of the dataset file (without extension).
    file_type : Literal["json", "jsonl"], optional
        The file type to load, either 'json' or 'jsonl'. Defaults to 'jsonl'.

    Returns:
    -------
    EvaluationDataset
        The loaded evaluation dataset.
    """
    # TODO add csv
    
    kw = dict(
        file_path=DATASETS_DIR / f"{dataset_name}.{file_type}",
        input_key_name="input",
        actual_output_key_name="actual_output",
        expected_output_key_name="expected_output",
        context_key_name="context",
        retrieval_context_key_name="retrieval_context",
    )
    dataset = EvaluationDataset()
    if file_type in ("json", "jsonl"):
        dataset.add_goldens_from_json_file(**kw)
    return dataset


def get_prompt(name: str) -> dict[str, str]:
    """Read single prompt."""
    if not name.endswith(".md"):
        name += ".md"
    with open(PROMPTS_DIR / name, "r") as f:
        content = f.read()
    return {"name": name.replace(".md", ""), "content": content}


def get_all_prompts() -> list[dict[str, str]]:
    """Read all prompts."""
    return [get_prompt(f) for f in PROMPTS_DIR.iterdir() if f.is_file()]
