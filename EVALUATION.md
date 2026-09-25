# 실제 사례 평가 절차

이 절차는 **저장된 3DM의 지정 치수**를 독립적으로 기록한 기준값과 비교합니다. 사진과 형상이 닮았는지, 가려진 면이 맞는지, Rhino에서 편집 가능한지는 자동으로 판정하지 않습니다. `case_type: real`은 작성자의 선언일 뿐 실제 사진임을 증명하지 않습니다.

1. 사용 권한이 확인된 실제 건축물 사진과 별도 도면·현장 실측값을 확보합니다. 고객 정보, 위치 정보, 비공개 자료를 공개 저장소에 넣지 않습니다. 현장 실측값을 모른다면 사진만으로 절대 치수를 확정하지 않습니다.
2. 기준값을 기록할 사람은 복원자가 만든 JSON·3DM을 보지 않고 치수와 출처를 먼저 작성합니다. 복원자는 기준값을 보지 않고 사진과 공개된 치수만으로 JSON→3DM을 저장합니다. 두 파일이 정해지면 수정하지 말고 SHA-256을 기록합니다.
3. 프로젝트의 무시된 `workspace/` 아래 사례 폴더에 `model.3dm`, `photo.png` 같은 이미지와 `case_manifest.json`을 둡니다. 3DM은 미터 단위, 모든 객체는 고유 이름을 가진 메시여야 합니다. 같은 폴더의 단순 파일명만 받습니다.
4. 아래의 **예시 값은 가상 숫자**입니다. 각 파일의 SHA-256에는 PowerShell의 `(Get-FileHash .\model.3dm -Algorithm SHA256).Hash.ToLower()` 및 사진 파일의 해시를 사용하고, 각 `truth_m`에는 독립 실측값을 입력합니다. `truth_source`에 도면 번호·측정 기록 등 실제 출처를 적습니다. `visibility`는 `given`(복원자에게 공개), `visible`(사진에서 관찰), `hidden`(비공개 기준) 중 하나입니다. 모든 수치는 미터입니다. `extent`는 물체의 해당 축 길이, `min`·`max`는 해당 축의 최소·최대 좌표입니다. 상대 거리는 `relative_to`와 `relative_edge`(`min` 또는 `max`)를 함께 적습니다.

```json
{
  "schema_version": 1,
  "case_type": "real",
  "model": {"file": "model.3dm", "sha256": "<실제 64자리 소문자 SHA-256>"},
  "references": [{"file": "photo.png", "sha256": "<실제 64자리 소문자 SHA-256>"}],
  "measurements": [
    {"name": "building_width", "object": "main_mass", "axis": "x", "quantity": "extent", "truth_m": 10.0, "tolerance_m": 0.1, "visibility": "hidden", "truth_source": "독립 현장 측량 기록"}
  ]
}
```

5. 프로젝트 최상위 폴더에서 `& .\.venv\Scripts\python.exe -m scripts.score_case .\workspace\사례폴더명`을 실행합니다. 성공하면 `case_score.json`이 새로 생깁니다. 기존 점수 파일은 덮어쓰지 않습니다. 다시 채점할 때는 원본을 보존하고 새 사례 폴더를 만듭니다.
6. `measurements_within_tolerance`와 각 오차를 확인하되, **주어진 치수와 숨긴 치수를 분리**해 평가합니다. 숨긴 치수에서 큰 오차가 나면 복원 성능 한계로 기록합니다. 기준 출처가 불확실하거나 복원자가 기준값을 봤다면 독립·블라인드 평가라고 부르지 않습니다. 최소 3개 이상 서로 다른 실제 건물/촬영 조건을 권장하며, 단일 사례 결과를 일반화하지 않습니다.
7. 마지막으로 사용 권한이 있는 사람이 사진과 전·후·측면 렌더를 눈으로 대조하고, 제3자 3DM 프로그램에서 열기·편집 여부를 별도로 기록합니다. 현재 채점 도구는 이 두 검사를 수행하지 않으므로, 별도 대조·외부 프로그램 검사를 완료하더라도 결과의 `photo_shape_match_verified`와 `independent_3dm_reader_verified`는 항상 `false`입니다. 실제 검토 내용과 담당자·날짜·사용 프로그램은 별도 기록으로 보존하세요.

`score_case.py`는 3DM을 `rhino3dm`으로 다시 읽어 메시 정점의 바운딩 박스를 계산합니다. 해시 일치와 이미지 파일 해독을 검사하지만 사진의 내용이나 `truth_source` 진위를 판별하지 않습니다. 기준값도 모델에서 역산했다면 독립 평가가 아닙니다. 이 도구의 통과는 나열된 치수의 허용 오차만 의미합니다.
