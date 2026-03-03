#!/usr/bin/env python3
"""Encrypt and store Rhea-Biomolecula templates."""

import argparse
import base64
import hashlib
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pymongo import MongoClient


def load_key(value: str) -> bytes:
    raw = value.strip()
    try:
        return base64.b64decode(raw)
    except Exception:
        raise SystemExit("BIORENDERER_TEMPLATE_KEY must be base64")


def encrypt_payload(payload: bytes, key: bytes) -> tuple[bytes, bytes]:
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    ct = cipher.encrypt(nonce, payload, None)
    return nonce, ct


def hash_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def store_in_mongo(uri: str, doc: dict) -> None:
    client = MongoClient(uri)
    db = client.get_default_database() if client.get_default_database() else client.get_database("rhea")
    coll = db.get_collection("biomolecula_templates")
    coll.update_one({"scene": doc["scene"]}, {"$set": doc}, upsert=True)
    client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Encrypt Rhea-Biomolecula template and store it safely")
    parser.add_argument("--input", required=True, help="Path to the JSON template")
    parser.add_argument("--output", default=None, help="Output encrypted file (default [input].enc)")
    parser.add_argument("--scene", required=True, help="Scene slug (used as document id)")
    parser.add_argument("--type", default="scene", help="Template type (scene/material/anim)")
    parser.add_argument("--version", type=int, default=1, help="Template version")
    parser.add_argument("--mongo-uri", default=os.environ.get("TASK_DB_URI"), help="Mongo URI for storing metadata")
    parser.add_argument("--key", default=os.environ.get("BIORENDERER_TEMPLATE_KEY"), help="Base64 AES key")
    args = parser.parse_args()

    if not args.key:
        parser.error("BIORENDERER_TEMPLATE_KEY is required (pass --key or set env)")

    key = load_key(args.key)
    inp = Path(args.input)
    if not inp.exists():
        parser.error(f"Input file {inp} does not exist")

    with inp.open("rb") as fh:
        data = fh.read()

    nonce, cipher = encrypt_payload(data, key)
    out = Path(args.output or f"{inp}.enc")
    out.parent.mkdir(parents=True, exist_ok=True)
    export_doc = {
        "scene": args.scene,
        "type": args.type,
        "version": args.version,
        "hash": hash_payload(data),
        "created_at": args.scene,
        "created_by": os.environ.get("USER", "orion"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "encrypted_blob": base64.b64encode(cipher).decode("ascii"),
    }
    with out.open("wb") as fh:
        fh.write(base64.b64encode(nonce + cipher))

    print(f"Encrypted template -> {out}")

    if args.mongo_uri:
        doc = export_doc.copy()
        doc["encrypted_blob"] = export_doc["encrypted_blob"]
        store_in_mongo(args.mongo_uri, doc)
        print("Stored metadata in Mongo")


if __name__ == "__main__":
    main()
