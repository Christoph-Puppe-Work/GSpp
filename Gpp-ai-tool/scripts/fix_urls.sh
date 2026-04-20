#!/bin/bash

# Finde alle regulären Dateien ab dem aktuellen Verzeichnis.
# Schließe den .git Ordner aus, um das Repository nicht zu korrumpieren.
find . -type d -name ".git" -prune -o -type f -exec sed -i \
    -e 's|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/Gpp-ai-tool|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/Gpp-ai-tool|g' \
    -e 's|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/One-Page-Apps|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/One-Page-Apps|g' \
    -e 's|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/zielobjektkategorien|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/zielobjektkategorien|g' \
    -e 's|https://api.github.com/repos/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/contents/zielobjektkategorien|https://api.github.com/repos/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/contents/zielobjektkategorien|g' \
    -e 's|https://raw.githubusercontent.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/refs/heads/main/zielobjektkategorien|https://raw.githubusercontent.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/refs/heads/main/zielobjektkategorien|g' \
    -e 's|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/blob/main/beispiel-kataloge/dsgvo_oscal_catalog.json|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/blob/main/beispiel-kataloge/dsgvo_oscal_catalog.json|g' \
    -e 's|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/blob/main/beispiel-kataloge/kritis_oscal_catalog.json|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/blob/main/beispiel-kataloge/kritis_oscal_catalog.json|g' \
    -e 's|https://raw.githubusercontent.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/refs/heads/main/beispiel-kataloge/dsgvo_oscal_catalog.json|https://raw.githubusercontent.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/refs/heads/main/beispiel-kataloge/dsgvo_oscal_catalog.json|g' \
    -e 's|https://raw.githubusercontent.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/refs/heads/main/beispiel-kataloge/kritis_oscal_catalog.json|https://raw.githubusercontent.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/refs/heads/main/beispiel-kataloge/kritis_oscal_catalog.json|g' \
    -e 's|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/hilfsdateien|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/hilfsdateien|g' \
    -e 's|https://raw.githubusercontent.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/refs/heads/main/hilfsdateien|https://raw.githubusercontent.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/refs/heads/main/hilfsdateien|g' \
    -e 's|https://api.github.com/repos/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/contents|https://api.github.com/repos/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/contents|g' \
    -e 's|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/issues|https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/issues|g' \
    -e 's|https://raw.githubusercontent.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/refs/heads/main|https://raw.githubusercontent.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/refs/heads/main|g' \
    -e 's|https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/refs/heads/main/Anwenderkataloge/Grundschutz%2B%2B/Grundschutz%2B%2B-catalog.json|https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/refs/heads/main/Anwenderkataloge/Grundschutz%2B%2B/Grundschutz%2B%2B-catalog.json|g' \
    -e 's|NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools|NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools|g' {} +

echo "Ersetzungen erfolgreich abgeschlossen."
