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

client = Kobo(token=API_KEY)
survey_uid = client.list_uid()['EUT_TEST_2']
asset = client.get_asset(survey_uid)
questions = client.get_questions(asset)
choices = client.get_choices(asset)
data = client.get_data(survey_uid)

# Save to JSON files
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
print("🔄 You can now run export.py to test the DataFrame functionality")
