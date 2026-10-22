using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;

namespace CitrusDrop
{
    internal static partial class PdfTools
    {
        public static string Tool(string directory, string name)
        {
            if (String.IsNullOrWhiteSpace(directory)) return "";
            string path = Path.Combine(directory, name + ".exe");
            return File.Exists(path) ? path : "";
        }

        public static string ConvertPdf(string input, string target, string directory, CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            if (!File.Exists(input) || Plans.Kind(input) != "pdf") throw new IOException("PDF 파일을 찾을 수 없습니다.");
            bool text = target == "pdf_txt";
            if (!text && target != "pdf_png" && target != "pdf_jpg") throw new ArgumentException("지원하지 않는 PDF 변환입니다.");
            string executable = Tool(directory, text ? "pdftotext" : "pdftoppm");
            if (!File.Exists(executable)) throw new FileNotFoundException("PDF 엔진 선택에서 Poppler의 pdftoppm.exe를 지정해 주세요. TXT 변환에는 같은 폴더의 pdftotext.exe도 필요합니다.");
            string folder = Path.GetDirectoryName(input);
            string temporary = Path.Combine(folder, ".citrus-drop-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temporary);
            try
            {
                if (text)
                {
                    string output = Path.Combine(temporary, "output.txt");
                    Run(executable, "-enc UTF-8 -layout " + Plans.Quote(input) + " " + Plans.Quote(output), token);
                    if (!File.Exists(output)) throw new IOException("텍스트 출력 파일이 생성되지 않았습니다.");
                    // An empty result is valid for a scan. No OCR is performed.
                    token.ThrowIfCancellationRequested();
                    return Plans.Publish(output, folder, Path.GetFileNameWithoutExtension(input) + "_converted", "txt");
                }
                string pages = Path.Combine(temporary, "pages"); Directory.CreateDirectory(pages);
                bool jpeg = target == "pdf_jpg";
                string prefix = Path.Combine(pages, "page");
                string args = (jpeg ? "-jpeg -jpegopt quality=90" : "-png") + " -r 150";
                Run(executable, args + " " + Plans.Quote(input) + " " + Plans.Quote(prefix), token);
                string[] output_files = Directory.GetFiles(pages, jpeg ? "page-*.jpg" : "page-*.png");
                if (output_files.Length == 0 || output_files.Any(p => new FileInfo(p).Length == 0))
                    throw new IOException("PDF 페이지 이미지가 생성되지 않았습니다.");
                token.ThrowIfCancellationRequested();
                return Plans.PublishDirectory(pages, folder, Path.GetFileNameWithoutExtension(input) + "_" + (jpeg ? "jpg" : "png") + "_pages");
            }
            finally { Cleanup(temporary); }
        }

        private static void Cleanup(string directory)
        {
            try { if (Directory.Exists(directory)) Directory.Delete(directory, true); }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
        }

        private static void Run(string executable, string arguments, CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            ProcessStartInfo start = new ProcessStartInfo(executable, arguments)
            { UseShellExecute = false, CreateNoWindow = true, RedirectStandardError = true };
            StringBuilder errors = new StringBuilder(); object error_lock = new object();
            using (Process process = new Process { StartInfo = start })
            {
                process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e)
                { if (e.Data != null) lock (error_lock) { if (errors.Length < 12000) errors.AppendLine(e.Data); } };
                try
                {
                    process.Start(); process.BeginErrorReadLine();
                    while (!process.WaitForExit(100)) token.ThrowIfCancellationRequested();
                    process.WaitForExit(); token.ThrowIfCancellationRequested();
                    if (process.ExitCode != 0)
                    {
                        string detail; lock (error_lock) detail = errors.ToString().Trim();
                        throw new IOException("PDF 변환 실패 (" + process.ExitCode + "). 암호가 필요하거나 손상된 PDF인지 확인해 주세요. " + detail);
                    }
                }
                finally
                {
                    try { if (!process.HasExited) { process.Kill(); process.WaitForExit(); } }
                    catch (InvalidOperationException) { }
                }
            }
        }
    }
}
