"""Test for KoboAPI DataFrame export functionality."""

import os
import sys
import json
from dotenv import load_dotenv

try:
    from koboapi import Kobo
    print("✅ koboapi imported successfully")
except ImportError as e:
    print(f"❌ Failed to import koboapi: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("KOBO_KEY")

if not API_KEY:
    print("❌ KOBO_KEY environment variable not found")
    sys.exit(1)

def test_export_functionality():
    """Test the export functionality with real KoBo data."""
    print("🚀 Starting export test...")

    try:
        # Initialize Kobo client
        client = Kobo(token=API_KEY, debug=True)

        # Get survey UID (adjust this to your survey)
        surveys = client.list_uid()
        if 'simple' not in surveys:
            print("❌ simple survey not found in your account")
            print("Available surveys:")
            for name, uid in surveys.items():
                print(f"  - {name}: {uid}")
            return False

        survey_uid = surveys['simple']
        print(f"📋 Using survey: {survey_uid}")

        # Method 1: Get DataFrames using new API
        print("\n1️⃣ Testing DataFrame generation...")
        dataframes = client.data_to_dataframes(survey_uid)

        print(f"✅ Generated {len(dataframes)} DataFrames")
        df_names = ['General/Main', 'Hogar', 'Individuo']

        for i, df in enumerate(dataframes):
            name = df_names[i] if i < len(df_names) else f"DataFrame {i+1}"
            print(f"  📊 {name}: {df.shape[0]} rows, {df.shape[1]} columns")

            # Show first few columns as sample
            sample_cols = list(df.columns)[:5]
            print(f"     Sample columns: {sample_cols}")

        # Method 2: Direct export to Excel using new API
        print("\n2️⃣ Testing Excel export...")
        output_file = 'test_export.xlsx'
        client.data_to_xlsx(survey_uid, output_file)

        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ Excel file created: {output_file} ({file_size} bytes)")
        else:
            print("❌ Excel file was not created")
            return False

        print("\n🎉 All tests passed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 KoboAPI Export Test Suite")
    print("=" * 50)

    # Test new API-based export
    api_success = test_export_functionality()



    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"  New API export: {'✅ PASS' if api_success else '❌ FAIL'}")
