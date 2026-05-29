I renamed and changed a lot, we need to adapt!

# zielobjektkategorien

we had them in

ZIELOBJEKTE_CSV_PATH = "os.path.join(REPO_ROOT, "Stand-der-Technik-Bibliothek/Dokumentation/namespaces/zielobjektkategorien.csv")"

but now we need to download them from https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek/blob/main/Dokumentation/namespaces/target_object_categories.csv

# Anwenderkatalog

Old: GPP_KOMPENDIUM_JSON_PATH = os.path.join(REPO_ROOT, "Stand-der-Technik-Bibliothek/Anwenderkataloge/Grundschutz++/Grundschutz++-catalog.json")


New: https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek/blob/main/Anwenderkataloge/Grundschutz%2B%2B/Grundschutz%2B%2B-catalog.json

# BSI Edition 2023

OLD: BSI_2023_JSON_PATH = os.path.join(REPO_ROOT, "ai_tool/src/assets/json/BSI_GS_OSCAL_current_2023_benutzerdefinierte_251121.json")

NEW: https://github.com/NTTDATA-DACH/BSI-GS-Benutzerdefinierte-Edition23-OSCAL/blob/main/BS_GK_OSCAL_JSON_DATA/BSI_GS_OSCAL_current_2023_benutzerdefinierte.json

# ai_tool renamed

Old: ai_tool
New: Gpp-ai-tool

