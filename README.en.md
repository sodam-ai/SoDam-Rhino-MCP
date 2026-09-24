# SoDam Rhino Offline MCP — English user guide

[한국어 Markdown](README.md) · [한국어 HTML](README.html) · [English HTML](README.en.html)

> **At a glance:** This Windows local tool turns a JSON specification of building components, positions and sizes into a <code>.3dm</code> file containing separately named meshes, then reopens the file for inspection. Neither Rhino nor a Rhino license is required. A photograph alone cannot automatically yield an accurate 3D building, and this project does not reproduce every Rhino feature.

This guide describes **the code currently in this folder**. Each step explains what to click or type for a first-time computer user. Unless stated otherwise, run commands in **Windows PowerShell** while the project root folder is open. Documentation baseline: 2026-09-25.

## Contents

1. [Terms and supported scope](#terms-and-supported-scope)
2. [Prerequisites and downloads](#prerequisites-and-downloads)
3. [Folder check and quick start](#folder-check-and-quick-start)
4. [Install in Codex or Claude Code](#install-in-codex-or-claude-code)
5. [Run and use the project](#run-and-use-the-project)
6. [Command reference](#command-reference)
7. [Working with photographic evidence](#working-with-photographic-evidence)
8. [Render and import with Blender](#render-and-import-with-blender)
9. [Workflow and architecture](#workflow-and-architecture)
10. [Security and data flow](#security-and-data-flow)
11. [File and document locations](#file-and-document-locations)
12. [Tests and current verification status](#tests-and-current-verification-status)
13. [Update summary](#update-summary)
14. [Troubleshooting](#troubleshooting)
15. [Frequently asked questions](#frequently-asked-questions)
16. [Copyright, licenses and commercial use](#copyright-licenses-and-commercial-use)

## Terms and supported scope

- **JSON:** A text file describing each building component's name, kind, position, size, color and evidence. You can start by copying the [example](examples/small_house.json).
- **3DM:** A Rhino-family file format. This project writes it with the <code>rhino3dm</code> library without launching Rhino. Saved objects have names, layers, colors and their source control values.
- **MCP:** A connection that lets an AI host such as Codex or Claude Code call tools in a local program. A **skill** instructs the AI on the workflow; this project's MCP server creates the files.
- **Blender:** A free 3D application. It is not needed for basic 3DM generation, but it is needed for two material renders, an editable <code>.blend</code> scene, or importing an existing Blender scene.
- **Inspection image:** An orthographic PNG made from the saved 3DM meshes. It is different from a Blender render and does not prove a match with a photograph.

The JSON route supports four component kinds: <code>box</code>, <code>wall_opening</code>, <code>gable_roof</code> and <code>cylinder</code>. It supports writing and reopening 3DM files, revising one component into a new file, two inspection PNG views, recording and auditing photographic evidence, and optional Blender round trips. More complex mesh forms can come from a trusted Blender scene.

**Not supported:** determining hidden surfaces or absolute dimensions accurately from a single photograph; automatic photograph-to-camera registration; controlling Rhino's UI; Rhino-native NURBS/Boolean/solid editing; named Rhino views saved into 3DM; or structural, code-compliance and construction approval. A 3DM imported from Blender is a mesh and does not preserve all <code>.blend</code> editing history, cameras, lights or node materials. See the [feature comparison](PARITY.md).

The upstream [Rhino Architectural Reverse Modeling](https://github.com/frankee0920-rgb/rhino-architectural-reverse-modeling) repository is a Codex/Claude Code **skill**, not a bundled Rhino MCP server. This project uses its principles of separating evidence, reopening deliverables and checking two views, but implements a separate runtime. The skill-folder installation pattern is similar; **the operation and features are not identical**. See the [upstream analysis](ANALYSIS.md).

## Prerequisites and downloads

| Item | When needed | Source and check |
|---|---|---|
| Windows PC and PowerShell | To run these commands | Search for “PowerShell” in the Start menu. This Windows launcher cannot be installed and run directly on a phone. |
| The complete project folder | Always | Obtain a trusted copy of this current project folder. When public, use <code>Code → Download ZIP</code> at [this project repository](https://github.com/sodam-ai/SoDam-Rhino-MCP), or clone it with Git. Access requires permission while the repository is private. The upstream URL is not this program’s download. |
| Python **3.12** and the <code>py</code> command | Always | Select a 3.12 installer from the [official Python Windows downloads](https://www.python.org/downloads/windows/). After installation, run <code>py -3.12 --version</code> in PowerShell. You do not need to replace another Python version. |
| Internet access | On first Python package installation | Do not assume a copied <code>.venv</code> from another PC will work. Recreate it for that PC. |
| Codex CLI or Claude Code | Only for AI chat with the skill and MCP | Follow the official [Codex guidance](https://developers.openai.com/codex/cli/) or [Claude Code guidance](https://code.claude.com/docs/en/setup), and install/sign in. **Neither is needed for CLI-only use.** The AI host itself may require network access and an account. |
| Blender **4.2, 4.3, 4.5 or 5.2**, as tested | Only for two renders, <code>.blend</code>, or Blender scene import | Choose the needed version from [Blender's official previous-version downloads](https://www.blender.org/download/previous-versions/). Installed Blender 4.2.16 LTS, 4.3.2, 4.5.13 LTS and 5.2.1 LTS passed actual MCP render and BLEND-to-3DM round trips on this PC. Other versions need separate testing. |

The required Python package versions are pinned in [requirements.txt](requirements.txt): <code>rhino3dm 8.35.0</code>, <code>mcp 1.30.0</code>, <code>Pillow 11.3.0</code> and <code>numpy 2.3.3</code>. Test tools are listed separately in [requirements-dev.txt](requirements-dev.txt). Rhino and a Rhino license are not installation prerequisites.

## Folder check and quick start

1. Open the downloaded project folder in File Explorer. Confirm that <code>README.md</code> and <code>requirements.txt</code> are visible at its top level.
2. Type <code>powershell</code> in the Explorer address bar and press Enter. PowerShell opens in this folder.
3. Enter these commands **one line at a time**. The first install and package download run only if the virtual environment (<code>.venv</code>) is absent. Existing environments and program versions are not automatically upgraded.

~~~powershell
Get-Location
py -3.12 --version
if (-not (Test-Path .\.venv\Scripts\python.exe)) { py -3.12 -m venv .venv; & .\.venv\Scripts\python.exe -m pip install -r requirements.txt }
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli build .\examples\small_house.json .\workspace\small_house.3dm
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli inspect .\workspace\small_house.3dm
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli render .\workspace\small_house.3dm .\workspace\main.png
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli render .\workspace\small_house.3dm .\workspace\secondary.png --azimuth 135
~~~

On success, <code>workspace</code> contains <code>small_house.3dm</code>, <code>main.png</code> and <code>secondary.png</code>. Double-click both PNGs in Explorer to inspect their actual contents. <code>inspect</code> rereads object names, layers, units and bounds from the saved file. **An existing output name is never overwritten**: choose a new name such as <code>small_house_v2.3dm</code> instead of deleting your old work.

If this project already has a compatible <code>.venv</code>, you need not recreate it. The installer does not silently upgrade a copied environment from another PC or mismatched package versions.

## Install in Codex or Claude Code

**Skip this section for CLI-only use.** Installing in an AI host makes the skill folder and local MCP connection available together. Install into **this project folder**, not a newly invented folder. The installer refuses to overwrite a different existing skill or MCP entry. Inspect the planned result with <code>--dry-run</code> first.

~~~powershell
py -3.12 .\scripts\install_skill.py --host codex --project . --dry-run
py -3.12 .\scripts\install_skill.py --host codex --project .
& .\.venv\Scripts\python.exe .\scripts\verify_installation.py --host codex
~~~

For Claude Code, change <code>--host codex</code> to <code>--host claude</code> in both the installation and verification commands. Sign in to Claude Code first and approve the project MCP request. On this PC, **Claude Code was signed out, so real host verification failed**. The installer's <code>mcp_status: ready</code> confirms configuration only; it does not prove sign-in, tool approval or a successful call.

The Codex skill goes in <code>.agents/skills/sodam-rhino-architectural-modeling/</code>; the Claude Code skill goes in <code>.claude/skills/sodam-rhino-architectural-modeling/</code>. Open a new host session and explicitly request <code>get_architectural_workspace</code> to prove the connection. Noninteractive Codex acceptance on this PC needed the <code>--approve-for-me</code> tool-approval setting. A <code>.mcp.json</code> or global MCP registration containing another PC's absolute path will not work: after moving this folder, inspect the path before running the installer, rather than blindly replacing existing entries.

## Run and use the project

**With the CLI:** Record reliable dimensions from your photograph or brief, then copy the [example JSON](examples/small_house.json). In a text editor, change <code>origin</code> (starting position), <code>size</code> and <code>name</code> in a newly named file. Run <code>build</code> for a new 3DM, <code>inspect</code> to reopen it, and <code>render</code> twice from different directions. The example JSON uses <code>units: meters</code>. Every new JSON spec must explicitly set <code>units</code> to <code>meters</code>, <code>millimeters</code>, <code>centimeters</code> or <code>feet</code>. The <code>z</code> axis points up.

**Through an AI host:** Open Codex or Claude Code for this project and ask: “Use the installed <code>sodam-rhino-architectural-modeling</code> skill and <code>sodam-rhino-offline</code> MCP. Check the workspace, distinguish known dimensions from assumptions, then make a new 3DM and primary/complementary images under new filenames.” The AI should call <code>get_architectural_workspace</code> first. Review the generated spec and images yourself. A photograph alone does not establish accurate measurements.

**To change an existing component:** Pass the original JSON filename, exact component name, complete replacement component JSON and a new output JSON filename to the <code>revise_architectural_spec</code> MCP tool; then build a new 3DM. A photo-evidence spec is rejected by this shortcut, because its evidence must be reviewed again. Write a complete new spec and rerun the evidence audit instead.

## Command reference

These examples share the prefix <code>& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli</code>. View all commands with <code>&amp; .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli --help</code>, and build options with <code>&amp; .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli build --help</code>.

| Command | Input → result | Example after the common prefix |
|---|---|---|
| <code>build</code> | JSON → new 3DM | <code>build .\examples\small_house.json .\workspace\house.3dm</code> |
| <code>inspect</code> | 3DM → object/layer/bounds report | <code>inspect .\workspace\house.3dm</code> |
| <code>render</code> | 3DM → inspection PNG | <code>render .\workspace\house.3dm .\workspace\main.png --azimuth 315 --elevation 28</code> |
| <code>render-blender</code> | 3DM → two rendered PNGs + <code>scene.blend</code> | <code>render-blender .\workspace\house.3dm .\workspace\blender_output --blender-exe "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"</code> |
| <code>import-blend</code> | Trusted <code>.blend</code> → mesh 3DM | <code>import-blend .\workspace\source.blend .\workspace\source.3dm --blender-exe "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"</code> |
| <code>prepare-reference</code> | Reference image and known dimensions → evidence packet JSON | See the photographic evidence steps below |
| <code>draft-evidence</code> | Spec and packet → numeric provenance draft | See below |
| <code>audit-evidence</code> | Check hashes and numeric provenance | See below |
| <code>build-verified</code> | Auditable spec → new 3DM | See below |

Use <code>--front-azimuth</code>, <code>--front-elevation</code>, <code>--rear-azimuth</code> and <code>--rear-elevation</code> to aim the Blender cameras. Defaults are 315°/28° and 135°/28°. Directions less than 10° apart are rejected. For <code>import-blend</code>, use <code>--meters-per-unit</code> when you know the scale of a scene without physical units. Otherwise the project explicitly assumes **1 Blender unit = 1 meter**.

The MCP server exposes 12 tools: <code>get_architectural_workspace</code>, <code>write_architectural_spec</code>, <code>revise_architectural_spec</code>, <code>build_architectural_model</code>, <code>inspect_architectural_model</code>, <code>render_architectural_view</code>, <code>render_blender_model</code>, <code>import_blender_scene</code>, <code>prepare_architectural_reference</code>, <code>draft_architectural_evidence</code>, <code>audit_architectural_evidence</code> and <code>build_verified_architectural_model</code>. Follow the host's tool description for exact arguments.

## Working with photographic evidence

Keep the original photograph and separate known dimensions from estimates. For example, “10 m” on a plan can be <code>given</code>; a value read from a photo is <code>measured</code>; a hidden side guessed from context is <code>inferred</code>. These labels **do not guarantee accuracy**. The verified build stops when an image hash changes or required provenance is missing.

~~~powershell
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli prepare-reference .\workspace\reference.json .\workspace\photo.png --known facade_width=10 --units meters
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli draft-evidence .\workspace\spec.json .\workspace\reference.json .\workspace\spec_review.json
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli audit-evidence .\workspace\spec_review.json .\workspace\reference.json
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli build-verified .\workspace\spec_review.json .\workspace\reference.json .\workspace\verified.3dm
~~~

Put <code>photo.png</code> and a spec you created as <code>spec.json</code> in <code>workspace</code> first. The draft marks numeric values as inferred. Compare and correct them against the [source material](workspace/) before auditing. A <code>given</code> value must match the known dimension's name, value and units. An audit does not automatically detect perspective distortion, occlusion or incorrect facts entered by a person. The [synthetic sample benchmark](BENCHMARK.md) used no actual user reference photograph.

## Render and import with Blender

If Blender is installed, <code>render-blender</code> writes <code>front.png</code>, <code>rear.png</code> and <code>scene.blend</code> into a new output folder. It uses the saved 3DM meshes, with example lighting and simple materials. Two PNG files existing is not evidence that they match a reference photograph. Open them and inspect both views yourself.

For an existing Blender model, preserve the source <code>.blend</code> and run <code>import-blend</code>. It imports evaluated modifier meshes, names, layers and basic colors. Blender starts with <code>--factory-startup --disable-autoexec</code> to disable auto-run scripts, but **do not open an untrusted .blend**. Give the actual <code>blender.exe</code> path of the version you want to use with <code>--blender-exe</code>. The 4.5 path above is an example; you can replace it with an installed 4.2, 4.3 or 5.2 path. MCP uses <code>SODAM_BLENDER_EXE</code> or the default installed path.

## Workflow and architecture

~~~text
User photographs, brief and reliable dimensions
  → Human/AI separates facts, observations and assumptions
  → Writes/revises a JSON component specification
  → [Optional] Records photo hashes and numeric provenance; audits them
  → Python model engine + rhino3dm → saves named mesh components in 3DM
  → Reopens saved 3DM; checks objects, units and bounds
  → Makes orthographic PNG inspections from two directions
  → [Optional] a tested Blender version → two rendered PNGs and editable .blend source
  → [Optional] Source .blend meshes → new 3DM
~~~

<code>sodam_rhino_mcp/cli.py</code> and <code>server.py</code> call the same modeling engine. The server uses <code>stdio</code> (local process standard input/output between it and its host), not a separate website, database or login screen. The Windows launcher <code>start_mcp.cmd</code> uses this folder's <code>.venv</code> Python and default <code>workspace</code>. You may set <code>SODAM_RHINO_WORKSPACE</code> to change the MCP work folder. MCP file arguments accept only **simple filenames directly inside that folder**. The CLI accepts user-supplied paths; check them before running commands.

## Security and data flow

- **Local processing:** This project's modeling, 3DM readback and image generation run in local processes. Installing Python packages and using an AI host may need the internet and an account. Do not interpret the whole project as “fully offline AI.”
- **Storage:** MCP input/output defaults to <code>workspace/</code>. Photographs, JSON, 3DM, PNG and BLEND files can contain confidential designs. Check before sharing, backing up or syncing them to a cloud.
- **Boundaries:** MCP rejects filename requests that escape the workspace and refuses to overwrite existing results. Regression tests cover incomplete output after failures. These protections do not make all malicious files or host permission issues harmless.
- **Host permissions:** Codex/Claude Code control their own sign-in and MCP tool approval. This server has no user accounts, per-role permissions or network API. Do not give untrusted people access to the host or its work folder.
- **Secrets:** Do not put API keys, passwords or tokens in photo filenames, JSON, commands, chat or README files. On 2026-09-25, a scan of 1,849 files excluding <code>.venv</code>, <code>__pycache__</code> and <code>.git</code> found no checked high-confidence secret-key patterns in readable files. One existing 3DM was unreadable due to permissions; 22 BLEND files contained Windows-path-like data. Review each file before sharing. The scan does not prove the absence of every secret or personal detail.

## File and document locations

| Path | Meaning |
|---|---|
| <code>README.md</code> / <code>README.html</code> | Same Korean content in Markdown / browser-readable HTML |
| <code>README.en.md</code> / <code>README.en.html</code> | Same English content in Markdown / browser-readable HTML |
| <code>examples/small_house.json</code> | Quick-start building specification |
| <code>workspace/</code> | Default MCP input/output folder; inspect actual results |
| <code>skill/sodam-rhino-architectural-modeling/</code> | Source skill; <code>.agents/</code> and <code>.claude/</code> hold installed copies |
| <code>sodam_rhino_mcp/</code> | CLI, MCP server, 3DM generation and inspection code |
| <code>scripts/install_skill.py</code> / <code>scripts/verify_installation.py</code> | Installer and operational verifier |
| <code>requirements.txt</code> / <code>requirements-dev.txt</code> | Pinned runtime / test dependencies |
| <code>ANALYSIS.md</code> / <code>PARITY.md</code> / <code>BENCHMARK.md</code> | Upstream analysis / feature limits / synthetic sample evaluation |
| <code>UPSTREAM_LICENSE.txt</code> / <code>resources/</code> | Upstream MIT notice / imported references |
| <code>LICENSE</code> / <code>LICENSE-GPL-3.0.txt</code> / <code>NOTICE</code> / <code>NOTICE.md</code> | Apache 2.0 / Blender script GPL 3+ / attribution / rights and release checklist |
| <code>sodam_acceptance_20260924*</code> | Earlier synthetic sample artifacts, not proof of quality against a user's photos |

## Tests and current verification status

~~~powershell
& .\.venv\Scripts\python.exe .\scripts\verify_installation.py --host codex
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\ruff.exe check .
& .\.venv\Scripts\mypy.exe sodam_rhino_mcp
& .\.venv\Scripts\python.exe .\scripts\smoke_mcp.py
~~~

On this PC on 2026-09-25, Blender 4.2.16, 4.3.2, 4.5.13 and 5.2.1 each passed **real MCP requests** for JSON-to-3DM creation, two Blender views, BLEND save and 3DM re-import. Codex registration, MCP tool discovery, model readback, evidence audit, PNG workflow, 46 unit tests, Python compilation and dependency checks also passed. The existing 5.2 PNG pair decoded at 1200×800 and differed. A temporary 500-box build/readback sample completed.

**Current static checks:** Full Ruff passes, mypy passes on ten core source files, 46 unit tests pass, and real MCP transport, 3DM creation and inspection pass. <code>typings/rhino3dm/</code> corrects the installed rhino3dm 8.35.0 typing declarations for the API surface used here.

**Unverified:** Claude Code is signed out on this PC, so operation through that host remains unverified. Visual render quality, accuracy against real user photographs, editing the 3DM in an independent application, other PCs and untested Blender versions remain unchecked. [NOTICE.md](NOTICE.md) describes path and metadata risks in generated assets. This local CLI/MCP has no browser UI, mobile layout, database or built-in login.

## Update summary

<details>
<summary>Expand: major changes through the current implementation and their verification status</summary>
<ul>
<li>A local MCP/CLI engine now writes and reopens 3DM files without launching Rhino, replacing a skill-only workflow.</li>
<li>JSON parts cover boxes, opening walls, gable roofs and cylindrical columns, preserving names, layers, evidence and source control values.</li>
<li>New-file component revisions, photo-hash/dimension provenance audits, two PNG inspection views, Blender rendering and BLEND import were added.</li>
<li>Regression tests cover path escapes, overwrite refusal, invalid input, partial outputs and installation conflicts.</li>
<li>Claude sign-in and MCP connection are checked separately. Signed-out Claude still fails on this PC.</li>
<li>Real MCP round trips passed on Blender 4.2, 4.3, 4.5 and 5.2. Current Ruff and mypy checks pass; signed-out Claude, real-photo accuracy and complete Rhino parity remain unverified. PARITY.md has details.</li>
</ul>
</details>

## Troubleshooting

| Symptom | Check and response |
|---|---|
| <code>py -3.12</code> not found | Install Python 3.12 and check <code>py -3.12 --version</code>. Do not quietly substitute another version. |
| <code>.venv\Scripts\python.exe</code> missing | Confirm the project root with <code>Get-Location</code>; run the venv/package steps under Quick Start. |
| Package versions differ | Check the pinned <code>requirements.txt</code>. The installer does not silently upgrade existing environments. |
| <code>refusing to overwrite</code> | Choose a new output name, such as <code>_v2</code>. Do not delete earlier work just to make the check pass. |
| JSON invalid or 3DM not created | Compare <code>units</code>, unique names, positive sizes and opening bounds with the example. Run <code>inspect</code> after a successful <code>build</code>. |
| MCP tools not visible | Run installer <code>--dry-run</code>, start a new host session, approve MCP, then run <code>verify_installation.py</code>. Configuration <code>ready</code> alone is not proof of use. |
| Claude Code verification fails | Check Claude sign-in and project MCP approval. Signed-out status currently fails the verifier. |
| Blender missing or rendering fails | Provide the real <code>blender.exe</code> of a tested version with <code>--blender-exe</code> or <code>SODAM_BLENDER_EXE</code>. Check that all three output files exist. |
| Wrong model scale | Inspect JSON <code>units</code> and Blender scene units, and <code>--meters-per-unit</code> if needed. Do not infer absolute size from a photo alone. |
| Files appear in the wrong folder | Check MCP <code>get_architectural_workspace</code> and <code>SODAM_RHINO_WORKSPACE</code>. The CLI uses the paths typed in its command. |
| Ruff or mypy fails | Install the pinned development dependencies and rerun the commands above. The corrected declarations in <code>typings/rhino3dm/</code> target rhino3dm 8.35.0; do not silently replace the SDK. |

## Frequently asked questions

**Q. Can I really use the supported workflow without a Rhino license?**

A. Yes. The supported JSON-to-mesh-3DM and inspection route does not launch Rhino. Blender features need Blender. This is not equivalent to Rhino-native editing.

**Q. Will one uploaded photograph automatically yield the same building?**

A. No. A photo does not settle hidden surfaces or absolute dimensions. A person must distinguish facts, measurements and assumptions and inspect the result.

**Q. Must I install Codex or Claude Code?**

A. No. The CLI can run alone. Calling tools through AI chat requires the host, its account and tool approval.

**Q. How do inspection and Blender PNGs differ?**

A. The first is a fast orthographic image of saved meshes; the second is rendered by Blender with simple materials and lighting. Neither proves a match with a photograph.

**Q. Can I edit existing files?**

A. Edit the source JSON and regenerate a 3DM **under a new name**. Overwriting prior results is refused. This is not free-form NURBS editing.

**Q. Can this run on a phone or as a website?**

A. The current product is a Windows local CLI/MCP, without a mobile app or web service. HTML README files are just browser-readable guides.

**Q. Can I distribute or sell it commercially?**

A. Project-authored code and documentation are offered under Apache License 2.0; four Blender API scripts are GPL-3.0-or-later. Imported MIT material and external assets keep their own terms. Check rights to photographs, plans, models and client data separately.

## Copyright, licenses and commercial use

1. **Project-authored code and documentation:** The copyright notice is <code>Copyright 2026 SoDam AI Studio</code>. [LICENSE](LICENSE) contains Apache License, Version 2.0. It permits use, modification, copying, redistribution, sale, hosted services, teaching and client delivery, subject to preserving the license and applicable copyright, change and NOTICE information when redistributing. It includes warranty disclaimer and liability limitations. It grants no trademark or input-asset rights.
2. **Blender API script exception:** <code>scripts/blender_scene.py</code>, <code>scripts/export_blend_mesh.py</code>, <code>scripts/create_blend_fixture.py</code> and <code>scripts/benchmark_reference_blender.py</code> directly use <code>bpy</code>. These four files are separately offered under GNU GPL version 3 or later; see [LICENSE-GPL-3.0.txt](LICENSE-GPL-3.0.txt). Sharing, selling or delivering them requires providing the relevant source and GPL terms. This follows [Blender’s official guidance](https://www.blender.org/about/license/); professional legal review may be needed for the scope when combining or redistributing software. Blender itself is not bundled.
3. **Imported upstream material:** Imported material from the [upstream repository](https://github.com/frankee0920-rgb/rhino-architectural-reverse-modeling) retains its MIT license and <code>Copyright (c) 2026 frank</code> in [UPSTREAM_LICENSE.txt](UPSTREAM_LICENSE.txt). Preserve its copyright, permission and disclaimer notices when copying, modifying, redistributing or using it commercially. [NOTICE](NOTICE) distinguishes the scopes.
4. **External dependencies and user assets:** Consult [McNeel’s notice](https://developer.rhino3d.com/license/) for the <code>rhino3dm</code> SDK. Python packages, Blender, photos, plans, 3D models, fonts, images, icons, trademarks, AI-generated material, external APIs and models have separate terms. This repository’s licenses do not grant their rights. Never add client data, personal information or confidential material to public examples.
5. **In plain language:** You can test locally with materials you own. For copying, modifying, forking, redistributing, commercial services, teaching or client delivery, follow the applicable three licenses above and check input rights, contracts, API pricing and service terms yourself. It can write 3DM without a Rhino license, but does not guarantee Rhino feature parity, geometric accuracy or suitability for design.

This is general information based on inspected files and official guidance. **It is for reference, has no guaranteed legal effect, and users should obtain qualified legal advice before acting.**
