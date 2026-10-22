# Citrus Drop

<p align="center"><img src="assets/citrus-drop.svg" alt="Citrus Drop 로고" width="180"></p>

<p align="center"><strong>끌어 놓는 순간, 파일 변환이 간편해집니다.</strong></p>

> 🚧 지속적으로 기능을 추가하고 개선하는 개발 중 프로젝트입니다.

윈도우용 로컬 파일 변환 앱입니다. 파일을 끌다가 **Shift**를 누르면 원형 메뉴가 나타나고, 원하는 형식 위에 놓으면 변환합니다. 기본 창에서 파일을 선택해 실행할 수도 있습니다.

현재 버전은 **Python + PySide6** 기반이며 이미지·PDF·영상·음성 변환과 ZIP 압축을 지원합니다. 새로운 기능과 사용성 개선을 계속 진행하고 있습니다.

## 빠른 실행

Windows 10/11 **64비트**, Python **3.11~3.13**이 필요합니다. 검증에 사용한 Python은 3.12입니다.

1. 저장소를 내려받아 압축을 모두 해제하세요.
2. 처음에는 `Setup.cmd`를 실행하세요. `.venv` 가상환경을 만들고 `requirements.txt`의 패키지를 설치합니다. 최초 설치에는 인터넷이 필요합니다.
3. `Start.cmd`를 실행하세요. 또는 `.venv\Scripts\python.exe main.py`로 실행할 수 있습니다.
4. 소스를 업데이트한 뒤에는 `Setup.cmd`를 다시 실행하여 의존성을 맞춰 주세요.

소스 실행 시 콘솔 창이 함께 열립니다. 콘솔 없이 배포하려면 아래의 EXE 빌드를 사용하세요. 이미 Python 3.14 이상이 기본으로 지정돼 있다면 `py -3.12 -m venv .venv`처럼 지원 버전으로 가상환경을 먼저 만든 뒤 Setup.cmd를 실행하세요.

직접 설치하는 경우:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

관리자 권한은 필요하지 않습니다. 탐색기와 앱을 같은 일반 권한으로 실행해 주세요. 앱 소스 폴더와 변환 결과를 저장할 원본 폴더에 쓰기 권한이 필요합니다.

## 사용 방법

- 탐색기에서 파일을 선택하고, 마우스 버튼을 계속 누른 채 끌기 시작합니다.
- 파일을 조금 움직인 뒤 **Shift를 한 번 누릅니다**. Shift를 먼저 누른 채 끌기 시작하는 순서는 지원하지 않습니다.
- 원형 메뉴 안으로 파일을 이동하면 가능한 형식이 표시됩니다. 주황색으로 강조된 항목 위에 놓으면 실행됩니다.
- Shift를 떼어도 메뉴는 유지됩니다. 중앙·항목 사이의 틈은 실행 영역이 아닙니다.
- Esc를 누르거나 메뉴 밖에서 드래그를 끝내면 메뉴가 닫힙니다.
- 기본 창에서도 파일 추가·드롭 → 출력 형식 선택 → 변환 실행이 가능합니다.
- 이미지 PDF의 페이지 순서는 파일 목록의 `위로`·`아래로`로 변경할 수 있습니다.
- 창을 닫으면 트레이에 남습니다. 트레이 아이콘을 더블클릭하면 다시 열립니다. 완전 종료는 트레이 메뉴의 `종료`입니다. 트레이를 제공하지 않는 환경에서는 창을 닫을 때 종료합니다.

## 지원 기능

| 구분 | 입력 | 출력 / 동작 | 준비 |
| --- | --- | --- | --- |
| 이미지 | PNG, JPG/JPEG, BMP, TIFF/TIF, GIF, WebP | PNG, JPG, BMP, TIFF, 정지 GIF, WebP | Python 패키지 설치 |
| 이미지 PDF | 위 이미지 하나 또는 여러 개 | 목록 순서대로 하나의 PDF | Python 패키지 설치 |
| PDF 이미지화 | PDF | 모든 페이지를 PNG/JPG로 저장 | Python 패키지 설치 |
| PDF 문자 추출 | 문자가 들어 있는 PDF | UTF-8 TXT | Python 패키지 설치 |
| 영상 | MP4, MOV, MKV, WebM, AVI, WMV, M4V | MP4, WebM, MP3, WAV, FLAC, OGG | FFmpeg 선택 |
| 음성 | MP3, M4A, WAV, FLAC, OGG, Opus, AIFF/AIF, WMA | MP3, WAV, FLAC, OGG | FFmpeg 선택 |
| 압축 | 선택한 일반 파일 | 하나의 ZIP | 추가 준비 없음 |
| 경로 복사 | 선택한 일반 파일 | 전체 경로를 줄바꿈으로 클립보드에 복사 | 추가 준비 없음 |

**PDF와 WebP에는 Poppler나 별도 실행 파일을 연결할 필요가 없습니다.** PDFium·Pillow 등이 Python 패키지에 포함됩니다. 영상·음성만 FFmpeg를 사용합니다. 사용한 Pillow 빌드가 WebP를 지원하지 않으면 해당 메뉴가 숨겨집니다.

서로 다른 종류의 파일을 함께 선택하면 ZIP·경로 복사만 표시됩니다. 폴더는 파일 목록에서 제외됩니다. 가상 파일·메일 첨부 객체는 먼저 일반 파일로 저장해 주세요.

### 이미지와 PDF 처리 기준

- 원본 파일은 유지하고, 결과는 원본과 같은 폴더에 새로 만듭니다.
- 기본 결과 이름은 `원래이름_converted.확장자`입니다. 같은 이름이 있으면 `_2`, `_3`을 붙입니다.
- JPG·WebP 품질은 90입니다. JPG·BMP와 이미지 PDF의 투명 영역은 흰색입니다.
- 이미지 EXIF 방향을 픽셀에 반영하며 원본 이미지 메타데이터는 복사하지 않습니다. 인쇄용 색상 프로파일 보존은 보장하지 않습니다.
- GIF 애니메이션·다중 페이지 TIFF는 파일마다 **첫 프레임 하나**를 사용합니다.
- 이미지 PDF는 A4 세로/가로를 이미지 방향에 맞춰 선택하고, 비율을 유지해 중앙 배치합니다. 여백은 최소 24pt이며 잘라내지 않습니다. ReportLab에 픽셀 이미지를 전달해 PDF에 삽입합니다.
- 이미지 PDF는 첫 입력 이미지의 폴더에 저장합니다. 여러 입력이면 `Citrus_images_날짜_시간.pdf`입니다.
- PDF → PNG/JPG는 **150 DPI**, JPG 품질 90으로 모든 페이지를 출력합니다. `원래이름_png_pages` 또는 `원래이름_jpg_pages` 폴더에 페이지 번호 순으로 저장합니다. 기존 폴더가 있으면 번호를 붙입니다.
- TXT는 PDF 안의 문자만 추출합니다. **OCR은 하지 않습니다.** 이미지 전용 PDF는 빈 TXT가 나올 수 있으며, 문단·표 순서는 원본과 다를 수 있습니다.
- 열기 암호 입력 기능은 없습니다. 암호가 필요한 PDF·손상된 PDF는 오류로 표시합니다.
- PDF 렌더링은 스레드 간 잠금으로 직렬화합니다. PDFium을 동시에 호출하지 않습니다.
- 1억 픽셀을 넘는 입력 이미지나 PDF 렌더링 페이지는 거부합니다. 디코딩 단계의 전체 메모리 사용량에 대한 별도 제한은 없습니다.

### 취소와 오류

작업 중 취소할 수 있습니다. FFmpeg 프로세스는 중지하고, PDF·이미지는 현재 디코딩/인코딩 호출이 끝난 뒤 취소될 수 있습니다. 취소·실패한 현재 파일의 임시 출력은 정리를 시도합니다. 취소 전에 완료된 결과는 유지됩니다. 이미지 PDF와 ZIP은 전체 선택을 하나의 작업으로 처리합니다.

PDF 페이지는 임시 폴더에서 모두 변환한 뒤 새 결과 폴더로 옮깁니다. 기존 결과 파일과 폴더를 덮어쓰지 않습니다. 강제 종료·권한 오류가 있으면 `.citrus-drop-…` 임시 폴더가 남을 수 있습니다.

일괄 변환 중 파일 하나가 실패해도 다음 파일은 계속 처리하고 기록을 남깁니다. 여러 작업을 동시에 실행하지는 않습니다. 작업 기록과 선택 파일 목록은 이번 실행 동안만 유지합니다.

## FFmpeg 연결

1. [FFmpeg 공식 다운로드 안내](https://ffmpeg.org/download.html)에서 신뢰할 수 있는 Windows 배포본을 준비하세요.
2. 앱의 `FFmpeg 선택`으로 `ffmpeg.exe`를 지정하세요.
3. 또는 EXE/소스 폴더 옆의 `tools/ffmpeg.exe`에 배치하세요. 필요한 DLL이 있으면 배포본의 구조를 유지하세요.

FFmpeg는 포함하거나 자동 다운로드하지 않습니다. 실제 코덱 지원은 선택한 빌드에 따라 달라집니다. H.264/AAC, VP9/Opus, MP3/Vorbis 등 출력 인코더가 필요합니다. 외부 프로세스는 인수 목록으로 실행하며 셸을 사용하지 않습니다.

설정은 `%LOCALAPPDATA%\CitrusDrop\settings.json`에 저장합니다. 기존 C# 버전의 `ffmpeg-path.txt`가 있으면 경로를 이어서 사용합니다. 이전 Poppler 설정은 더 이상 필요하지 않습니다.

## EXE로 빌드

**Windows에서** `build.cmd`를 실행하세요. 패키지를 설치하고 PyInstaller로 `dist/CitrusDrop/CitrusDrop.exe`를 만듭니다.

- 사용자 PC에 Python을 별도 설치하지 않고 배포할 수 있도록 만드는 구성입니다.
- EXE 한 개만 복사하지 말고 **CitrusDrop 폴더 전체**를 전달해야 합니다. Qt·PDFium 라이브러리와 데이터가 함께 필요합니다.
- FFmpeg는 별도로 선택하거나 EXE 옆 `tools` 폴더에 배치합니다.
- Windows용 EXE는 Windows에서 빌드해야 합니다. Linux 빌드 결과를 Windows용으로 사용할 수 없습니다.
- 라이브러리 공지와 라이선스 파일을 함께 유지하세요. 자세한 내용은 THIRD_PARTY_NOTICES.md에 있습니다.

## 로고

프로젝트 로고는 `assets/citrus-drop.svg`에 있습니다. 현재 앱의 창·트레이 아이콘은 `assets/logo.png` 또는 `assets/icon.ico`를 사용하며, EXE 아이콘은 `assets/icon.ico`가 있어야 적용됩니다. 자세한 내용은 `assets/README.md`를 참고하세요.

## 소스 구조

| 파일 | 수정할 내용 |
| --- | --- |
| `main.py` | 실행 진입점 |
| `citrus_drop/ui.py` | 한국어 기본 창, 원형 메뉴, 드롭 |
| `citrus_drop/app.py` | 트레이, 작업 스레드, 시작·종료 |
| `citrus_drop/native.py` | 윈도우 입력 상태, Shift 제스처 |
| `citrus_drop/models.py` | 지원 형식과 메뉴 규칙 |
| `citrus_drop/converters.py` | 이미지·FFmpeg·ZIP |
| `citrus_drop/pdf_tools.py` | 이미지 PDF, PDF 페이지 이미지·문자 추출 |
| `citrus_drop/jobs.py` | 일괄 처리·취소·작업 기록 |
| `citrus_drop/storage.py` | 결과 이름 충돌 방지·설정·임시 파일 |
| `CitrusDrop.spec` | EXE 패키징 구성 |

## 테스트

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

또는 `tests/run-tests.cmd`를 실행하세요. 자동 환경에서는 `--no-pause`를 추가합니다. Qt 테스트는 offscreen 환경에서 화면·메뉴·드롭 이벤트와 작업 스레드를 검사합니다. `python main.py --smoke-test`로 실제 앱 초기화·종료도 확인할 수 있습니다.

현재 검증 결과와 남은 Windows 실기기 항목은 VALIDATION.md에 기록합니다.

## 알려진 제한

- 전역 Shift 메뉴는 Windows 전용입니다. 다른 OS에서는 기본 창의 파일 선택·드롭으로 변환을 테스트할 수 있습니다.
- 드래그는 마우스 버튼·이동·Shift 상태로 감지합니다. 파일이 아닌 드래그에서도 메뉴가 잠시 뜰 수 있지만, 실제 로컬 파일 드롭이 있어야 변환합니다. 키 입력 내용이나 클립보드 내용을 수집하지 않습니다.
- Windows 탐색기와 실제 OLE 드롭, 혼합 DPI·다중 모니터·RDP는 실기기 확인이 필요합니다.
- HEIC/AVIF/SVG, Word/엑셀/프레젠테이션 변환, PDF → Word, OCR, 크롭·PDF 편집·자동 실행·단축키 변경은 구현하지 않았습니다.
- 변환 중 파일을 서버로 업로드하지 않습니다. 초기 패키지 설치와 선택적 빌드 도구 설치만 인터넷을 사용합니다.

## 라이선스 및 사용 안내

Citrus Drop은 소스 코드를 공개하는 **소스 공개(Source-available)** 프로젝트입니다.

- 개인적·비상업적 목적의 사용, 복제 및 수정은 허용됩니다.
- 상업적 이용, 상업적 배포, 유료 제품·서비스에의 통합은 저작권자의 사전 서면 허가가 필요합니다.
- 소스 공개는 상업적 이용 권한을 자동으로 부여하지 않습니다.
- 자세한 조건은 [LICENSE](LICENSE)를 확인하세요. 이 정책은 OSI 인증 오픈소스 라이선스가 아닙니다.

## 참고

- [Qt for Python](https://doc.qt.io/qtforpython-6/)
- [Pillow](https://pillow.readthedocs.io/)
- [pypdfium2](https://pypdfium2.readthedocs.io/en/stable/python_api.html)
- [ReportLab](https://docs.reportlab.com/)
- [PyInstaller](https://pyinstaller.org/)
