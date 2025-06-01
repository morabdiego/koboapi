import os
from dotenv import load_dotenv
from koboapi import Kobo
from pprint import pprint

load_dotenv()
API_KEY = os.getenv("KOBO_KEY")

# Initialize client with debug enabled to see URL construction
client = Kobo(token=API_KEY, debug=True)

print("=== TESTING ALL WRAPPER METHODS WITH DEBUG MODE ===\n")

try:
    print("1. Testing list_assets():")
    print("-" * 40)
    assets = client.list_assets()
    # pprint(assets[:2])  # Show only first 2 assets
    print(f"Found {len(assets)} assets\n")

    print("2. Testing list_uid():")
    print("-" * 40)
    uid_map = client.list_uid()
    print(f"Asset name -> UID mapping:")
    for name, uid in list(uid_map.items())[:3]:  # Show first 3
        print(f"  {name}: {uid}")
    print(f"... and {len(uid_map) - 3} more\n")

    if uid_map:
        # Get first asset UID for testing
        first_asset_uid = list(uid_map.values())[1]
        first_asset_name = list(uid_map.keys())[1]

        print(f"3. Testing get_asset() with UID: {first_asset_uid}")
        print("-" * 40)
        asset_detail = client.get_asset(first_asset_uid)
        print(f"Asset name: {asset_detail.get('name', 'N/A')}")
        print(f"Asset type: {asset_detail.get('asset_type', 'N/A')}\n")

        print(f"4. Testing get_data() with various parameters:")
        print("-" * 40)

        # Test basic data retrieval
        print("  4a. Basic data retrieval:")
        data_basic = client.get_data(first_asset_uid, limit=5)
        print(f"    Retrieved {len(data_basic.get('results', []))} records\n")

        # Test with query parameter
        print("  4b. With query parameter:")
        data_query = client.get_data(
            first_asset_uid,
            query='{"_id": {"$gt": 1}}',
            limit=3
        )
        print(f"    Retrieved {len(data_query.get('results', []))} records\n")

        # Test with submitted_after
        print("  4c. With submitted_after parameter:")
        data_after = client.get_data(
            first_asset_uid,
            submitted_after="2024-01-01T00:00:00",
            limit=3
        )
        print(f"    Retrieved {len(data_after.get('results', []))} records\n")

        # Test with start and limit
        print("  4d. With start and limit parameters:")
        data_paginated = client.get_data(
            first_asset_uid,
            start=0,
            limit=2
        )
        print(f"    Retrieved {len(data_paginated.get('results', []))} records\n")

        # Test with query and submitted_after (should ignore submitted_after)
        print("  4e. With both query and submitted_after (should ignore submitted_after):")
        data_both = client.get_data(
            first_asset_uid,
            query='{"_id": {"$gt": 1}}',
            submitted_after="2024-01-01T00:00:00",
            limit=2
        )
        print(f"    Retrieved {len(data_both.get('results', []))} records\n")

        print("5. Testing get_choices():")
        print("-" * 40)
        choices = client.get_choices(asset_detail)
        print(f"Found {len(choices)} choice lists:")
        for list_name, choice_dict in list(choices.items())[:2]:  # Show first 2
            print(f"  {list_name}: {len(choice_dict)} choices")
        print()

        print("6. Testing get_questions() without unpacking:")
        print("-" * 40)
        questions_basic = client.get_questions(asset_detail, unpack_multiples=False)
        print(f"Found {len(questions_basic.get('questions', {}))} root questions")
        print(f"Found {len(questions_basic.get('groups', {}))} groups\n")

        print("7. Testing get_questions() with unpacking multiples:")
        print("-" * 40)
        questions_unpacked = client.get_questions(asset_detail, unpack_multiples=True)
        print(f"Found {len(questions_unpacked.get('questions', {}))} root questions (unpacked)")
        print(f"Found {len(questions_unpacked.get('groups', {}))} groups (unpacked)\n")

        print("8. Testing download_xlsform():")
        print("-" * 40)
        try:
            filepath = client.download_xlsform(first_asset_uid)
            print(f"XLS form downloaded successfully to: {filepath}")
            # Check if file exists
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"File size: {file_size} bytes")
            else:
                print("Warning: File was not created")
        except Exception as e:
            print(f"Download failed: {e}")
        print()

    else:
        print("No assets found to test detailed methods\n")

except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()

print("=== TESTING DIFFERENT ENDPOINTS ===\n")

print("9. Testing humanitarian endpoint:")
print("-" * 40)
try:
    humanitarian_client = Kobo(token=API_KEY, endpoint='humanitarian', debug=True)
    humanitarian_assets = humanitarian_client.list_assets()
    print(f"Humanitarian endpoint assets: {len(humanitarian_assets)}\n")
except Exception as e:
    print(f"Humanitarian endpoint error: {e}\n")

print("10. Testing custom endpoint:")
print("-" * 40)
try:
    custom_client = Kobo(token=API_KEY, endpoint='https://custom.example.com/', debug=True)
    # This will likely fail but shows URL construction
    custom_assets = custom_client.list_assets()
except Exception as e:
    print(f"Custom endpoint error (expected): {e}\n")

print("=== URL CONSTRUCTION TESTING COMPLETE ===")
