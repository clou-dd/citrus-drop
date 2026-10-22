# 검증 상태 — 2026-10-22 / Python 0.3.0

## 실제 확인한 내용

- 별도의 깨끗한 Python 3.12 가상환경에 requirements-dev.txt를 설치했습니다.
- `pip check`가 통과했습니다. PySide6 6.8.3, Pillow 12.3.0, pypdfium2 5.14.0, ReportLab 4.4.9를 사용했습니다.
- 자동 테스트 **38개가 통과**했습니다. 테스트 프로세스도 종료 코드 0으로 정상 종료했습니다. 창 없는 실행의 시작 실패 로그와 종료 코드 처리도 검사했습니다.
- 소스 앱의 `python main.py --smoke-test`가 통과했습니다. Qt 화면을 초기화하고 임시 이미지 → PDF → PNG 변환·디코딩을 실행한 뒤 정상 종료했습니다.
- PyInstaller로 Linux용 폴더 패키지를 실제 빌드했고, 패키지 실행 파일의 `--smoke-test`도 통과했습니다. Qt·PDFium·ReportLab 리소스가 포함되는지 실행으로 확인했습니다.
- 기본 창·원형 메뉴를 실제 렌더링해 한글 표시와 배치, 항목 강조를 확인했습니다. 투명 메뉴를 다시 그릴 때 안내 글자가 겹치던 문제를 수정했습니다.
- 생성한 PDF를 렌더링해 A4 가로/세로 방향, 이미지 비율·순서·여백을 확인했습니다.
- 기존 C# 코드를 현재 소스에서 제거하고 Python 실행·설치·빌드 안내로 정리했습니다. 과거 버전은 Git 이력에 남습니다.
- 프로젝트 SVG를 렌더링한 PNG를 확인했고, ICO의 16·24·32·48·64·128·256px 이미지 포함을 검사했습니다. 창·트레이·EXE에 같은 로고를 연결했습니다.
- `Start.cmd`는 `start`와 `pythonw.exe`로 실행하고 돌아오도록 수정했습니다. 설치 실패 시에만 오류를 볼 수 있도록 콘솔을 유지합니다.
- GitHub Actions의 Windows x64 빌드·테스트·EXE 실행 검사·배포 폴더 업로드를 추가했습니다. 실제 실행 결과는 저장소의 `Windows EXE` 워크플로에서 확인할 수 있습니다.

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

- [ ] Windows x64의 Setup.cmd / Start.cmd 실행
- [ ] build.cmd로 Windows EXE 빌드 후 폴더 전체에서 실행
- [ ] Windows API 입력 감지와 탐색기 실제 파일 드래그 중 Shift 메뉴 표시
- [ ] 실제 OLE 드롭의 Copy 효과와 원본 보존
- [ ] 트레이 아이콘·창 닫기·재열기·변환 중 종료
- [ ] 다중 모니터·혼합 DPI·RDP에서 메뉴 위치와 드롭 수신
- [ ] 선택한 Windows FFmpeg 배포본의 코덱·한글 경로
- [ ] Windows 탐색기·작업 표시줄에서 프로젝트 로고 표시

Windows용 실행 파일은 Linux에서 빌드하지 않았습니다. 저장소의 build.cmd와 CitrusDrop.spec는 Windows에서 해당 EXE를 만들기 위한 구성입니다. Linux 패키지 테스트 성공을 Windows EXE 검증 성공으로 해석하면 안 됩니다.

## 재현

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe main.py --smoke-test
```

`tests/run-tests.cmd --no-pause`로 자동 테스트를 실행할 수도 있습니다. 테스트용 파일은 독립적인 임시 폴더에서만 만들며, 변환 대상 원본을 덮어쓰지 않습니다.
