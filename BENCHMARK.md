# 사용자 파일 없는 역모델링 검증

`workspace/benchmark_case_01/`은 기존 예제 JSON과 생성 엔진을 입력으로 사용하지 않고 Blender에서 별도로 작성한 기준 모델입니다. 기준 모델의 정면·측면·후면·사시도 PNG와 **알려진 폭 10.0m**만 보고 `reconstruction.json`을 저장했습니다. 그 뒤 `reconstructed.3dm`을 생성했으며, 이 두 파일을 고정한 후 `reference_truth.json`을 열어 점수를 계산했습니다.

## 검증 결과

- `score_geometry.json`: 저장된 3DM 메시 정점을 다시 읽어 **관찰/제공된 13개 치수 모두 허용 오차 0.2m 이내**. 이 사례에서는 13개 모두 기준 수치와 일치했습니다.
- 벽 두께는 제공된 시점에서 알 수 없으므로 `inferred_hidden`으로 표시하고 점수에서 제외했습니다.
- 저장된 모델은 13개 이름 붙은 메시 객체로 재읽혔습니다. `reconstructed_front.png`, `reconstructed_rear.png`, `blender_output/front.png`, `blender_output/rear.png`, `blender_output/scene.blend`가 실제 저장 3DM에서 생성됐습니다.
- `score.json`은 최초 JSON 값 비교 기록입니다. **최종 판정은 저장 지오메트리를 측정한 `score_geometry.json`**을 사용합니다.

## 해석 범위와 남은 위험

이 결과는 정면·측면·후면 직교도가 제공된 **단일 인공 샘플**의 기술 검증입니다. 생성기와 복원 작업을 같은 에이전트가 수행했으며, 무작위 기준값은 복원 JSON을 고정할 때까지 열지 않았습니다. 실제 사진의 투시 왜곡, 가려진 면, 불명확한 치수, 복잡한 형상에 대한 정확도는 입증되지 않았습니다. Rhino UI에서 직접 열거나 제3자 3DM 리더로 교차 검증하지도 않았습니다. Blender 참조 장면과 Blender 출력은 별도 파일로 보존되어 있습니다.

기존 검수도의 지붕 겹침 표시는 픽셀별 깊이 버퍼로 수정하고 같은 시점의 수정 전후 이미지를 직접 비교했습니다. 기존 문제는 검수도 렌더러의 가시화 오류였으며 3DM 형상 오류가 아니었습니다. 사진 일치 여부는 PNG 출력만으로 판단하지 않고 저장 지오메트리와 Blender 뷰를 함께 확인해야 합니다.

## 파일과 재검증

- 기준: `front.png`, `right.png`, `rear.png`, `perspective.png`, `reference.blend`, `reference_truth.json`, `brief.txt`
- 복원: `reconstruction.json`, `reconstructed.3dm`, 두 검수 PNG, `blender_output/`
- 점수: `score_geometry.json`

새 사례를 만들 때는 빈 출력 폴더에 기존 Blender 4.5로 `scripts/benchmark_reference_blender.py`를 실행합니다. 출력 폴더 다음에 정수 시드를 지정하면 재현할 수 있고, 생성 시드는 기준값 파일에 기록됩니다. 첫 사례는 시드 기록 기능 추가 전에 생성되어 기준 `.blend`와 PNG를 보존합니다. `workspace/benchmark_seed_check/`는 시드 기능만 확인한 별도 참고 사례이며 복원 점수 대상은 아닙니다. 기준값 파일은 복원 JSON 저장 전 열지 않습니다. 점수 스크립트는 새 사례의 `score_geometry.json`이 이미 있으면 덮어쓰지 않습니다.

```powershell
& 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe' -b --factory-startup --python .\scripts\benchmark_reference_blender.py -- .\workspace\benchmark_new
# 이미지와 brief.txt만 보고 reconstruction.json 작성, CLI build로 reconstructed.3dm 생성
& .\.venv\Scripts\python.exe -m scripts.score_benchmark .\workspace\benchmark_new
```



## 도전형 사례: L자 별동, 가림, 단일 원근

workspace/benchmark_case_02/는 독립 Blender 생성기의 challenging 모드로 만든 사례입니다. 앞쪽 L자 별동과 전경 나무가 있으며, 기준 이미지는 perspective.png 한 장뿐입니다. 알려진 값은 본채 폭 10.0m입니다. 복원 초안과 검증형 3DM을 저장한 뒤 숨겨진 reference_truth.json을 열었습니다. 기준 생성 시드는 734291입니다.

- reference_packet.json은 기준 사진의 해시·화소 크기·알려진 폭을 보존합니다. reconstruction_annotated.json은 기하 숫자 37개 중 주어진 폭 2개, 추정 35개, 사진에서 확정 계측 0개로 기록했습니다.
- reconstructed.3dm에는 이름 붙은 메시 6개가 있습니다. inspection_front.png와 blender_render/의 두 PNG 및 scene.blend를 실제 저장된 3DM에서 만들었습니다. 전경 나무는 건물 형상이 아니므로 제외했습니다.
- 기존 score_challenge.json은 복원 JSON을 비교한 기록입니다. 새 score_challenge_geometry.json은 저장된 reconstructed.3dm 메시 정점을 재서 비교합니다. 알려진 폭 오차는 0m, 추정 치수 9개의 평균 절대 오차는 0.45m, 최대 오차는 1.0m로 일치했습니다. 가려진 출입문 위치·폭과 본채 깊이는 특히 부정확했습니다. 이는 불확실성을 드러내는 실패 분석이지 정확한 자동 복원의 성공 증거가 아닙니다.
- 새 기준 실행은 기존 Blender의 --factory-startup으로 scripts/benchmark_reference_blender.py 뒤에 빈 출력 폴더, 정수 시드, challenging을 순서대로 지정합니다. 복원 JSON과 3DM을 고정한 뒤 scripts/score_challenge.py로 저장된 3DM 메시의 오차를 계산합니다. 기존 점수 파일은 덮어쓰지 않고 score_challenge_geometry.json을 새로 만듭니다.

실제 고객 사진, 제3자 3DM 리더에서의 열기, NURBS 편집, 구조·시공 적합성은 아직 검증되지 않았습니다. 설치된 FreeCAD 1.1의 Import.insert는 이 3DM에 no supported file format을 반환했습니다. 이는 FreeCAD 가져오기 미지원 결과이며 3DM 손상 증거는 아닙니다.
