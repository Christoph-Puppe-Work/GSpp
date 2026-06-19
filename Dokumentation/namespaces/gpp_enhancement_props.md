# Grundschutz++ Enhancement Property Namespace

This file is the OSCAL property **naming-system identifier** (`ns`) for the custom properties
that the `Gpp-ai-tool` ED2023 enhancement stage (`stage_ED23_profiles_enhanced`) attaches to each
maturity-level `statement` part of an *enhanced* OSCAL profile.

**Namespace URI** (use verbatim as the prop `ns`):

```
https://github.com/NTT-Data-Deutschland-SE/Grundschutz-Plus-Plus-Tools/tree/main/Dokumentation/namespaces/gpp_enhancement_props.md
```

These properties are **not** defined by OSCAL (whose namespace `http://csrc.nist.gov/ns/oscal` is
reserved for OSCAL-defined names) and are **not** part of the BSI Stand-der-Technik-Bibliothek
namespaces, so they carry this dedicated namespace to avoid collisions — the same `ns`-per-naming-system
convention the BSI catalogs use for `modal_verbs.csv`, `security_level.csv`, etc.

## Properties

| prop `name`      | meaning                                                       | allowed values |
|------------------|--------------------------------------------------------------|----------------|
| `control_class`  | Functional class of the control (NIST-style)                 | `Technical`, `Operational`, `Management` |
| `phase`          | ISMS lifecycle phase the control primarily applies to        | `Initiation`, `Risk Assessment`, `Risk Treatment`, `Implementation`, `Operation`, `Audit`, `Improvement` |
| `effective_on_c` | Impact on **Confidentiality** when the control is effective  | `high`, `medium`, `low` |
| `effective_on_i` | Impact on **Integrity** when the control is effective        | `high`, `medium`, `low` |
| `effective_on_a` | Impact on **Availability** when the control is effective     | `high`, `medium`, `low` |

The maturity level itself is carried by the **standard OSCAL `label` property** (`m1` … `m5`, no
custom `ns`) on the same `statement` part, and is therefore intentionally not listed here.

The allowed values above are enforced by the AI response schema
`Gpp-ai-tool/src/assets/schemas/enhanced_control_response_schema.json`.
