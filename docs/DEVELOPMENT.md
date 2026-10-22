# 개발자 안내

### Python 소스로 실행

Windows 10/11 **64비트**, Python **3.11~3.13**이 필요합니다. 검증에 사용한 Python은 3.12입니다.

1. 저장소를 내려받아 압축을 모두 해제하세요.
2. 처음에는 `Setup.cmd`를 실행하세요. `.venv` 가상환경을 만들고 패키지와 Pretendard 폰트를 준비합니다. 최초 설치에는 인터넷이 필요합니다.
3. `Start.cmd`를 실행하세요. 또는 `.venv\Scripts\python.exe main.py`로 실행할 수 있습니다.
4. 소스를 업데이트한 뒤에는 `Setup.cmd`를 다시 실행하여 의존성을 맞춰 주세요.

`Start.cmd`는 `pythonw.exe`를 별도 프로세스로 실행하고 돌아옵니다. 더블클릭할 때 CMD 창이 잠깐 나타날 수 있지만 앱이 종료될 때까지 남아 있지는 않습니다. 최초 설치·설치 오류를 표시하는 동안에는 콘솔 창이 유지됩니다. 시작 오류는 `%LOCALAPPDATA%\CitrusDrop\startup-error.log`에서 확인할 수 있습니다. 콘솔에서 직접 오류를 확인하려면 `.venv\Scripts\python.exe main.py`로 실행하세요.

이미 Python 3.14 이상이 기본으로 지정돼 있다면 `py -3.12 -m venv .venv`처럼 지원 버전으로 가상환경을 먼저 만든 뒤 Setup.cmd를 실행하세요.

직접 설치하는 경우:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe tools\fetch_fonts.py
.venv\Scripts\python.exe main.py
```

관리자 권한은 필요하지 않습니다. 탐색기와 앱을 같은 일반 권한으로 실행해 주세요. 앱 소스 폴더와 변환 결과를 저장할 원본 폴더에 쓰기 권한이 필요합니다.

## EXE로 빌드

**Windows에서** `build.cmd`를 실행하세요. 패키지를 설치하고 PyInstaller로 `dist/CitrusDrop.exe`를 만듭니다.

GitHub의 `Windows EXE` 워크플로도 Windows x64 환경에서 테스트·아이콘 생성·빌드·EXE 실행 검사를 수행하고 단일 EXE를 Artifacts로 제공하고, 검증 성공 후 새 버전이면 Releases에 프리릴리즈로 게시합니다. EXE만 새 폴더에 복사한 뒤 내장 폰트·이미지 → PDF → PNG 변환·종료까지 검사합니다. 소스 변경 시 자동 실행되며 Actions에서 `Run workflow`로 다시 빌드할 수도 있습니다.

- 사용자 PC에 Python을 별도 설치하지 않고 배포할 수 있도록 만드는 구성입니다.
- **`CitrusDrop.exe` 하나만 전달하면 됩니다.** Qt·PDFium·라이브러리 데이터·폰트는 EXE 내부에 포함합니다.
- FFmpeg는 별도로 선택하거나 EXE 옆 `tools` 폴더에 배치합니다.
- Windows용 EXE는 Windows에서 빌드해야 합니다. Linux 빌드 결과를 Windows용으로 사용할 수 없습니다.
- 라이브러리 공지·프로젝트 제작 정보·폰트 라이선스는 EXE에 포함하며 `앱 정보`에서 읽을 수 있습니다. 재빌드할 때도 고지를 유지하세요. 자세한 내용은 THIRD_PARTY_NOTICES.md에 있습니다.

## 로고

프로젝트 로고 `assets/citrus-drop.svg`를 앱 창·트레이·EXE 아이콘에 연결했습니다. `tools/generate_icons.py`가 `assets/logo.png`와 여러 크기가 들어 있는 `assets/icon.ico`를 생성합니다. `build.cmd`와 GitHub 빌드에서 자동 실행합니다. 자세한 내용은 `assets/README.md`를 참고하세요.

## 폰트

기본 창·원형 메뉴·트레이 메뉴는 **Pretendard**를 사용합니다. 본문 14px, 보조 설명 12px, 주요 제목 28px를 기준으로 Regular·SemiBold·Bold 굵기를 구분했습니다. 앱에 폰트가 포함되어 사용자 PC에 별도로 설치할 필요가 없습니다.

Pretendard v1.3.9 원본은 **SIL Open Font License 1.1**로 배포되며 앱에 포함한 배포와 상업적 사용이 허용됩니다. 폰트는 수정하지 않았으며, 원본 저작권 고지와 라이선스는 `assets/fonts/OFL.txt`에 포함합니다. 폰트의 OFL은 앱 소스의 라이선스와 별도로 유지됩니다.

소스 설치·빌드 시 공식 저장소의 고정된 버전에서 원본 OTF 3개를 받아 SHA-256을 확인합니다. 앱 실행 중에는 폰트를 다운로드하거나 시스템에 설치하지 않습니다. 자세한 출처는 `assets/fonts/README.md`를 참고하세요.

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
| `citrus_drop/typography.py` | 앱 내 Pretendard 로딩·기본 글꼴 |
| `tools/fetch_fonts.py` | 설치·빌드 시 공식 원본 폰트 준비·해시 확인 |
| `CitrusDrop.spec` | EXE 패키징 구성 |

## 테스트

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

또는 `tests/run-tests.cmd`를 실행하세요. 자동 환경에서는 `--no-pause`를 추가합니다. Qt 테스트는 offscreen 환경에서 화면·메뉴·드롭 이벤트와 작업 스레드를 검사합니다. `python main.py --smoke-test`로 실제 앱 초기화·종료도 확인할 수 있습니다.

현재 검증 결과와 남은 Windows 실기기 항목은 VALIDATION.md에 기록합니다.

## 프리릴리즈 배포

- `main`의 Windows EXE 검사에 성공하면 현재 `pyproject.toml` 버전으로 프리릴리즈를 게시합니다. 기존에 게시된 버전의 EXE나 태그는 변경하지 않습니다.
- 새 배포는 `pyproject.toml`과 `citrus_drop/__init__.py`의 버전을 함께 올리고 `docs/releases/v버전.md`에 안내를 작성한 뒤 `main`에 반영합니다. README의 버전·다운로드 링크와 변경 내역도 함께 맞춰 주세요.
- EXE와 `SHA256SUMS.txt`를 함께 제공합니다. 게시 전 업로드를 완료하고, 게시 후 프리릴리즈 상태·파일 크기·파일 목록을 검사합니다.
- 실패로 남은 초안은 같은 커밋에서 다시 실행할 때만 이어서 게시합니다. 다른 커밋의 초안은 자동으로 수정하지 않습니다.
- 프리릴리즈는 GitHub의 `releases/latest`에 포함되지 않으므로 README는 해당 버전과 Releases 목록에 연결합니다.
- 현재 워크플로는 모든 배포를 프리릴리즈로 표시합니다. 정식 배포로 전환할 때 별도 변경이 필요합니다.
