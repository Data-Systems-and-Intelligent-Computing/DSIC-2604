"""Block-randomized repeated-query benchmark harness."""
import random
from dataclasses import dataclass
from src.common import write_jsonl

@dataclass(frozen=True)
class RunCondition:
    file_size_mib: int
    query_family: str
    selectivity_id: str

def randomized_block(conditions, seed):
    items = list(conditions)
    random.Random(seed).shuffle(items)
    return items

def record_run(path, payload):
    write_jsonl(path, payload)
