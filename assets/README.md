# 프로젝트 로고

- `assets/citrus-drop.svg`: 로고 원본입니다.
- `assets/logo.png`: SVG에서 생성한 512px PNG입니다.
- `assets/icon.ico`: 같은 SVG에서 생성한 16·24·32·48·64·128·256px Windows 아이콘입니다. 앱 창·트레이·EXE 파일에서 사용합니다.
- 로고를 수정하면 `.venv\Scripts\python.exe tools\generate_icons.py`로 PNG/ICO를 다시 만드세요. `build.cmd`와 GitHub Windows 빌드에서도 자동 생성합니다.
- EXE 파일에 포함된 아이콘을 바꾸려면 다시 빌드해야 합니다. 앱은 ICO → PNG → SVG 순서로 읽고, 모두 없으면 임시 C 아이콘을 표시합니다.
- 소스 실행에서는 프로젝트의 assets 폴더를 읽습니다. 패키지에는 이 폴더가 포함됩니다. EXE 옆에 assets 폴더를 별도로 두면 해당 로고를 우선 읽습니다.
