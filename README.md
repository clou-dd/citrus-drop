# Citrus Drop 0.2 — Windows용 로컬 파일 변환

Tangerine for Mac의 **파일 드래그 → Shift → 원형 메뉴에 드롭 → 로컬 변환** 흐름을 참고하여 새로 작성한 Windows 데스크톱 앱의 첫 버전 소스입니다. Tangerine의 공식 Windows 버전은 아니며 원본 코드·아이콘은 사용하지 않았습니다.

**현재 버전: PDF 변환 기능을 추가한 0.2입니다.** 전체 앱과 Windows 테스트 코드의 C# 5 / .NET Framework 4.8 대상 컴파일을 확인했습니다. PDF 작성·페이지 이미지화·텍스트 추출의 공통 코드는 Linux에서 실제 실행 검증했습니다. Windows의 WPF 화면·탐색기 드래그 동작과 이미지 디코더 실행은 별도로 확인해야 합니다.

## 실행 방법

1. ZIP을 다운로드한 다음 **압축을 모두 해제**해 주세요. ZIP 내부에서 직접 실행하지 마세요.
2. Windows 10/11, .NET Framework 4.8이 있는 일반 사용자 계정에서 `Start.cmd`를 더블클릭하세요.
3. 최초 실행 시 Windows의 C# 컴파일러로 `CitrusDrop.exe`를 빌드한 뒤 앱을 실행하도록 구성했습니다. Visual Studio나 별도 .NET SDK를 요구하지 않습니다. 빌드가 실패하면 콘솔의 오류를 확인해 주세요.
4. 이후에는 생성된 `CitrusDrop.exe`를 직접 실행하셔도 됩니다. 기존 버전을 업데이트하거나 소스를 수정했다면 앱을 종료하고 `build.cmd`를 다시 실행하세요. 기존 EXE가 있으면 `Start.cmd`는 재빌드하지 않습니다.

앱을 놓은 폴더와 변환할 원본 폴더에 쓰기 권한이 필요합니다. 관리자 실행은 필요하지 않습니다. 탐색기와 앱을 서로 다른 권한 수준으로 실행하면 Windows의 드롭 제한이 생길 수 있으므로 일반 권한으로 사용해 주세요.

## 사용하는 방법

- 탐색기에서 파일 하나 또는 여러 개를 선택하고 마우스로 끌기 시작하세요.
- **마우스 버튼을 계속 누른 채, 움직인 다음 Shift를 한 번 누르세요.** Shift를 먼저 누른 채 드래그를 시작하는 순서는 현재 지원하지 않습니다.
- 원형 메뉴가 나타나면 파일을 메뉴 안으로 조금 이동하세요. 파일 종류를 확인한 뒤 가능한 형식이 표시됩니다.
- 원하는 형식 위에서 마우스 버튼을 놓으면 작업을 시작합니다. Shift를 떼어도 메뉴는 유지됩니다.
- 중앙·메뉴 사이의 틈은 실행 영역이 아닙니다. 주황색으로 강조된 항목에 놓으세요.
- Esc를 누르거나 메뉴 밖에서 드래그를 끝내면 메뉴가 닫힙니다.
- 기본 창의 드롭 영역이나 `파일 추가`로 파일을 넣고 작업을 선택해 실행할 수도 있습니다.
- 창을 닫으면 트레이에 남습니다. 트레이 아이콘을 더블클릭하면 다시 열립니다. 완전 종료는 트레이 메뉴의 `종료`를 선택하세요.
- 원형 메뉴를 잠시 끄려면 기본 창에서 `Shift 원형 메뉴 사용` 체크를 해제하세요. 이 설정은 재실행 시 기본값으로 돌아옵니다.

## 포함된 기능

| 구분 | 입력 | 출력 / 동작 | 추가 준비 |
| --- | --- | --- | --- |
| 기본 이미지 | PNG, JPG/JPEG, BMP, TIFF/TIF, GIF | PNG, JPG, BMP, TIFF, 정지 GIF, 하나의 PDF | 없음 |
| WebP 이미지 | 기본 이미지, WebP | WebP 및 기본 이미지 형식 | FFmpeg |
| 영상 | MP4, MOV, MKV, WebM, AVI, WMV, M4V | MP4, WebM, MP3, WAV, FLAC, OGG | FFmpeg |
| 음성 | MP3, M4A, WAV, FLAC, OGG, Opus, AIFF/AIF, WMA | MP3, WAV, FLAC, OGG | FFmpeg |
| PDF 이미지화 | PDF | 모든 페이지를 PNG 또는 JPG로 저장 (150 DPI) | Poppler |
| PDF 텍스트 | 텍스트가 포함된 PDF | UTF-8 TXT 추출 (OCR 제외) | Poppler |
| 압축 | 선택한 일반 파일 | 하나의 ZIP 파일 | 없음 |
| 파일 작업 | 선택한 일반 파일 | 전체 경로를 줄바꿈으로 클립보드에 복사 | 없음 |

- FFmpeg의 실제 지원 여부는 선택한 빌드에 포함된 디코더·인코더와 원본 파일 내용에 따라 달라집니다. DRM 파일·손상된 파일 등은 변환되지 않을 수 있습니다.
- 서로 다른 종류의 파일을 함께 선택하면 공통 작업인 ZIP·경로 복사만 표시됩니다.
- JPG 품질은 90으로 고정했습니다. JPG·BMP의 투명 영역은 흰색으로 채웁니다.
- GIF 애니메이션과 여러 페이지 TIFF는 **첫 프레임 / 첫 페이지만** 변환합니다. 이미지로부터 PDF를 만들 때도 각 입력 파일의 첫 프레임을 한 페이지로 사용합니다.
- 기본 이미지 변환은 EXIF 방향을 픽셀에 반영하며, 원본 이미지 메타데이터를 복사하지 않습니다. 원본의 색상 프로파일 보존이나 인쇄용 색상 정확도는 보장하지 않습니다.
- 변환은 한 번에 한 작업, 파일별 순차 처리입니다. FFmpeg 실행 중에는 취소 버튼으로 중지할 수 있습니다. 이미지 디코딩·인코딩 자체는 즉시 중단되지 않을 수 있습니다.

## PDF 기능 사용

| 작업 | 사용 방법 | 결과 |
| --- | --- | --- |
| 이미지 → PDF | 이미지 선택 → `PDF 만들기` | 선택한 이미지들을 하나의 PDF로 저장 |
| PDF → PNG | PDF 선택 → `PNG` | 모든 페이지를 새 폴더에 `page-1.png` 등으로 저장 |
| PDF → JPG | PDF 선택 → `JPG` | 모든 페이지를 새 폴더에 `page-1.jpg` 등으로 저장 |
| PDF → TXT | PDF 선택 → `TXT` | 텍스트를 UTF-8 파일로 추출 |

- 이미지 → PDF는 Poppler 없이 사용할 수 있습니다. WebP 입력에는 기존과 같이 FFmpeg가 필요합니다.
- 이미지 PDF는 A4 세로/가로를 이미지 방향에 맞춰 선택하고, 비율을 유지해 중앙에 배치합니다. 여백은 최소 24pt이며 이미지를 잘라내지 않습니다. 모든 입력은 JPG 품질 90으로 재인코딩되므로 손실 압축이 적용됩니다. 투명 영역은 흰색입니다.
- 여러 이미지의 순서는 기본 창의 `위로`·`아래로` 버튼으로 바꿀 수 있습니다. 탐색기 드롭 순서가 원하는 순서와 다를 수 있으므로 기본 창에서 확인해 주세요.
- 이미지 PDF는 이미지 파일 하나당 한 페이지입니다. GIF 애니메이션·여러 페이지 TIFF의 전체 프레임 병합은 지원하지 않습니다.
- PNG·JPG 출력은 150 DPI이고 JPG 품질은 90입니다. 매우 큰 PDF 페이지나 많은 페이지는 시간·메모리·디스크 공간을 많이 사용합니다.
- TXT 추출은 PDF에 이미 들어 있는 문자만 사용합니다. 스캔 이미지의 글자 인식(OCR)은 하지 않습니다. 텍스트 없는 PDF도 빈 TXT로 정상 처리될 수 있으며 문단·표 순서는 원본과 다를 수 있습니다.
- 암호 입력 기능은 없습니다. 열기 암호가 필요한 PDF는 오류로 표시합니다. PDF 편집·페이지 합치기·분할 기능은 이 버전에 포함하지 않았습니다.

### PDF 엔진 연결 (PDF → PNG/JPG/TXT)

1. [Poppler Windows 배포 프로젝트](https://github.com/oschwartz10612/poppler-windows)의 Releases에서 Windows 배포본을 준비하고 **전체 압축을 해제**하세요.
2. 앱의 `PDF 엔진 선택`에서 배포본의 `Library/bin/pdftoppm.exe`를 선택하세요. `pdftotext.exe`가 같은 폴더에 있으면 TXT 메뉴도 활성화됩니다.
3. EXE만 따로 복사하지 말고 주변 DLL과 `share` 데이터 폴더를 포함한 전체 구조를 유지하세요.
4. 또는 전체 배포본의 `Library` 폴더가 `tools/poppler/Library` 위치에 오도록 배치하세요. `tools/poppler/bin` 또는 `tools/poppler` 아래에 실행 파일이 있는 배포 형태도 인식합니다.

이 프로젝트는 Poppler 바이너리를 포함하거나 자동 다운로드하지 않습니다. Poppler를 제품과 함께 배포한다면 해당 배포본과 종속 라이브러리의 라이선스를 확인해야 합니다. 원본 Poppler는 [공식 프로젝트](https://poppler.freedesktop.org/)에서 확인할 수 있습니다. 선택한 경로는 `%LOCALAPPDATA%\CitrusDrop\poppler-directory.txt`에 저장합니다.

## 결과 저장과 원본 보호

- 결과는 **각 원본 파일과 같은 폴더**에 `원래이름_converted.확장자`로 생성됩니다.
- 같은 결과 이름이 이미 있으면 `_2`, `_3`처럼 번호를 붙입니다. 원본이나 기존 결과를 덮어쓰지 않습니다.
- 변환이 끝난 임시 파일만 최종 이름으로 이동합니다. 실패하거나 취소한 현재 파일의 임시 결과는 삭제를 시도합니다. 강제 종료나 권한 오류가 있으면 `.citrus-drop-…` 임시 폴더가 남을 수 있습니다.
- ZIP은 첫 번째 선택 파일의 폴더에 `Citrus_날짜_시간.zip`으로 저장됩니다. 파일 이름이 중복되면 ZIP 내부 이름에 번호를 붙입니다. 원래 폴더 계층은 담지 않습니다.
- 이미지 PDF는 첫 입력 이미지 폴더에 저장합니다. 단일 입력은 `원래이름_converted.pdf`, 여러 입력은 `Citrus_images_날짜_시간.pdf`입니다.
- PDF 이미지화는 원본 폴더에 `원래이름_png_pages` 또는 `원래이름_jpg_pages` 폴더를 만듭니다. 기존 폴더가 있으면 `_2` 등을 붙입니다. 전체 변환이 성공한 뒤에만 결과 폴더를 확정합니다.
- 취소 전에 이미 완료된 결과 파일은 유지됩니다.
- 이 앱은 파일을 업로드하거나 변환 서버에 연결하지 않습니다. FFmpeg는 사용자가 지정한 로컬 실행 파일을 실행합니다. 앱은 FFmpeg를 자동 다운로드하지 않습니다.

## FFmpeg 연결

1. [FFmpeg 공식 다운로드 안내](https://ffmpeg.org/download.html)에서 신뢰할 수 있는 Windows 배포본을 준비하세요.
2. 압축을 해제한 뒤 앱에서 `FFmpeg 선택`을 눌러 `ffmpeg.exe`를 선택하세요.
3. 또는 `CitrusDrop.exe` 옆의 `tools` 폴더에 `ffmpeg.exe`를 배치하세요.
4. 연결 후 파일을 추가하거나 메뉴를 다시 열면 확장 형식이 표시됩니다. 작업 중에 실행 파일을 교체하지 마세요.

MP4: `libx264`, `aac` / WebM: `libvpx-vp9`, `libopus` / WebP: `libwebp` / MP3: `libmp3lame` / OGG: `libvorbis` 인코더를 사용합니다. FFmpeg를 재배포하는 경우 해당 빌드의 라이선스 조건을 별도로 확인해야 합니다. 이 패키지에는 FFmpeg 바이너리를 포함하지 않았습니다.

FFmpeg 경로는 사용자 계정의 `%LOCALAPPDATA%\CitrusDrop\ffmpeg-path.txt`에 저장합니다. 변환할 파일 목록이나 작업 기록은 영구 저장하지 않습니다.

## 알려진 제한과 미구현 기능

- **드래그 감지는 현재 마우스 버튼·이동·Shift 상태를 이용한 방식입니다.** 파일이 아닌 드래그에서도 메뉴가 잠시 뜰 수 있습니다. 실제 변환은 Windows가 전달한 `FileDrop` 경로를 확인한 뒤에만 실행됩니다. 키 입력 내용이나 클립보드를 수집하지 않습니다.
- 메뉴를 열 때 파일 종류는 아직 알 수 없으므로 처음에는 빈 원이 보일 수 있습니다. 파일을 메뉴 안으로 이동하면 가능한 형식이 나타납니다.
- 일반 파일만 처리합니다. 폴더·가상 파일·메일 첨부 객체를 직접 드래그하는 동작은 지원하지 않습니다. 폴더를 섞어 넣으면 폴더는 목록에서 제외됩니다.
- 지원하지 않는 확장자는 ZIP·경로 복사만 사용할 수 있습니다. HEIC/AVIF/SVG, Word·엑셀·프레젠테이션 변환과 PDF → 편집 가능한 Word 변환은 아직 구현하지 않았습니다.
- 크롭·영상 자르기·PDF 병합·파일 보관 선반·탐색기 우클릭 메뉴·로그인 시 자동 시작·단축키 변경·변환 품질 설정은 미구현입니다.
- 혼합 배율의 여러 모니터, RDP, 보안 프로그램이 설치된 환경에서 메뉴 위치와 드롭 수신은 Windows 실기기 검증이 필요합니다. 현재 DPI 설정은 시스템 DPI 방식입니다.
- 이미지 디코딩 전후 메모리 사용량이 클 수 있습니다. 1억 픽셀을 넘는 기본 이미지는 명시적으로 거부합니다. 매우 큰 파일에 대한 메모리 사용 제한은 별도로 구현하지 않았습니다.

## Windows 검증

- 자동 검증: `tests\run-tests.cmd`를 실행하세요. 이미지 출력·투명 영역·EXIF 방향·원본 보존·파일 이름 충돌·ZIP 중복 이름·취소·임시 파일 정리를 확인합니다. 실제 파일은 별도의 임시 테스트 폴더에서 만들고 정리합니다.
- 수동 검증: `VALIDATION.md`의 항목을 확인하세요. 자동 검증은 트레이나 탐색기 드래그 동작을 검사하지 않습니다.
- 현재 제공 환경에서는 Windows 테스트 EXE의 컴파일까지만 확인했습니다. Windows 자동·수동 검증은 실행하지 못했으며, 아래 별도 PDF 테스트는 실제 실행했습니다.

### 공통 PDF 코드 실행 검사 (개발용)

.NET 8 SDK, Python의 `Pillow`, `reportlab`, `pypdf`, Poppler를 준비한 뒤 `python tests/run_portable_tests.py`를 실행하세요. Windows에서는 `--poppler-dir "C:\Poppler\Library\bin"`을 추가하세요. 실제 앱의 PDF 작성·추출 코드를 사용하며, 별도 임시 폴더에서만 파일을 만듭니다. 이 테스트는 WPF 화면이나 Windows 이미지 전처리를 실행하지 않습니다.

## 소스 구조

| 파일 | 역할 |
| --- | --- |
| `src/Program.cs` | 시작·단일 실행·트레이·작업 실행·FFmpeg 설정 |
| `src/Native.cs` | Windows 입력 상태 확인·메뉴 위치 |
| `src/WheelWindow.cs` | 원형 메뉴·OLE 파일 드롭 |
| `src/MainWindow.cs` | 한국어 기본 창·파일 목록·작업 기록 |
| `src/Core.cs` | 지원 형식·파일 필터·출력 이름·프로세스 인수 인코딩 |
| `src/Converter.cs` | 이미지·FFmpeg·ZIP·취소·임시 파일 처리 |
| `src/PdfImages.cs` | 이미지 전처리와 PDF 생성 연결 |
| `src/PdfDocumentWriter.cs` | 이미지 PDF 구조 작성 |
| `src/PdfTools.cs` | Poppler 실행·페이지 이미지/TXT 추출 |

개발 기준: C# 5 문법, WPF, .NET Framework 4.8. 앱 실행에는 NuGet 패키지가 필요하지 않습니다. 선택적으로 제공한 SDK 프로젝트는 빌드용 Microsoft .NET Framework 참조 어셈블리 패키지를 사용합니다. 이 버전은 Windows 상주 UX를 확인하기 위한 시작점이며, 기능을 확장할 때 각 변환 엔진을 분리해 추가할 수 있는 구조입니다.

참고한 공개 문서:

- [Tangerine 공식 기능 소개](https://tangerineformac.com/)
- [Microsoft: WPF Drag and Drop Overview](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/advanced/drag-and-drop-overview)
- [Microsoft: GetAsyncKeyState](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getasynckeystate)
- [Microsoft: C# Compiler Options](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/)
