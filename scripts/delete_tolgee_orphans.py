#!/usr/bin/env python3.14
"""Delete orphan keys from Tolgee by comparing Tolgee keys against EN canonical keys.

Identifies orphans by fetching Tolgee keys per namespace and comparing against
locales/en/<ns>.json (authoritative). Deletes keys that exist in Tolgee but not
in EN.

Usage:
  python3.14 scripts/delete_tolgee_orphans.py --dry-run   # report only
  python3.14 scripts/delete_tolgee_orphans.py             # actually delete
"""
import json, os, sys, urllib.request, time

API_URL = "http://127.0.0.1:8080"
PROJECT_ID = 6
API_KEY = os.environ.get("TOLGEE_API_KEY", "tgpak_gzpwk3bxmeyxi5dfgqytczzzmvtdendpov2tanlpm52gy")
DRY_RUN = "--dry-run" in sys.argv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN_DIR = os.path.join(BASE_DIR, "locales", "en")
MODULES_FILE = os.path.join(BASE_DIR, "locales", "modules.json")


def fetch_all_project_keys():
    """Fetch ALL keys from the project, paginating."""
    all_keys = []
    page = 0
    while True:
        url = f"{API_URL}/v2/projects/{PROJECT_ID}/keys?size=500&sort=id,asc&page={page}"
        req = urllib.request.Request(url, headers={"X-API-Key": API_KEY})
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode())
        page_keys = data["_embedded"]["keys"]
        all_keys.extend(page_keys)
        total_pages = data["page"]["totalPages"]
        if page >= total_pages - 1:
            break
        page += 1
    return all_keys


def delete_key(key_id):
    """Delete a single key by ID."""
    url = f"{API_URL}/v2/projects/{PROJECT_ID}/keys/{key_id}"
    req = urllib.request.Request(url, method="DELETE", headers={"X-API-Key": API_KEY})
    urllib.request.urlopen(req)


def main():
    # Load EN canonical keys per namespace
    modules = json.load(open(MODULES_FILE))
    en_keys_by_ns = {}
    for ns in modules:
        en_file = os.path.join(EN_DIR, f"{ns}.json")
        if os.path.exists(en_file):
            data = json.load(open(en_file))
            # Flatten nested keys: for each path in the JSON, build the full key name
            def flatten(obj, prefix=""):
                result = set()
                for k, v in obj.items():
                    full = f"{prefix}{k}" if prefix else k
                    result.add(full)
                    if isinstance(v, dict):
                        result.update(flatten(v, f"{full}."))
                return result
            en_keys_by_ns[ns] = flatten(data)
        else:
            en_keys_by_ns[ns] = set()

    # Build master EN key name set (all canonical names across all namespaces)
    all_en_names = set()
    for ns, names in en_keys_by_ns.items():
        all_en_names.update(names)

    print(f"Loading Tolgee keys (fetching entire project)...")
    all_tolgee_keys = fetch_all_project_keys()
    print(f"  Total Tolgee keys: {len(all_tolgee_keys)}")

    # Post-filter: for each key, check if its name matches EN canonical keys
    # Keys that exist in Tolgee but NOT in EN are orphans
    orphans = []
    for k in all_tolgee_keys:
        name = k.get("name", "")
        if name not in all_en_names:
            orphans.append(k)

    # Also check: keys in generated/ui namespace whose names don't match
    # the generated/ui EN file specifically
    gen_en = en_keys_by_ns.get("generated/ui", set())
    gen_tolgee = [k for k in all_tolgee_keys if k.get("namespace") == "generated/ui"]
    gen_orphans = [k for k in gen_tolgee if k.get("name", "") not in gen_en]

    print(f"\n=== ORPHAN ANALYSIS ===")
    print(f"All Tolgee keys not in any EN file: {len(orphans)}")
    print(f"Generated/ui orphans (namespace-filtered): {len(gen_orphans)}")

    # Use the namespace-filtered approach for generated/ui (more precise)
    # For other namespaces, check individually
    all_orphan_ids = []
    
    # generated/ui orphans
    for k in gen_orphans:
        all_orphan_ids.append(k["id"])

    # Check other namespaces for orphans (should be minimal)
    for ns in modules:
        if ns == "generated/ui":
            continue
        ns_en = en_keys_by_ns.get(ns, set())
        ns_tolgee = [k for k in all_tolgee_keys if k.get("namespace") == ns]
        ns_orphans = [k for k in ns_tolgee if k.get("name", "") not in ns_en]
        for k in ns_orphans:
            all_orphan_ids.append(k["id"])

    print(f"\nTotal orphan key IDs to delete: {len(all_orphan_ids)}")

    # Show samples
    if all_orphan_ids:
        print("\nOrphan samples (first 15):")
        seen_names = set()
        for k in [k for k in all_tolgee_keys if k["id"] in all_orphan_ids][:15]:
            name = k["name"]
            ns = k.get("namespace", "?")
            if name not in seen_names:
                print(f"  ID={k['id']} | NS={ns} | Name={name}")
                seen_names.add(name)

    if not all_orphan_ids:
        print("No orphans found. Done.")
        return

    if DRY_RUN:
        print(f"\n[DRY RUN] Would delete {len(all_orphan_ids)} keys. Remove --dry-run to execute.")
        return

    # Execute deletion
    print(f"\nDeleting {len(all_orphan_ids)} orphan keys in batches of 100...")
    deleted = 0
    failed = 0
    for i in range(0, len(all_orphan_ids), 100):
        batch = all_orphan_ids[i : i + 100]
        # Try batch delete first
        url = f"{API_URL}/v2/projects/{PROJECT_ID}/keys"
        body = json.dumps(batch).encode()
        req = urllib.request.Request(
            url, method="DELETE", data=body,
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(req)
            deleted += len(batch)
        except Exception:
            # Fallback: delete individually
            for kid in batch:
                try:
                    delete_key(kid)
                    deleted += 1
                except Exception as ex:
                    print(f"  Failed to delete key {kid}: {ex}", file=sys.stderr)
                    failed += 1
        print(f"  Batch {i // 100 + 1}: deleted={deleted}, failed={failed}")
        time.sleep(0.1)  # rate limit courtesy

    print(f"\n[OK] Deleted {deleted} orphan keys, failed={failed}")


if __name__ == "__main__":
    main()