# 검증 상태 — 2026-10-22 / Python 0.3.3

## v0.3.3 프리릴리즈

- 작은 글씨에서 마지막 글자를 읽기 어려웠던 상단 버튼을 `앱 정보`로 변경하고, 버전·제작 정보·라이선스를 확인한다는 도움말을 추가했습니다.
- 기존 UI 테스트 **10개가 통과**했습니다. 실제 번들 문서로 라이선스 창이 열리고 프로젝트·폰트 라이선스와 v0.3.3이 표시되는 것도 확인했습니다.
- Linux Qt offscreen에서 최소 창 너비 650px 및 `QT_SCALE_FACTOR` 1·1.25·1.5로 상단을 렌더링해 글자 배치를 확인했습니다. Windows의 실제 모니터 DPI 검증을 대체하지 않습니다.
- [v0.3.3 Windows x64 검사](https://github.com/clou-dd/citrus-drop/actions/runs/39762158302)가 성공했습니다. 자동 테스트 **47개 통과·1개 건너뜀**이며, FFmpeg 미설치에 따른 선택적 실제 음성 변환 검사만 건너뛰었습니다. 단일 EXE 빌드·내장 고지·폰트·아이콘 및 동반 파일 없는 실행·PDF 변환·종료 검사도 통과했습니다.
- [v0.3.3 Pre-release](https://github.com/clou-dd/citrus-drop/releases/tag/v0.3.3)를 게시했습니다. EXE와 SHA256SUMS.txt 업로드 완료·파일 크기·EXE SHA-256 일치·게시 후 프리릴리즈 상태를 검사했습니다.
- 배포 검사 5개로 공개된 버전의 파일 보호, 잘못된 EXE 거부, 업로드 해시 불일치 시 게시 중단, 정상 프리릴리즈 게시, API 권한 오류 전파를 확인했습니다.
- README를 224줄에서 48줄로 줄였습니다. 공개 GitHub 페이지에서 프리릴리즈 표시·다운로드 링크·안내 영상·기존 원형 메뉴 이미지와 릴리스 첨부 파일 표시를 확인했습니다.

## 기존 기능 확인 기록 (v0.3.2)

- 별도의 깨끗한 Python 3.12 가상환경에 requirements-dev.txt를 설치했습니다.
- `pip check`가 통과했습니다. PySide6 6.8.3, Pillow 12.3.0, pypdfium2 5.14.0, ReportLab 4.4.9를 사용했습니다.
- 자동 테스트 **43개가 통과**했습니다. 테스트 프로세스도 종료 코드 0으로 정상 종료했습니다. 창 없는 실행의 시작 실패 로그와 종료 코드 처리도 검사했습니다.
- 소스 앱의 `python main.py --smoke-test`가 통과했습니다. Qt 화면을 초기화하고 임시 이미지 → PDF → PNG 변환·디코딩을 실행한 뒤 정상 종료했습니다.
- v0.3.2는 PyInstaller 단일 파일 방식으로 전환했습니다. 프로젝트·제작자·의존성·폰트 고지를 EXE에 포함하고 `정보·라이선스` 창에서 읽는 경로를 자동 테스트했습니다.
- Linux의 첫 빌드는 중간 PYZ 아카이브 헤더가 완성되지 않아 실행 검사가 실패했습니다. `/tmp`의 새 작업 폴더에서 캐시를 지우고 다시 빌드한 결과, 파일 하나만 공백·한글 경로에 복사한 실행 검사가 통과했습니다. 내장 폰트·이미지 → PDF → PNG·정상 종료와 동반 파일 미생성을 확인했고, 내장 고지 원문 바이트와 PYZ 읽기도 검사했습니다.
- 기본 창·원형 메뉴를 실제 렌더링해 한글 표시와 배치, 항목 강조를 확인했습니다. 투명 메뉴를 다시 그릴 때 안내 글자가 겹치던 문제를 수정했습니다.
- `창 닫기` 버튼이 스크롤 영역 밖에 유지되는지, 트레이 유무에 따라 창 숨김·종료가 구분되는지 검사했습니다. `프로그램 종료`에서 작업 취소를 거절하면 실행을 유지하고, 수락하면 작업 정리 후 종료하도록 대기하는지도 검사했습니다.
- Pretendard 원본 Regular·SemiBold·Bold를 앱 전용으로 로드하고 한글·영문·숫자 글리프와 실제 SemiBold 선택을 검사했습니다. 기본 창·원형 메뉴의 크기와 굵기를 맞췄고, 폰트 라이선스를 배포에 포함했습니다.
- 생성한 PDF를 렌더링해 A4 가로/세로 방향, 이미지 비율·순서·여백을 확인했습니다.
- 기존 C# 코드를 현재 소스에서 제거하고 Python 실행·설치·빌드 안내로 정리했습니다. 과거 버전은 Git 이력에 남습니다.
- 프로젝트 SVG를 렌더링한 PNG를 확인했고, ICO의 16·24·32·48·64·128·256px 이미지 포함을 검사했습니다. 창·트레이·EXE에 같은 로고를 연결했습니다.
- `Start.cmd`는 `start`와 `pythonw.exe`로 실행하고 돌아오도록 수정했습니다. 설치 실패 시에만 오류를 볼 수 있도록 콘솔을 유지합니다.
- v0.3.2의 [GitHub Actions Windows x64 검사](https://github.com/clou-dd/citrus-drop/actions/runs/39750455677)가 성공했습니다. Python 3.12에서 **42개 통과, 1개 건너뜀**입니다. 정보·라이선스와 닫기·종료 버튼 검사도 포함하며, FFmpeg 미설치로 선택적 실제 음성 변환 검사만 건너뛰었습니다.
- Windows용 단일 `CitrusDrop.exe`를 실제 빌드했습니다. PE GUI 서브시스템(콘솔 없음), 내장 아이콘, 고지 원문 바이트와 Pretendard OTF 포함을 검사했습니다. **EXE 하나만 공백·한글이 있는 새 폴더에 복사한 `--smoke-test`가 통과**했습니다. 내장 Pretendard 로딩, 임시 이미지 → PDF → PNG 변환·정상 종료·동반 파일 미생성을 확인했습니다.
- Windows 단일 EXE를 [CitrusDrop-windows-x64 아티팩트](https://github.com/clou-dd/citrus-drop/actions/runs/39750455677/artifacts/12412789897)로 업로드했습니다. ZIP 안의 `CitrusDrop.exe`만 사용하면 됩니다. `_internal` 폴더는 필요하지 않습니다. 보관 기간은 30일이며 새 빌드로 갱신할 수 있습니다.

- README용 실제 앱 화면 3장을 캡처했습니다. 샘플 이미지 2개를 원형 메뉴의 Qt 드롭 이벤트로 PDF 변환하고, 성공 상태·2페이지 PDF·첫 페이지 렌더링을 확인했습니다. 캡처 환경과 재현 방법은 `docs/screenshots/README.md`에 기록했습니다.

## 테스트 범위

| 영역 | 검사 내용 |
| --- | --- |
| 이미지 | PNG/JPG/BMP/TIFF/GIF/WebP 변환, 투명 영역, EXIF 방향, 메타데이터 제거, GIF 첫 프레임 |
| 원본·결과 보호 | 원본 바이트 보존, 결과 이름 충돌, 기존 빈 결과 폴더 보존, 실패 시 임시 출력 정리 |
| PDF | 여러 이미지의 페이지 순서·A4 방향·색상, 전체 PNG/JPG 출력, UTF-8·한글 문자 추출, 이미지 전용 PDF의 빈 TXT |
| PDF 오류·동시성 | 손상·암호 PDF 오류, 중간 취소 후 결과 미생성, PDFium 호출 직렬화 |
| ZIP·일괄 처리 | 중복 파일명과 내용, 파일 하나 실패 후 계속 처리, 시작 전 취소 |
| 외부 프로세스 | 실제 FFmpeg WAV → FLAC 변환, 실행 중 취소 시 자식 프로세스 종료, 오류 출력 처리 |
| 설정 | 기존 C# FFmpeg 경로 이관, JSON 저장·재사용 |
| Qt 화면 | 파일 순서 변경, 작업 선택, 실제 로컬 파일 드롭 수신, 외부 URL 거부, 원형 메뉴 경계·재그리기·드롭 |
| 앱 수명 | 작업 스레드 완료·정리, 클립보드 경로 복사, Qt 리소스 정리 후 정상 종료 |
| Shift 제스처 | 끌기 시작 후 Shift, Shift 해제 후 유지, Esc·외부 종료, 먼저 누른 Shift 거부 |

Qt 테스트와 렌더링은 Linux의 offscreen 플랫폼에서 실행했습니다. 이 검사가 Windows 탐색기나 실제 마우스 입력 검증을 대체하지는 않습니다.

## 남은 Windows 실기기 검사

- [x] Windows x64 CI에서 단일 EXE 빌드·아이콘 리소스·콘솔 없음·동반 파일 없이 시작/변환/종료 검사
- [ ] Windows x64의 Setup.cmd / Start.cmd 실행
- [ ] build.cmd로 Windows 단일 EXE 빌드 후 실행
- [ ] Windows API 입력 감지와 탐색기 실제 파일 드래그 중 Shift 메뉴 표시
- [ ] 실제 OLE 드롭의 Copy 효과와 원본 보존
- [ ] 트레이 아이콘·창 닫기·재열기·변환 중 종료
- [ ] 다중 모니터·혼합 DPI·RDP에서 메뉴 위치와 드롭 수신
- [ ] 선택한 Windows FFmpeg 배포본의 코덱·한글 경로
- [ ] Windows 탐색기·작업 표시줄에서 프로젝트 로고 표시

Windows용 실행 파일은 GitHub의 Windows 러너에서 빌드·실행 검사했습니다. 자동 GUI 검사는 offscreen 환경이며, 탐색기에서의 실제 드래그·트레이·작업 표시줄 표시와 사용자 PC의 설치/시작 스크립트 검사는 별도로 남아 있습니다.

## 재현

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe tools\fetch_fonts.py
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe main.py --smoke-test
```

`tests/run-tests.cmd --no-pause`로 자동 테스트를 실행할 수도 있습니다. 테스트용 파일은 독립적인 임시 폴더에서만 만들며, 변환 대상 원본을 덮어쓰지 않습니다.
