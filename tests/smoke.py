import os
import sys
import json
from dotenv import load_dotenv

# Debug information
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")

try:
    from koboapi import Kobo
    print("✅ koboapi imported successfully")
except ImportError as e:
    print(f"❌ Failed to import koboapi: {e}")
    print("Available packages:")
    import pkg_resources
    installed_packages = [d.project_name for d in pkg_resources.working_set]
    print(installed_packages)
    sys.exit(1)

load_dotenv()
API_KEY = os.getenv("KOBO_KEY")

if not API_KEY:
    print("❌ KOBO_KEY environment variable not found")
    sys.exit(1)

print("🚀 Starting smoke test...")

try:
    client = Kobo(token=API_KEY)

    # Test asset listing - this should work with both old and new API
    uid_mapping = client.list_uid()
    print(f"✅ Found {len(uid_mapping)} assets")

    # Check if test survey exists
    if 'simple' not in uid_mapping:
        print("❌ Test survey 'simple' not found in assets")
        print("Available assets:", list(uid_mapping.keys())[:5])  # Show first 5
        sys.exit(1)

    survey_uid = uid_mapping['simple']
    print(f"✅ Found test survey with UID: {survey_uid}")

    # Test asset retrieval
    asset = client.get_asset(survey_uid)
    print("✅ Asset retrieved successfully")

    # Test structure extraction
    questions = client.get_questions(asset)
    choices = client.get_choices(asset)
    print("✅ Questions and choices extracted successfully")

    # Test data retrieval
    data = client.get_data(survey_uid)
    submissions_count = len(data.get('results', []))
    print(f"✅ Data retrieved successfully - {submissions_count} submissions")

    # Save to JSON files for inspection
    with open('questions.json', 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    with open('choices.json', 'w', encoding='utf-8') as f:
        json.dump(choices, f, indent=2, ensure_ascii=False)

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with open('survey.json', 'w', encoding='utf-8') as f:
        json.dump(asset, f, indent=2, ensure_ascii=False)

    print("✅ Smoke test completed - JSON files generated")
    print("📋 Generated files: questions.json, choices.json, data.json, survey.json")

    # Test DataFrame functionality if there are submissions
    if submissions_count > 0:
        print("🔄 Testing DataFrame functionality...")
        try:
            dataframes = client.data_to_dataframes(survey_uid)
            print(f"✅ Generated {len(dataframes)} DataFrames")
            for i, df in enumerate(dataframes):
                print(f"   DataFrame {i}: {df.shape}")
            print("🔄 You can now run export.py to test Excel export functionality")
        except Exception as e:
            print(f"⚠️  DataFrame functionality test failed: {e}")
            print("   This might be due to complex nested structures - manual review needed")
    else:
        print("ℹ️  No submissions found - skipping DataFrame test")

except Exception as e:
    print(f"❌ Smoke test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
