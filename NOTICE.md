# Rights and release checklist / 권리·배포 점검표

This document records observed files and remaining checks. It is not a substitute for the license texts or legal advice. 이 문서는 확인한 파일과 남은 점검 사항을 기록하며 라이선스 원문이나 법률 자문을 대신하지 않습니다.

## License boundaries / 라이선스 적용 범위

| Material / 자료 | Governing notice / 적용 고지 | Practical obligation / 실무상 의무 |
|---|---|---|
| Project-authored code and documentation / 프로젝트 자체 코드·문서 | [Apache License, Version 2.0](LICENSE), Copyright 2026 SoDam AI Studio | Preserve license, applicable attribution, change and NOTICE notices on redistribution. 재배포 시 관련 고지를 보존합니다. |
| Four scripts directly importing Blender <code>bpy</code> / Blender API 스크립트 4개 | [GNU GPL version 3 or later](LICENSE-GPL-3.0.txt): <code>scripts/blender_scene.py</code>, <code>scripts/export_blend_mesh.py</code>, <code>scripts/create_blend_fixture.py</code>, <code>scripts/benchmark_reference_blender.py</code> | Provide GPL terms and corresponding source when sharing or delivering. 공유·납품 시 GPL 조건과 해당 소스를 제공합니다. See [Blender's official guidance](https://www.blender.org/about/license/). |
| Imported upstream material / 원본에서 가져온 자료 | [MIT notice](UPSTREAM_LICENSE.txt), Copyright (c) 2026 frank | Retain the copyright, permission and disclaimer text with copied/substantial portions. 복제본·상당 부분에 원본 고지를 유지합니다. |
| Third-party dependencies / 외부 패키지 | Their own licenses / 각 패키지의 별도 라이선스 | Recheck the exact shipped package and notices, especially if bundling binaries. 실제 배포물 기준으로 다시 확인합니다. |
| User inputs and generated assets / 사용자 입력·생성물 | Separate rights of owners and licensors / 별도 권리 | Confirm source, consent, commercial use and metadata before publication or client delivery. 공개·납품 전 출처·동의·상업 이용·메타데이터를 확인합니다. |

The root [NOTICE](NOTICE) is an attribution notice. This checklist does not alter any license. 최상위 NOTICE는 저작권 고지이며 이 점검표는 라이선스 조건을 변경하지 않습니다.

## Dependency and material audit / 의존성·자료 점검

Pinned runtime packages in [requirements.txt](requirements.txt) are rhino3dm 8.35.0, mcp 1.30.0, Pillow 11.3.0 and numpy 2.3.3. Development tools in [requirements-dev.txt](requirements-dev.txt) are mypy 1.18.2 and ruff 0.16.2. On 2026-09-26, metadata for 38 distributions in the local virtual environment was checked. The direct runtime packages report MIT (<code>rhino3dm</code> and <code>mcp</code>) and MIT-CMU (<code>Pillow</code>); <code>numpy</code> carries a bundled license file covering BSD-family and third-party/native components, including a GCC runtime exception notice. Transitive metadata also includes MPL-2.0 (<code>certifi</code>) and Apache-2.0/BSD dual licensing (<code>cryptography</code>). <code>pathspec</code> has a bundled license file even though its top-level license metadata is empty. This metadata check does not clear any future wheel, binary bundle or distribution method. 2026-09-26 로컬 가상 환경의 38개 패키지 메타데이터를 확인했습니다. 재배포 전 실제 포함할 파일의 라이선스 전문·고지·소스 제공 의무를 다시 확인해야 합니다.

The repository does not bundle Rhino or Blender executables. It may invoke a separately installed Blender for optional rendering/import. Git-tracked files contain no PNG, BLEND, 3DM, font, audio or video assets; local acceptance outputs are ignored. User-supplied photographs, plans, marks, fonts, models, prompts and AI-generated work are not cleared by this project's license. Before shipping generated PNG/BLEND/3DM assets, inspect provenance, permission, similarity, personal data and embedded metadata. Rhino나 Blender 실행 파일은 동봉하지 않으며, 사용자 제공 자료와 AI 생성물의 권리·메타데이터는 배포 전에 별도로 확인해야 합니다.

## Before publishing a release or client deliverable / 공개·납품 전 확인

1. Verify the rights holder of every new code/document/asset and the applicability of the three notices above. 새로운 코드·문서·자료의 권리자와 위 세 고지의 적용 범위를 확인합니다.
2. Check the exact Git staged file list. Exclude <code>.mcp.json</code>, <code>.venv/</code>, <code>workspace/</code>, root <code>sodam_acceptance_*</code>, caches and <code>CHECKPOINT.md</code>. Never commit keys, tokens, private paths, credentials, personal or client data. 정확한 Git 등록 파일 목록을 확인하고 로컬 설정·산출물·캐시·체크포인트·민감정보를 제외합니다.
3. Inspect any example or output that will actually ship, including image metadata and embedded paths in BLEND/3DM. A previous local scan found Windows-path-like bytes in BLEND files and metadata keys in PNGs; these local outputs are excluded by default. 공개할 예제·산출물의 화면 내용·메타데이터·내장 경로를 별도 확인합니다.
4. Run unit, integration, lint, type and dependency checks on the final staged tree. Do not equate a successful unit test with visual render quality, full Rhino parity or a working signed-out Claude host. 최종 등록본에서 테스트를 재실행하고 품질·동등성·호스트 로그인 상태를 별개로 판단합니다.
5. For commercialization or client delivery, review customer contracts, inputs, external services/API plans, Blender script GPL source obligations, local law and notices with qualified counsel where needed. 상업 이용·납품 전 계약·입력 자료·외부 서비스·GPL 소스 제공·적용 법률을 전문가와 검토합니다.

**Unverified / 미확인:** Actual ownership of independently authored assets; redistribution terms of every possible package/binary; visual quality and likeness to real photographs; client-specific contracts and jurisdiction. These are not guaranteed by this checklist. 자체 생성 자산의 권리, 모든 가능한 패키지의 재배포 조건, 실제 사진 일치성, 고객 계약·관할 법률은 이 문서만으로 보증하지 않습니다.

**참고용·법적 효력 보장 안 함, 사용자 책임·변호사 확인 권장.**
