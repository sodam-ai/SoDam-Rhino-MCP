# SoDam Rhino Offline MCP — 한국어 사용 설명서

[English Markdown](README.en.md) · [한국어 HTML](README.html) · [English HTML](README.en.html)

> **한눈에 보기:** 이 프로젝트는 건물의 위치·크기·종류를 적은 JSON에서 구성요소별 메시(mesh)가 들어 있는 <code>.3dm</code> 파일을 만들고, 이를 다시 읽어 검수하는 Windows용 로컬 도구입니다. Rhino 설치나 Rhino 라이선스는 필요하지 않습니다. 사진만 넣으면 정확한 3D가 자동 완성되는 제품은 아니며, Rhino의 모든 기능을 복제하지도 않습니다.

이 문서는 **현재 이 폴더에 있는 코드**를 설명합니다. 처음 컴퓨터를 쓰는 사람도 따라갈 수 있도록 클릭할 위치와 명령의 의미를 함께 적었습니다. 명령은 별도 표시가 없으면 **Windows PowerShell**에서 프로젝트 최상위 폴더를 연 상태로 실행합니다. 설명 기준일: 2026-09-25.

## 목차

1. [먼저 알아둘 말과 지원 범위](#먼저-알아둘-말과-지원-범위)
2. [사전 준비물과 다운로드](#사전-준비물과-다운로드)
3. [폴더 확인과 빠른 시작](#폴더-확인과-빠른-시작)
4. [Codex 또는 Claude Code에 설치](#codex-또는-claude-code에-설치)
5. [실행과 실제 사용 순서](#실행과-실제-사용-순서)
6. [명령어 모음](#명령어-모음)
7. [사진 근거를 다루는 방법](#사진-근거를-다루는-방법)
8. [Blender로 렌더하고 가져오기](#blender로-렌더하고-가져오기)
9. [워크플로우와 아키텍처](#워크플로우와-아키텍처)
10. [보안과 데이터 흐름](#보안과-데이터-흐름)
11. [파일과 문서 위치](#파일과-문서-위치)
12. [테스트와 현재 확인 상태](#테스트와-현재-확인-상태)
13. [업데이트 내용](#업데이트-내용)
14. [문제·오류 대처](#문제오류-대처)
15. [자주 묻는 질문](#자주-묻는-질문)
16. [저작권·라이선스·상업적 이용](#저작권라이선스상업적-이용)

## 먼저 알아둘 말과 지원 범위

- **JSON:** 건물 부품의 이름, 종류, 위치, 크기, 색과 근거를 글자로 저장한 설계 입력 파일입니다. [예제](examples/small_house.json)를 복사해 시작할 수 있습니다.
- **3DM:** Rhino 계열 파일 형식입니다. 여기서는 Rhino를 실행하지 않고 <code>rhino3dm</code> 라이브러리로 작성합니다. 저장된 객체는 이름·레이어·색·입력 제어값을 가집니다.
- **MCP:** Codex나 Claude Code 같은 AI 호스트가 로컬 프로그램의 도구를 호출하는 연결 방식입니다. **스킬**은 AI에게 작업 절차를 알려주는 지침이고, 실제 파일 생성은 이 프로젝트의 MCP 서버가 수행합니다.
- **Blender:** 무료 3D 프로그램입니다. 기본 3DM 생성에는 필요하지 않지만 두 장의 재질 렌더와 편집 가능한 <code>.blend</code>, 기존 Blender 장면 가져오기에는 필요합니다.
- **검수도:** 저장한 3DM 메시에서 만든 직교 PNG입니다. Blender 렌더나 사진 일치 증명과 구별합니다.

지원하는 JSON 부품은 <code>box</code>(상자), <code>wall_opening</code>(개구부 벽), <code>gable_roof</code>(박공지붕), <code>cylinder</code>(원형 기둥) 네 가지입니다. 3DM 작성·재열기, 새 파일로 구성요소 수정, 두 시점 검수 PNG, 사진 근거 기록·감사, 선택적 Blender 왕복을 제공합니다. 복잡한 메시 형상은 신뢰할 수 있는 Blender 장면에서 가져올 수 있습니다.

**지원하지 않는 것:** 사진 한 장만으로 숨은 면·절대 치수를 정확히 알아내기, 자동 사진 카메라 맞춤, Rhino 화면 제어, Rhino 고유 NURBS/Boolean/솔리드 편집 기능, 3DM에 Rhino 이름 붙은 뷰 저장, 구조·법규·시공 적합성 판정. Blender에서 가져온 것은 메시이며 원본 <code>.blend</code>의 수정 이력·카메라·조명·노드 재질이 3DM에 그대로 보존되지는 않습니다. 자세한 대응표는 [PARITY.md](PARITY.md)에 있습니다.

원본 [Rhino Architectural Reverse Modeling](https://github.com/frankee0920-rgb/rhino-architectural-reverse-modeling)은 Codex/Claude Code **작업 스킬**이며 Rhino MCP 서버 자체를 포함하지 않습니다. 이 프로젝트는 그 증거 구분·재열기·두 시점 검수 원칙을 참고해 별도로 만든 실행 경로입니다. 원본과 설치 폴더 방식은 비슷하지만 **작동 방식과 기능이 동일하다는 뜻은 아닙니다.** [원본 분석](ANALYSIS.md)을 참고하세요.

## 사전 준비물과 다운로드

| 필요한 것 | 언제 필요한가 | 구하는 곳과 확인 방법 |
|---|---|---|
| Windows PC와 PowerShell | 이 문서의 명령 실행 | 시작 메뉴에서 “PowerShell” 검색. 모바일 기기에서는 이 Windows 실행기를 직접 설치·실행할 수 없습니다. |
| 이 프로젝트 폴더 전체 | 항상 | 현재 작업 폴더를 신뢰할 수 있는 경로로 복사해 받으세요. [이 프로젝트의 GitHub 저장소](https://github.com/sodam-ai/SoDam-Rhino-MCP)에서 공개 상태일 때 <code>Code → Download ZIP</code>을 눌러 받거나, 아래 Git 명령으로 복제하세요. 비공개 상태에서는 접근 권한이 필요합니다. 위 원본 GitHub 주소는 이 프로그램의 다운로드 주소가 아닙니다. |
| Python **3.12**와 <code>py</code> 명령 | 항상 | [Python 공식 Windows 다운로드](https://www.python.org/downloads/windows/)에서 3.12 계열 설치 파일을 선택하세요. 설치 후 PowerShell에서 <code>py -3.12 --version</code>으로 확인합니다. 다른 Python 버전을 덮어쓸 필요는 없습니다. |
| 인터넷 연결 | Python 패키지를 처음 설치할 때 | 이미 갖춘 <code>.venv</code>는 다른 PC로 무조건 복사해 쓰지 마세요. 새 PC에서 해당 PC용으로 다시 설치합니다. |
| Codex CLI 또는 Claude Code | AI 대화에서 MCP/스킬을 쓸 때만 | 각각의 [Codex 공식 안내](https://developers.openai.com/codex/cli/) 또는 [Claude Code 공식 안내](https://code.claude.com/docs/en/setup)를 따라 설치·로그인합니다. **CLI만 사용할 경우 둘 다 불필요**합니다. 호스트 자체에는 네트워크·계정이 필요할 수 있습니다. |
| Blender **4.2·4.3·4.5·5.2** 중 검증된 버전 | 두 렌더·<code>.blend</code>·Blender 장면 가져오기를 쓸 때만 | [Blender 공식 이전 버전 다운로드](https://www.blender.org/download/previous-versions/)에서 필요한 버전을 받습니다. 이 PC에 설치된 4.2.16 LTS·4.3.2·4.5.13 LTS·5.2.1 LTS는 실제 MCP 렌더와 BLEND→3DM 왕복에 통과했습니다. 다른 버전은 별도 확인이 필요합니다. |

프로젝트의 필수 Python 패키지는 [requirements.txt](requirements.txt)에 **고정된 버전**으로 적혀 있습니다: <code>rhino3dm 8.35.0</code>, <code>mcp 1.30.0</code>, <code>Pillow 11.3.0</code>, <code>numpy 2.3.3</code>. 테스트 도구는 [requirements-dev.txt](requirements-dev.txt)에 별도로 있습니다. Rhino 프로그램이나 Rhino 라이선스를 설치할 필요는 없습니다.

## 폴더 확인과 빠른 시작

1. 파일 탐색기에서 내려받은 이 프로젝트 폴더를 엽니다. <code>README.md</code>와 <code>requirements.txt</code>가 보이는 최상위 폴더인지 확인하세요.
2. 탐색기 주소창에 <code>powershell</code>을 입력하고 Enter를 누릅니다. 이 폴더에서 PowerShell이 열립니다.
3. 다음을 **한 줄씩** 입력합니다. 가상환경(<code>.venv</code>)이 없을 때만 첫 설치와 패키지 다운로드가 실행됩니다. 기존 환경과 프로그램 버전은 자동으로 갱신하지 않습니다.

~~~powershell
Get-Location
py -3.12 --version
if (-not (Test-Path .\.venv\Scripts\python.exe)) { py -3.12 -m venv .venv; & .\.venv\Scripts\python.exe -m pip install -r requirements.txt }
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli build .\examples\small_house.json .\workspace\small_house.3dm
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli inspect .\workspace\small_house.3dm
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli render .\workspace\small_house.3dm .\workspace\main.png
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli render .\workspace\small_house.3dm .\workspace\secondary.png --azimuth 135
~~~

성공하면 <code>workspace</code>에 <code>small_house.3dm</code>, <code>main.png</code>, <code>secondary.png</code>가 생깁니다. 탐색기에서 PNG 두 장을 더블클릭해 실제 내용이 보이는지 확인하세요. <code>inspect</code>는 저장 파일의 객체·레이어·단위·범위를 다시 읽습니다. **같은 이름의 출력이 이미 있으면 덮어쓰지 않고 실패**하므로 지우지 말고 <code>small_house_v2.3dm</code>처럼 새 이름을 지정하세요.

이미 이 프로젝트에 <code>.venv</code>가 있고 버전이 맞는 경우 새로 만들 필요가 없습니다. 다른 PC에서 온 <code>.venv</code>나 패키지 버전이 다른 환경은 현재 설치기가 자동 업그레이드하지 않습니다.

## Codex 또는 Claude Code에 설치

**CLI만 쓴다면 이 단계는 건너뛰세요.** AI 호스트에 설치하면 스킬 폴더와 로컬 MCP 연결을 함께 사용합니다. 설치 대상은 다른 폴더가 아니라 **현재 프로젝트 폴더**입니다. 설치기는 기존 다른 내용의 스킬이나 MCP 항목을 덮어쓰지 않습니다. 먼저 <code>--dry-run</code>으로 예상 상태를 봅니다.

~~~powershell
py -3.12 .\scripts\install_skill.py --host codex --project . --dry-run
py -3.12 .\scripts\install_skill.py --host codex --project .
& .\.venv\Scripts\python.exe .\scripts\verify_installation.py --host codex
~~~

Claude Code를 쓰는 사람은 위 설치 명령의 <code>--host codex</code>를 <code>--host claude</code>로 바꿉니다. 검증 명령도 <code>--host claude</code>로 바꿉니다. Claude Code에서 먼저 로그인하고 프로젝트 MCP 승인 요청을 처리하세요. 현재 이 PC에서는 **Claude Code 로그아웃으로 실제 호스트 검증이 실패**했습니다. 설치 결과의 <code>mcp_status: ready</code>는 등록 설정 확인일 뿐 로그인·승인·호출 성공을 뜻하지 않습니다.

Codex는 <code>.agents/skills/sodam-rhino-architectural-modeling/</code>, Claude Code는 <code>.claude/skills/sodam-rhino-architectural-modeling/</code>에 스킬을 둡니다. 새 호스트 세션을 열고 스킬을 지정해 <code>get_architectural_workspace</code>를 호출해야 실제 연결을 확인할 수 있습니다. 이 PC의 비대화형 Codex 검증에는 도구 승인 설정 <code>--approve-for-me</code>가 필요했습니다. 다른 PC의 절대경로를 복사한 <code>.mcp.json</code>이나 전역 MCP 등록은 사용할 수 없으므로, 폴더를 옮겼다면 기존 항목을 무작정 덮어쓰지 말고 경로를 확인한 후 설치기를 실행하세요.

## 실행과 실제 사용 순서

**사람이 CLI로 사용할 때:** 사진·설명에서 확실한 치수를 적고 [예제 JSON](examples/small_house.json)을 복사합니다. 텍스트 편집기로 새 파일의 <code>origin</code>(시작 좌표), <code>size</code>(크기), <code>name</code>(부품 이름)를 바꿉니다. <code>build</code>로 새 3DM을 만들고 <code>inspect</code>로 재열기, <code>render</code> 두 번으로 다른 방향을 확인합니다. 예제 JSON은 <code>units: meters</code>를 사용합니다. 새 JSON에는 <code>units</code>를 반드시 명시하고 <code>meters</code>, <code>millimeters</code>, <code>centimeters</code>, <code>feet</code> 중 하나를 선택해야 합니다. <code>z</code>는 위쪽입니다.

**AI 대화로 사용할 때:** 프로젝트에서 Codex/Claude Code를 열고 “설치된 <code>sodam-rhino-architectural-modeling</code> 스킬과 <code>sodam-rhino-offline</code> MCP를 사용해 작업 폴더를 확인하고, 이 건물의 **확실한 치수와 추정한 부분을 구분**한 뒤 3DM·정면/보조 시점 이미지를 새 이름으로 만들어줘”라고 요청합니다. AI가 먼저 <code>get_architectural_workspace</code>를 호출해 작업 위치를 확인해야 합니다. AI가 생성한 명세와 이미지는 사용자가 확인하세요. 사진만으로 측정값이 정확해지지는 않습니다.

**기존 부품만 바꿀 때:** MCP의 <code>revise_architectural_spec</code>에 원본 JSON 파일명, 정확한 부품 이름, 완전한 대체 부품 JSON, 새 출력 JSON 이름을 전달한 뒤 새 3DM을 만듭니다. 사진 근거가 붙은 명세는 이 간편 수정 경로가 거부하므로 전체 명세를 새로 작성하고 근거 감사를 다시 해야 합니다.

## 명령어 모음

다음 명령의 앞부분 <code>& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli</code>는 모두 같습니다. 전체 도움말은 <code>&amp; .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli --help</code>, 부품 생성 도움말은 <code>&amp; .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli build --help</code>로 확인합니다.

| 명령 | 입력 → 결과 | 예시 |
|---|---|---|
| <code>build</code> | JSON → 새 3DM | <code>build .\examples\small_house.json .\workspace\house.3dm</code> |
| <code>inspect</code> | 3DM → 객체·레이어·범위 표시 | <code>inspect .\workspace\house.3dm</code> |
| <code>render</code> | 3DM → 검수 PNG | <code>render .\workspace\house.3dm .\workspace\main.png --azimuth 315 --elevation 28</code> |
| <code>render-blender</code> | 3DM → 두 렌더 PNG + <code>scene.blend</code> | <code>render-blender .\workspace\house.3dm .\workspace\blender_output --blender-exe "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"</code> |
| <code>import-blend</code> | 신뢰할 수 있는 <code>.blend</code> → 메시 3DM | <code>import-blend .\workspace\source.blend .\workspace\source.3dm --blender-exe "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"</code> |
| <code>prepare-reference</code> | 참고 이미지·알려진 치수 → 근거 기록 JSON | 아래 사진 절차 참고 |
| <code>draft-evidence</code> | 명세·근거 기록 → 숫자별 추정 표시 명세 | 아래 사진 절차 참고 |
| <code>audit-evidence</code> | 자료 해시·수치 출처 검사 | 아래 사진 절차 참고 |
| <code>build-verified</code> | 감사 가능한 명세 → 새 3DM | 아래 사진 절차 참고 |

Blender 카메라는 <code>--front-azimuth</code>, <code>--front-elevation</code>, <code>--rear-azimuth</code>, <code>--rear-elevation</code>으로 방향을 지정합니다. 기본값은 315°/28°와 135°/28°입니다. 두 방향 사이가 10° 미만이면 거부됩니다. <code>import-blend</code>의 <code>--meters-per-unit</code>은 Blender 파일에 물리 단위가 없을 때 정확한 변환 비율을 알면 사용합니다. 모르면 기본 **Blender 1 단위 = 1 m라는 가정**을 표시합니다.

MCP 서버에는 12개 도구가 있습니다: <code>get_architectural_workspace</code>, <code>write_architectural_spec</code>, <code>revise_architectural_spec</code>, <code>build_architectural_model</code>, <code>inspect_architectural_model</code>, <code>render_architectural_view</code>, <code>render_blender_model</code>, <code>import_blender_scene</code>, <code>prepare_architectural_reference</code>, <code>draft_architectural_evidence</code>, <code>audit_architectural_evidence</code>, <code>build_verified_architectural_model</code>. 실제 입력 형식은 호스트가 표시하는 도구 설명을 따릅니다.

## 사진 근거를 다루는 방법

사진을 사용할 때는 원본 사진을 보관하고, 알려진 치수와 추정값을 나눕니다. 예를 들어 외벽 폭이 도면에 “10 m”라고 있으면 <code>given</code>, 사진에서 읽은 것은 <code>measured</code>, 보이지 않아 가정한 것은 <code>inferred</code>입니다. 이 분류는 **정확도 보증이 아닙니다.** 사진 해시가 달라지거나 필수 출처가 빠지면 검증형 모델 생성을 중단합니다.

~~~powershell
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli prepare-reference .\workspace\reference.json .\workspace\photo.png --known facade_width=10 --units meters
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli draft-evidence .\workspace\spec.json .\workspace\reference.json .\workspace\spec_review.json
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli audit-evidence .\workspace\spec_review.json .\workspace\reference.json
& .\.venv\Scripts\python.exe -m sodam_rhino_mcp.cli build-verified .\workspace\spec_review.json .\workspace\reference.json .\workspace\verified.3dm
~~~

먼저 <code>photo.png</code>와 직접 만든 <code>spec.json</code>을 <code>workspace</code>에 놓으세요. 초안은 수치마다 추정 표시를 추가하므로 사람이 [원본 자료](workspace/)와 대조·수정한 다음 감사를 실행합니다. 알려진 치수 이름·값·단위가 일치해야 <code>given</code>을 인정합니다. 감사가 통과해도 사진의 투시·가림·잘못 입력한 사실을 자동 판별하는 것은 아닙니다. **사용자 참고 사진 없이 실행한 샘플 점수**는 [BENCHMARK.md](BENCHMARK.md)에 따로 기록했습니다.

## Blender로 렌더하고 가져오기

Blender가 설치된 경우 <code>render-blender</code>를 실행하면 새 출력 폴더에 <code>front.png</code>, <code>rear.png</code>, <code>scene.blend</code>가 생성됩니다. 저장된 3DM 메시를 재료로 사용하며 조명·재질은 기본 예시입니다. PNG 파일이 두 장 있다는 사실과 사진이 같은 모습이라는 주장은 다릅니다. 파일을 직접 열어 방향과 내용물을 확인하세요.

기존 Blender 장면을 3DM으로 바꾸려면 작업 원본 <code>.blend</code>를 보존하고 <code>import-blend</code>를 실행합니다. Blender 모디파이어의 평가된 메시·이름·레이어·기본 색을 가져옵니다. Blender는 <code>--factory-startup --disable-autoexec</code>로 실행해 자동 실행 스크립트를 끄지만 **알 수 없는 출처의 .blend는 여전히 열지 마세요.** 사용할 Blender 버전의 실제 <code>blender.exe</code> 위치를 <code>--blender-exe</code>에 적습니다. 위 명령의 4.5 경로는 예시이며, 설치된 4.2·4.3·5.2 경로로 바꿀 수 있습니다. MCP에서는 <code>SODAM_BLENDER_EXE</code> 환경 변수나 기본 설치 경로를 사용합니다.

## 워크플로우와 아키텍처

~~~text
사용자 사진·설명·확실한 치수
  → 사람/AI가 사실·측정·추정을 구분
  → JSON 구성요소 명세 작성/수정
  → [선택] 사진 해시·수치 근거 기록과 감사
  → Python 모델 엔진 + rhino3dm → 구성요소별 메시 3DM 저장
  → 저장 3DM 재열기·객체/단위/경계 검사
  → 두 방향 직교 검수 PNG
  → [선택] 검증된 Blender 버전 → 두 렌더 PNG와 편집 원본 .blend
  → [선택] 원본 .blend 메시 → 새 3DM
~~~

<code>sodam_rhino_mcp/cli.py</code>와 <code>server.py</code>는 같은 모델 엔진을 호출합니다. 서버는 <code>stdio</code>(호스트와 로컬 프로세스 사이 표준 입출력) 방식으로 동작하고 별도 웹사이트·DB·로그인 화면을 제공하지 않습니다. Windows 실행기 <code>start_mcp.cmd</code>는 현재 폴더의 <code>.venv</code> Python과 기본 <code>workspace</code>를 사용합니다. MCP에서 쓸 폴더는 <code>SODAM_RHINO_WORKSPACE</code>로 지정할 수 있습니다. 서버가 파일명을 요청할 때는 해당 폴더 **바로 아래의 단순 파일명**만 허용합니다. CLI는 사용자가 지정한 파일 경로를 직접 사용하므로, 작업 전 경로를 확인해야 합니다.

## 보안과 데이터 흐름

- **로컬 처리:** 이 프로젝트의 모델 생성·3DM 재열기·이미지 작성은 로컬 프로세스에서 합니다. Python 패키지 다운로드와 AI 호스트 사용은 인터넷/계정이 필요할 수 있으므로 프로젝트 전체를 “완전 오프라인 AI”라고 해석하지 마세요.
- **저장 위치:** 기본 MCP 입력·출력은 <code>workspace/</code>입니다. 사용자 사진, JSON, 3DM, PNG, BLEND에는 비공개 설계 내용이 들어갈 수 있습니다. 공유·백업·클라우드 동기화 전에 직접 검토하세요.
- **경계:** MCP는 상위 폴더로 빠지는 파일명을 거부하고 기존 이름의 결과를 덮어쓰지 않습니다. 출력 실패 후 불완전한 파일이 남지 않도록 하는 테스트도 있습니다. 이 조치가 모든 악성 파일·호스트 권한 문제를 해결한다는 뜻은 아닙니다.
- **호스트 권한:** Codex/Claude Code의 로그인과 MCP 호출 승인은 해당 호스트가 관리합니다. 이 서버 자체에는 사용자 계정·역할별 권한이나 네트워크 API가 없습니다. 신뢰하지 않는 사람에게 이 컴퓨터의 호스트·작업 폴더 접근을 주지 마세요.
- **비밀정보:** API 키·비밀번호·토큰을 사진 이름, JSON, 명령, 대화, README에 넣지 마세요. 2026-09-25 검사에서 <code>.venv</code>·<code>__pycache__</code>·<code>.git</code> 폴더를 제외한 1,849개 파일 중 읽을 수 있었던 파일에는 검사한 고신뢰 비밀키 패턴이 없었습니다. 기존 3DM 1개는 권한 오류로 읽지 못했고, BLEND 22개에는 Windows 절대 경로처럼 보이는 데이터가 있습니다. 공유 전 파일별 확인이 필요하며, 이 검사는 모든 비밀이나 개인정보의 부재를 증명하지 않습니다.

## 파일과 문서 위치

| 경로 | 의미 |
|---|---|
| <code>README.md</code> / <code>README.html</code> | 같은 한국어 내용의 Markdown / 브라우저용 HTML |
| <code>README.en.md</code> / <code>README.en.html</code> | 같은 영어 내용의 Markdown / 브라우저용 HTML |
| <code>examples/small_house.json</code> | 빠른 시작용 건물 명세 |
| <code>workspace/</code> | 기본 MCP 작업·출력 폴더; 실제 결과를 직접 확인 |
| <code>skill/sodam-rhino-architectural-modeling/</code> | 설치할 스킬 원본; <code>.agents/</code>·<code>.claude/</code>는 설치본 |
| <code>sodam_rhino_mcp/</code> | CLI·MCP 서버·3DM 생성·검수 코드 |
| <code>scripts/install_skill.py</code> / <code>scripts/verify_installation.py</code> | 설치와 실제 작동 검사 |
| <code>requirements.txt</code> / <code>requirements-dev.txt</code> | 고정 실행 의존성 / 테스트 도구 |
| <code>ANALYSIS.md</code> / <code>PARITY.md</code> / <code>BENCHMARK.md</code> | 원본 분석 / 기능 대응·한계 / 합성 샘플 평가 |
| <code>UPSTREAM_LICENSE.txt</code> / <code>resources/</code> | 원본 MIT 고지 / 가져온 참고 자료 |
| <code>LICENSE</code> / <code>LICENSE-GPL-3.0.txt</code> / <code>NOTICE</code> / <code>NOTICE.md</code> | Apache 2.0 / Blender 스크립트 GPL 3+ / 저작권 고지 / 권리·배포 점검표 |
| <code>sodam_acceptance_20260924*</code> | 과거 합성 예제 산출물; 사용자 사진에 대한 품질 증명은 아님 |

## 테스트와 현재 확인 상태

~~~powershell
& .\.venv\Scripts\python.exe .\scripts\verify_installation.py --host codex
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\ruff.exe check .
& .\.venv\Scripts\mypy.exe sodam_rhino_mcp
& .\.venv\Scripts\python.exe .\scripts\smoke_mcp.py
~~~

2026-09-25 이 PC의 Blender 4.2.16·4.3.2·4.5.13·5.2.1 각각에서 **실제 MCP 요청으로** JSON→3DM 생성, 두 시점 Blender 렌더, BLEND 저장·3DM 재가져오기가 통과했습니다. Codex 설치·MCP 도구 발견·모델 재열기·근거 감사·PNG 작업, 단위 테스트 46개, Python 문법 검사와 의존성 검사도 통과했습니다. 기존 5.2 렌더 PNG 두 장은 1200×800으로 열리고 서로 달랐습니다. 임시 500개 상자 생성·재열기도 완료했습니다.

**현재 정적 검사:** Ruff 전체 검사 통과, mypy 핵심 모듈 10개 검사 통과, 단위 테스트 46개 통과, 실제 MCP 통신·3DM 생성·검수 흐름 통과입니다. <code>typings/rhino3dm/</code>은 설치된 rhino3dm 8.35.0의 불완전한 타입 선언을 이 프로젝트에서 사용하는 실제 API 범위로 보정합니다.

**미확인:** 이 PC의 Claude Code는 로그아웃 상태여서 실제 호스트 연결 검증이 완료되지 않았습니다. 렌더의 육안 품질, 실제 사용자 사진과의 정확도, 제3자 편집기의 3DM 편집, 다른 PC·미시험 Blender 버전도 확인되지 않았습니다. [권리·배포 점검표](NOTICE.md)에 생성물의 경로·메타데이터 위험을 설명합니다. 브라우저 UI·모바일 반응형·DB·자체 로그인 기능은 이 로컬 CLI/MCP에 없습니다.

## 업데이트 내용

<details>
<summary>펼치기: 현재 구현까지의 주요 변경과 검증 상태</summary>
<ul>
<li>원본 지침만 있던 경로 대신 Rhino 실행 없이 3DM을 만들고 다시 여는 로컬 MCP/CLI 엔진을 추가했습니다.</li>
<li>JSON 부품을 상자·개구부 벽·박공지붕·원형 기둥으로 확장하고 구성요소 이름·레이어·근거·입력 제어값을 저장합니다.</li>
<li>새 파일을 만드는 구성요소 수정, 사진 해시·치수 출처 감사, 두 시점 검수 PNG, Blender 렌더·BLEND 가져오기를 추가했습니다.</li>
<li>경로 이탈·기존 파일 덮어쓰기·잘못된 입력·부분 출력·설치 충돌에 대한 방어와 회귀 테스트를 추가했습니다.</li>
<li>Claude 로그인·MCP 연결을 별도로 검증하도록 바꿨습니다. 현재 이 PC의 Claude 로그아웃은 여전히 실패로 표시됩니다.</li>
<li>Blender 4.2·4.3·4.5·5.2의 실제 MCP 왕복을 확인했습니다. 현재 Ruff·mypy 검사는 통과하며, Claude 로그아웃, 실제 사진 정확도와 완전한 Rhino 기능 동등성은 미확인입니다. 세부 이력은 PARITY.md에 있습니다.</li>
</ul>
</details>

## 문제·오류 대처

| 보이는 문제 | 확인·대처 순서 |
|---|---|
| <code>py -3.12</code>를 찾지 못함 | Python 3.12 설치와 <code>py -3.12 --version</code> 확인. 다른 버전으로 조용히 바꾸지 마세요. |
| <code>.venv\Scripts\python.exe</code>가 없음 | 프로젝트 루트인지 <code>Get-Location</code>으로 확인하고 빠른 시작의 venv·패키지 설치를 실행합니다. |
| 패키지 버전이 다르다고 함 | <code>requirements.txt</code>의 고정 버전을 확인하세요. 설치기는 기존 환경을 임의 업데이트하지 않습니다. |
| <code>refusing to overwrite</code> | 결과 파일 이름을 <code>_v2</code>처럼 바꿉니다. 원본을 지워서 통과시키지 마세요. |
| JSON 입력 오류 또는 3DM이 안 만들어짐 | 예제와 <code>units</code>, 이름 중복, 양수 크기, 개구부 범위를 비교합니다. <code>build</code> 후 <code>inspect</code>로 재확인합니다. |
| MCP 도구가 보이지 않음 | 설치기 <code>--dry-run</code> → 호스트 재시작/새 세션 → MCP 승인 → <code>verify_installation.py</code> 순서로 확인합니다. 설정의 <code>ready</code>만 보고 성공이라 판단하지 마세요. |
| Claude Code 검증 실패 | 먼저 Claude Code 로그인 상태와 프로젝트 MCP 승인을 확인합니다. 로그아웃은 현재 검증기에서 실패로 처리됩니다. |
| Blender를 찾지 못함 / 렌더 실패 | 검증된 버전의 실제 <code>blender.exe</code> 경로를 <code>--blender-exe</code>로 지정하거나 <code>SODAM_BLENDER_EXE</code> 환경 변수를 지정합니다. 출력 폴더에 세 파일이 모두 있는지 확인합니다. |
| 모델 크기가 틀림 | JSON <code>units</code>와 Blender 장면 단위, 필요한 경우 <code>--meters-per-unit</code>을 확인합니다. 사진만 보고 절대 치수를 확정하지 마세요. |
| 파일이 다른 폴더에 생김 | MCP의 <code>get_architectural_workspace</code> 응답과 <code>SODAM_RHINO_WORKSPACE</code>를 확인합니다. CLI는 명령에 적은 경로를 사용합니다. |
| lint·mypy 실패 | 고정된 개발 의존성을 설치하고 위 검증 명령을 다시 실행합니다. <code>typings/rhino3dm/</code>의 보정 선언은 rhino3dm 8.35.0 기준이므로 SDK 버전을 임의로 바꾸지 마세요. |

## 자주 묻는 질문

**Q. Rhino 라이선스 없이 진짜 사용할 수 있나요?**

A. 지원된 JSON→메시 3DM·검수도 경로는 Rhino를 실행하지 않습니다. Blender 기능은 Blender가 있어야 합니다. Rhino 고유 편집 기능과 똑같지는 않습니다.

**Q. 사진 한 장을 올리면 똑같은 건물이 자동 생성되나요?**

A. 아닙니다. 보이지 않는 면과 절대 치수는 사진만으로 확정할 수 없습니다. 사람이 사실·측정·추정을 구분하고 결과를 확인해야 합니다.

**Q. Codex나 Claude Code를 꼭 설치해야 하나요?**

A. 아닙니다. 명령줄 CLI만 쓸 수 있습니다. AI 대화에서 도구를 호출하려면 해당 호스트·계정·승인이 필요합니다.

**Q. 검수 PNG와 Blender PNG는 무엇이 다른가요?**

A. 전자는 저장된 메시를 빠르게 확인하는 직교 그림이고, 후자는 Blender 장면의 기본 재질·조명 렌더입니다. 둘 다 사진과 일치한다는 증거는 아닙니다.

**Q. 기존 파일을 수정할 수 있나요?**

A. 입력 JSON을 수정해 **새 이름의** 3DM을 재생성합니다. 기존 결과 덮어쓰기는 거부합니다. Rhino의 자유로운 NURBS 편집과 같지는 않습니다.

**Q. 모바일이나 웹페이지에서 사용할 수 있나요?**

A. 현재 Windows 로컬 CLI/MCP 프로젝트이며 모바일 앱·웹 서비스는 없습니다. HTML README는 설명서를 브라우저에서 읽기 위한 파일입니다.

**Q. 지금 배포하거나 상업적으로 판매해도 되나요?**

A. 이 프로젝트의 자체 코드와 문서는 Apache License 2.0으로 공개할 계획이며, Blender API 스크립트 4개는 GPL-3.0-or-later입니다. 원본 MIT 자료와 외부 자료는 각각의 고지를 지켜야 합니다. 사용자의 사진·도면·모델·고객 자료에 대한 공개·상업 이용권은 별도로 확인하세요.

## 저작권·라이선스·상업적 이용

1. **프로젝트 자체 코드·문서:** 권리자 표시는 <code>Copyright 2026 SoDam AI Studio</code>입니다. [LICENSE](LICENSE)의 Apache License, Version 2.0에 따라 사용·수정·복제·재배포·판매·서비스 운영·교육·고객사 납품이 가능합니다. 재배포 시 라이선스 사본과 적용되는 저작권·변경·NOTICE 고지를 유지해야 합니다. 보증은 없고 책임이 제한됩니다. 이 허가는 상표 사용권이나 입력 자료의 권리를 주지 않습니다.
2. **Blender API 스크립트 예외:** <code>scripts/blender_scene.py</code>, <code>scripts/export_blend_mesh.py</code>, <code>scripts/create_blend_fixture.py</code>, <code>scripts/benchmark_reference_blender.py</code>는 <code>bpy</code>를 직접 사용합니다. 이 네 파일은 [LICENSE-GPL-3.0.txt](LICENSE-GPL-3.0.txt)의 GNU GPL version 3 or later로 별도 제공됩니다. 공유·판매·납품 시 해당 소스와 GPL 조건을 함께 제공해야 합니다. 이는 [Blender 공식 안내](https://www.blender.org/about/license/)를 반영한 것이며, 다른 코드와 결합·배포할 때의 적용 범위는 법무/전문가 검토가 필요합니다. Blender 실행 파일은 이 저장소에 포함하지 않습니다.
3. **원본 자료:** [원본 저장소](https://github.com/frankee0920-rgb/rhino-architectural-reverse-modeling)에서 가져온 자료의 MIT 허가와 <code>Copyright (c) 2026 frank</code>는 [UPSTREAM_LICENSE.txt](UPSTREAM_LICENSE.txt)에 유지됩니다. 복사·수정·재배포·상업 이용 시 해당 저작권·허가·면책 고지를 함께 보존하세요. [NOTICE](NOTICE)에 권리 범위를 구분했습니다.
4. **외부 의존성과 사용자 자료:** <code>rhino3dm</code> SDK의 허가는 [McNeel 고지](https://developer.rhino3d.com/license/)를 확인하세요. Python 패키지, Blender, 사진, 도면, 3D 모델, 폰트, 이미지, 아이콘, 상표, AI 생성물, 외부 API·모델에는 각자의 조건이 있습니다. 저장소 라이선스가 이들의 권리를 자동으로 부여하지 않습니다. 특히 고객 자료·개인정보·비공개 정보는 공개 예제에 넣지 마세요.
5. **쉽게 말해:** 본인 소유 자료로 로컬에서 시험할 수 있습니다. 코드를 복제·수정·포크·배포하거나 상업 서비스·교육·납품에 쓰려면 위 세 라이선스의 해당 조건을 지키고, 투입 자료·계약·API 요금제·서비스 약관을 직접 확인해야 합니다. Rhino 라이선스 없이 3DM을 만들 수 있지만 Rhino 제품 기능·정확성·설계 적합성을 보증하지 않습니다.

이 설명은 확인된 파일과 공식 안내를 바탕으로 한 일반 정보입니다. **참고용·법적 효력 보장 안 함, 사용자 책임·변호사 확인 권장.**
