using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace CitrusDrop
{
    internal sealed class Operation
    {
        public readonly string Id;
        public readonly string Label;
        public readonly string Description;
        public Operation(string id, string label, string description)
        { Id = id; Label = label; Description = description; }
        public override string ToString() { return Label + "  ·  " + Description; }
    }

    internal static class Plans
    {
        private static readonly HashSet<string> images = Set(".png,.jpg,.jpeg,.bmp,.tif,.tiff,.gif,.webp");
        private static readonly HashSet<string> videos = Set(".mp4,.mov,.mkv,.webm,.avi,.wmv,.m4v");
        private static readonly HashSet<string> audio = Set(".mp3,.m4a,.wav,.flac,.ogg,.opus,.aiff,.aif,.wma");
        private static HashSet<string> Set(string s)
        { return new HashSet<string>(s.Split(','), StringComparer.OrdinalIgnoreCase); }
        public static string Kind(string path)
        {
            string ext = Path.GetExtension(path);
            if (images.Contains(ext)) return "image";
            if (videos.Contains(ext)) return "video";
            if (audio.Contains(ext)) return "audio";
            if (ext.Equals(".pdf", StringComparison.OrdinalIgnoreCase)) return "pdf";
            return "other";
        }
        public static string[] Files(IEnumerable<string> paths)
        {
            if (paths == null) return new string[0];
            return paths.Where(p => !String.IsNullOrWhiteSpace(p) && File.Exists(p))
                .Select(Path.GetFullPath).Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
        }
        public static List<Operation> ForFiles(string[] files, bool has_ffmpeg, bool has_pdf_renderer = false, bool has_pdf_text = false)
        {
            List<Operation> list = new List<Operation>();
            if (files.Length == 0) return list;
            string kind = Kind(files[0]);
            if (files.Any(p => Kind(p) != kind)) kind = "other";
            bool needs_external_image = files.Any(p => Path.GetExtension(p).Equals(".webp", StringComparison.OrdinalIgnoreCase));
            if (kind == "image" && (!needs_external_image || has_ffmpeg))
            {
                Add(list, "png", "PNG", "투명 배경 유지");
                Add(list, "jpg", "JPG", "품질 90 · 흰 배경");
                Add(list, "bmp", "BMP", "흰 배경");
                Add(list, "tiff", "TIFF", "정지 이미지");
                Add(list, "gif", "GIF", "정지 이미지 · 색상 축소");
                if (has_ffmpeg) Add(list, "webp", "WebP", "FFmpeg · 품질 90");
                Add(list, "pdf", "PDF 만들기", "선택 순서대로 하나의 PDF");
            }
            else if (kind == "pdf")
            {
                if (has_pdf_renderer)
                {
                    Add(list, "pdf_png", "PNG", "PDF 전체 페이지 · 150 DPI");
                    Add(list, "pdf_jpg", "JPG", "PDF 전체 페이지 · 150 DPI");
                }
                if (has_pdf_text) Add(list, "pdf_txt", "TXT", "PDF 텍스트 추출 · OCR 제외");
            }
            else if (has_ffmpeg && (kind == "video" || kind == "audio"))
            {
                if (kind == "video")
                {
                    Add(list, "mp4", "MP4", "H.264 / AAC");
                    Add(list, "webm", "WebM", "VP9 / Opus");
                }
                Add(list, "mp3", "MP3", "오디오 변환 / 추출");
                Add(list, "wav", "WAV", "PCM 오디오");
                Add(list, "flac", "FLAC", "무손실 오디오");
                Add(list, "ogg", "OGG", "Vorbis 오디오");
            }
            Add(list, "zip", "ZIP", "선택 파일을 하나로 압축");
            Add(list, "path", "경로 복사", "파일 경로를 클립보드에");
            return list;
        }
        private static void Add(List<Operation> list, string id, string label, string desc)
        { list.Add(new Operation(id, label, desc)); }

        // CommandLineToArgvW / C-runtime quoting rules. Never launch a command shell.
        public static string Quote(string value)
        {
            System.Text.StringBuilder b = new System.Text.StringBuilder("\"");
            int slashes = 0;
            foreach (char c in value)
            {
                if (c == '\\') { slashes++; continue; }
                if (c == '"') { b.Append('\\', slashes * 2 + 1); b.Append('"'); }
                else { b.Append('\\', slashes); b.Append(c); }
                slashes = 0;
            }
            b.Append('\\', slashes * 2); b.Append('"');
            return b.ToString();
        }

        public static string Publish(string temporary_path, string folder, string stem, string extension)
        {
            for (int i = 1; i < 10000; i++)
            {
                string suffix = i == 1 ? "" : "_" + i;
                string destination = Path.Combine(folder, stem + suffix + "." + extension);
                try { File.Move(temporary_path, destination); return destination; }
                catch (IOException) { if (!File.Exists(destination) && !Directory.Exists(destination)) throw; }
            }
            throw new IOException("출력 파일 이름을 만들 수 없습니다. 같은 이름의 파일을 정리해 주세요.");
        }

        public static string PublishDirectory(string temporary_path, string folder, string stem)
        {
            for (int i = 1; i < 10000; i++)
            {
                string destination = Path.Combine(folder, stem + (i == 1 ? "" : "_" + i));
                try { Directory.Move(temporary_path, destination); return destination; }
                catch (IOException) { if (!File.Exists(destination) && !Directory.Exists(destination)) throw; }
            }
            throw new IOException("출력 폴더 이름을 만들 수 없습니다.");
        }
    }
}
