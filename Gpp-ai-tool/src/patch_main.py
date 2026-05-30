import re

with open('Gpp-ai-tool/src/main.py', 'r') as f:
    content = f.read()

# Add import
content = content.replace(
    "from pipeline import stage_strip, stage_ED23_profiles_enhanced, stage_gpp, stage_match_bausteine, stage_profiles, processing",
    "from pipeline import stage_strip, stage_ED23_profiles_enhanced, stage_base_process_enhanced, stage_gpp, stage_match_bausteine, stage_profiles, processing"
)

# Add choices
content = content.replace(
    'choices=["stage_gpp", "stage_match_bausteine", "stage_strip", "stage_profiles", "stage_ED23_profiles_enhanced"],',
    'choices=["stage_gpp", "stage_match_bausteine", "stage_strip", "stage_profiles", "stage_ED23_profiles_enhanced", "stage_base_process_enhanced"],'
)

# Add to if/elif block
replacement = """        elif args.stage == "stage_ED23_profiles_enhanced":
            await stage_ED23_profiles_enhanced.run_stage_ED23_profiles_enhanced()
        elif args.stage == "stage_base_process_enhanced":
            await stage_base_process_enhanced.run_stage_base_process_enhanced()"""
content = content.replace(
    """        elif args.stage == "stage_ED23_profiles_enhanced":
            await stage_ED23_profiles_enhanced.run_stage_ED23_profiles_enhanced()""",
    replacement
)

with open('Gpp-ai-tool/src/main.py', 'w') as f:
    f.write(content)
