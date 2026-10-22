using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;

namespace CitrusDrop
{
    // Runs the production PDF writer and Poppler process path, without WPF.
    // Arguments: isolated test directory, tool directory, landscape JPEG,
    // portrait JPEG, text PDF fixture. The caller owns cleanup of its fixtures.
    internal static class PortablePdfTests
    {
        private static int checks;
        private static void Check(bool condition, string name)
        { if (!condition) throw new Exception("FAIL: " + name); checks++; Console.WriteLine("PASS: " + name); }
        public static int Main(string[] args)
        {
            try
            {
                if (args.Length != 5) throw new ArgumentException("Expected 5 test fixture arguments.");
                string root = Path.GetFullPath(args[0]); Directory.CreateDirectory(root);
                string tools = Path.GetFullPath(args[1]);
                string pdf = Path.Combine(root, "한글 공백 & $ PDF.pdf");
                PdfDocumentWriter.Write(pdf, new List<PdfImagePage>
                {
                    new PdfImagePage { JpegPath = args[2], PixelWidth = 800, PixelHeight = 400 },
                    new PdfImagePage { JpegPath = args[3], PixelWidth = 400, PixelHeight = 800 }
                }, CancellationToken.None);
                byte[] original = File.ReadAllBytes(pdf);
                Check(original.Length > 100, "writer generated PDF");
                string png = PdfTools.ConvertPdf(pdf, "pdf_png", tools, CancellationToken.None);
                Check(Directory.GetFiles(png, "*.png").Length == 2, "PDF to PNG exports every page");
                string again = PdfTools.ConvertPdf(pdf, "pdf_png", tools, CancellationToken.None);
                Check(again != png && Directory.GetFiles(png, "*.png").Length == 2, "existing page folder preserved");
                string jpg = PdfTools.ConvertPdf(pdf, "pdf_jpg", tools, CancellationToken.None);
                Check(Directory.GetFiles(jpg, "*.jpg").Length == 2, "PDF to JPG exports every page");
                Check(File.ReadAllBytes(pdf).SequenceEqual(original), "source PDF unchanged");
                string text = PdfTools.ConvertPdf(Path.GetFullPath(args[4]), "pdf_txt", tools, CancellationToken.None);
                Check(File.ReadAllText(text).Contains("Citrus PDF text fixture"), "PDF to UTF-8 text");
                string scan_text = PdfTools.ConvertPdf(pdf, "pdf_txt", tools, CancellationToken.None);
                Check(File.ReadAllText(scan_text).Trim().Length == 0, "image-only PDF produces no invented OCR text");
                string bad = Path.Combine(root, "broken.pdf"); File.WriteAllText(bad, "This is not a PDF.");
                bool rejected = false;
                try { PdfTools.ConvertPdf(bad, "pdf_png", tools, CancellationToken.None); }
                catch (IOException) { rejected = true; }
                Check(rejected && !Directory.Exists(Path.Combine(root, "broken_png_pages")), "invalid PDF leaves no final folder");
                CancellationTokenSource cancelled = new CancellationTokenSource(); cancelled.Cancel();
                bool stopped = false;
                try { PdfTools.ConvertPdf(pdf, "pdf_png", tools, cancelled.Token); } catch (OperationCanceledException) { stopped = true; }
                Check(stopped, "pre-cancelled PDF conversion rejected");
                Check(Directory.GetDirectories(root, ".citrus-drop-*").Length == 0, "PDF temporary directories cleaned");
                Check(Plans.ForFiles(new[] { pdf }, false, true, true).Count(o => o.Id.StartsWith("pdf_")) == 3, "PDF menu exposes PNG JPG TXT");
                Console.WriteLine("ALL PASSED: " + checks + " portable PDF checks"); return 0;
            }
            catch (Exception ex) { Console.Error.WriteLine(ex); return 1; }
        }
    }
}
