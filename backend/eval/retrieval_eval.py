"""Retrieval evaluation — measures Recall@K across 30 gold Q&A pairs.

Recall@K answers: "For what fraction of questions does the correct
document appear in the top K retrieved chunks?"

This is a fast, deterministic metric — no LLM calls needed. Run it
after any change to chunking, embeddings, or retrieval parameters.

Usage:
    python eval/retrieval_eval.py
    python eval/retrieval_eval.py --k 3        # stricter gate
    python eval/retrieval_eval.py --fail-below 0.85
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.pipeline.retrieval import retrieve

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

GOLD_PATH = Path(__file__).parent / "gold_qa.json"

# CI gate defaults
DEFAULT_K = 5
DEFAULT_FAIL_BELOW = 0.80


async def evaluate(k: int) -> dict:
    gold = json.loads(GOLD_PATH.read_text())

    results = []
    async with AsyncSessionLocal() as session:
        for item in gold:
            chunks = await retrieve(session, item["question"])
            retrieved_urls = [c.url for c in chunks[:k]]

            # A hit = the expected document URL appears in the top K results
            hit = item["expected_url"] in retrieved_urls
            rank = next(
                (i + 1 for i, c in enumerate(chunks) if c.url == item["expected_url"]),
                None,
            )

            results.append(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "expected_url": item["expected_url"],
                    "hit": hit,
                    "rank": rank,
                    "retrieved_urls": retrieved_urls,
                }
            )

    hits = sum(r["hit"] for r in results)
    recall = hits / len(results)

    return {
        "recall_at_k": recall,
        "k": k,
        "hits": hits,
        "total": len(results),
        "results": results,
    }


def print_report(report: dict) -> None:
    k = report["k"]
    recall = report["recall_at_k"]
    hits = report["hits"]
    total = report["total"]

    print(f"\n{'='*60}")
    print(f"  RETRIEVAL EVAL — Recall@{k}")
    print(f"{'='*60}")
    print(f"  Score:  {recall:.1%}  ({hits}/{total} questions)")
    print(f"{'='*60}\n")

    misses = [r for r in report["results"] if not r["hit"]]
    if misses:
        print(f"  MISSES ({len(misses)}):")
        for r in misses:
            print(f"  [{r['id']}] {r['question'][:70]}")
            print(f"         Expected: .../{r['expected_url'].split('/')[-2]}/")
            print(f"         Got:      {[u.split('/')[-2] for u in r['retrieved_urls']]}")
            print()
    else:
        print("  All questions retrieved correctly.\n")

    hits_list = [r for r in report["results"] if r["hit"]]
    if hits_list:
        avg_rank = sum(r["rank"] for r in hits_list) / len(hits_list)
        print(f"  Average rank of correct doc (hits only): {avg_rank:.1f}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieval eval for RAG pipeline")
    parser.add_argument("--k", type=int, default=DEFAULT_K, help="Recall@K cutoff")
    parser.add_argument(
        "--fail-below",
        type=float,
        default=DEFAULT_FAIL_BELOW,
        help="Exit code 1 if recall is below this threshold (CI gate)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    report = asyncio.run(evaluate(args.k))

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    if report["recall_at_k"] < args.fail_below:
        print(
            f"  FAIL: Recall@{args.k} = {report['recall_at_k']:.1%} "
            f"< threshold {args.fail_below:.1%}"
        )
        sys.exit(1)
    else:
        print(
            f"  PASS: Recall@{args.k} = {report['recall_at_k']:.1%} "
            f">= threshold {args.fail_below:.1%}"
        )


if __name__ == "__main__":
    main()
