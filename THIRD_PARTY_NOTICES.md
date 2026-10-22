# Third-party components

Citrus Drop source is provided under LICENSE.txt (MIT).
Its dependencies are separate projects with their own licenses:

| Component | Purpose | License information |
| --- | --- | --- |
| PySide6, Shiboken6, Qt | Desktop UI and tray | LGPL-3.0 / GPL / commercial options; see the distribution's license files |
| Pillow | Image codecs | MIT-CMU and bundled codec licenses |
| pypdfium2 | PDFium Python bindings | Apache-2.0 / BSD-3-Clause; see its license files |
| PDFium and its dependencies | PDF rendering and text | BSD-style and individual third-party licenses in pypdfium2's distribution |
| ReportLab | PDF creation | BSD license and bundled data/font notices |
| PyInstaller | Build tool | GPL with bootloader exception; see the PyInstaller distribution |

The packaging specification copies installed package metadata and the PDFium
package's data/license files. Keep those notices and the supplied shared
libraries when distributing the application folder. Review the component's
complete license terms for your chosen distribution.

FFmpeg is optional and is not included or downloaded by Citrus Drop. Its
license depends on the FFmpeg build and enabled libraries. Users select their
own local executable. Network access is used by Setup.cmd/build.cmd to install
Python dependencies; conversion itself does not upload files.

Sources:
- https://doc.qt.io/qtforpython-6/licenses.html
- https://python-pillow.org/
- https://github.com/pypdfium2-team/pypdfium2
- https://www.reportlab.com/
- https://pyinstaller.org/
