# 검증 상태 — 2026-10-22 / 0.2

## 완료한 검사

- 전체 앱 소스를 C# 5 / .NET Framework 4.8 참조 어셈블리 대상으로 컴파일했습니다. 경고를 오류로 처리한 빌드가 통과했습니다.
- Windows 자동 검증 코드 `SmokeTests.cs`도 같은 대상으로 컴파일했습니다. 실행은 아직 하지 못했습니다.
- 앱에서 사용하는 `PdfDocumentWriter.cs`, `PdfTools.cs`, `Core.cs`를 별도 .NET 8 테스트 실행 파일로 컴파일하고 Linux에서 실행했습니다.
- 실제 Poppler 엔진으로 PDF → PNG/JPG/TXT를 실행했습니다. 아래 11개 검사가 통과했습니다.
- 독립적인 pypdf 파서로 생성 PDF의 2페이지와 A4 가로·세로 방향을 확인했습니다.
- 생성된 PNG를 실제 디코딩하고, 두 페이지를 렌더링한 결과를 눈으로 확인했습니다. 이미지 비율과 순서, 여백, 방향이 의도대로 유지되었습니다.
- XML 설정·매니페스트와 빌드 스크립트, 원본 보존·출력 이름 충돌·임시 폴더 정리 코드를 확인했습니다.

### 실행한 PDF 검사 11개

1. 자체 PDF 작성 코드가 PDF를 생성함
2. PDF의 전체 2페이지를 PNG로 출력함
3. 같은 작업을 다시 실행해도 기존 결과 폴더가 보존됨
4. PDF의 전체 2페이지를 JPG로 출력함
5. 원본 PDF의 바이트가 유지됨
6. 문자 PDF에서 UTF-8 TXT를 추출함
7. 이미지 전용 PDF에서 OCR 문자를 만들어내지 않고 빈 텍스트를 출력함
8. 잘못된 PDF는 오류로 처리하고 최종 결과 폴더를 남기지 않음
9. 시작 전에 취소된 PDF 작업을 거부함
10. PDF 작업의 임시 폴더가 정리됨
11. 엔진 사용 가능 여부에 따라 PNG/JPG/TXT 메뉴가 표시됨

## 남은 Windows 실행 검사

현재 검증 환경은 Linux입니다. Windows 대상 EXE 컴파일 성공이 Windows 화면·입력·코덱 실행을 보장하지는 않습니다.

`tests\run-tests.cmd`를 Windows에서 실행하면 이미지 크기·투명 배경·EXIF 방향·원본 보존·이름 충돌·ZIP 내용·이미지 PDF 생성·취소를 자동 검사합니다. 자동 실행 환경에서는 `--no-pause` 옵션을 사용할 수 있습니다.

- [ ] Windows 기본 이미지 변환과 이미지 → PDF의 WPF 전처리 실행
- [ ] 탐색기 단일·다중 파일 드래그 중 Shift 메뉴 표시와 드롭
- [ ] Shift를 뗀 뒤 메뉴 유지, Esc·외부 드롭 취소
- [ ] 원본 파일 이동·삭제 없이 결과 생성
- [ ] 파일 목록의 위로·아래로 이동이 PDF 페이지 순서에 반영됨
- [ ] Poppler Windows 배포본의 DLL·데이터 경로 연결
- [ ] PDF → PNG/JPG/TXT 전체 페이지 출력과 한글 텍스트
- [ ] 열기 암호가 필요한 PDF의 오류 안내
- [ ] 실행 중 취소 시 Poppler/FFmpeg 프로세스와 임시 파일 정리
- [ ] 쓰기 금지 폴더·대형 파일·다중 모니터·혼합 화면 배율
- [ ] 창 닫기·트레이 재열기·진행 중 종료

## 검증 도구 구분

- 제품은 .NET Framework 4.8용 WPF 앱입니다. .NET 8은 이번 공통 코드 실행 검사에 사용했으며 사용자 PC의 필수 실행 환경이 아닙니다.
- WPF 자동 검사: `tests/SmokeTests.cs`
- 공통 PDF 코드 검사: `tests/PortablePdfTests.cs`, `tests/run_portable_tests.py`
- 공통 검사 재현: .NET 8 SDK, Python의 Pillow·reportlab·pypdf, Poppler를 준비하고 `python tests/run_portable_tests.py`를 실행합니다.
- Windows에서는 `--poppler-dir "C:\Poppler\Library\bin"`을 추가합니다.
