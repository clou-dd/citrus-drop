# Pretendard

Citrus Drop uses the original Pretendard v1.3.9 by Kil Hyung-jin under
the SIL Open Font License 1.1. See [OFL.txt](OFL.txt) for the complete copyright
notice and license. The font itself is not modified, renamed, or subsetted.
It is loaded only for this application and is not installed as a system font.

`Setup.cmd` and the Windows build workflow run `tools/fetch_fonts.py` to download
Regular, SemiBold and Bold OTF files from the official repository. These static
faces keep font weight selection consistent across Qt's Windows and Linux backends.
The script pins upstream commit `5c41199ea0024a9e0b2cb31735265056e5472d76`
and verifies SHA-256:

```
Pretendard-Regular.otf  3ffbacde6ab8411f1d2db54bb9b1f0b3ee2a738932033722cf0388c06aed1c93
Pretendard-SemiBold.otf c89bc43027dc7cde5726e96223376f8eec09302b2fc1f8147fd5b57cfc376118
Pretendard-Bold.otf     2e91915fab54df71cc9598ebf608b2bdb54c6fe3c066ac61dff0bc44fca71cc7
```

The downloaded OTFs are ignored by Git, but are included with this license in the
packaged application. No font download is performed while the app runs.

Source: https://github.com/orioncactus/pretendard/tree/v1.3.9
