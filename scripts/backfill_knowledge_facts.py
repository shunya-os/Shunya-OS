#!/usr/bin/env python3
"""CLI script: Backfill knowledge_facts from document extracted_text.

Usage:
    python3 backfill_knowledge_facts.py
    python3 backfill_knowledge_facts.py --doc-id 15
    python3 backfill_knowledge_facts.py --dry-run
"""

import argparse
import sys
import os

# Ensure app can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main():
    parser = argparse.ArgumentParser(description="Backfill knowledge_facts from documents")
    parser.add_argument("--doc-id", type=int, default=None,
                        help="Single document ID to process (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be extracted without storing")
    args = parser.parse_args()

    from app import create_app, db
    from app.document.extraction_pipeline import store_document_facts, backfill_all_documents, extract_entities
    from app.models import Document

    app = create_app()
    with app.app_context():
        if args.dry_run:
            docs = db.session.query(Document).order_by(Document.id).all()
            if args.doc_id:
                docs = [d for d in docs if d.id == args.doc_id]
            print(f"DRY RUN: Scanning {len(docs)} document(s)")
            print("=" * 60)
            for doc in docs:
                text = doc.extracted_text or ""
                if not text.strip():
                    print(f"  Doc#{doc.id} ({doc.filename}): NO TEXT — skipping")
                    continue
                entities = extract_entities(text)
                total_entities = sum(len(v) for v in entities.values())
                print(f"  Doc#{doc.id} ({doc.filename}): {total_entities} entities found")
                for etype, items in entities.items():
                    for item in items:
                        print(f"    [{etype}] {item['value']} (conf={item['confidence']})")
            print("=" * 60)
            return

        if args.doc_id:
            count = store_document_facts(args.doc_id)
            print(f"Stored {count} knowledge_facts from document #{args.doc_id}")
        else:
            results = backfill_all_documents()
            print(
                f"Processed {results['processed']}/{results['total_docs']} documents, "
                f"stored {results['facts_stored']} facts, "
                f"{results['skipped_no_text']} skipped (no text), "
                f"{len(results['errors'])} errors"
            )
            if results["errors"]:
                print("Errors:")
                for err in results["errors"]:
                    print(f"  Doc#{err['doc_id']} ({err['filename']}): {err['error']}")


if __name__ == "__main__":
    main()