using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Threading;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace CitrusDrop
{
    internal static class SmokeTests
    {
        private static int checks;
        private static void Check(bool condition, string name)
        { if (!condition) throw new Exception("FAIL: " + name); checks++; Console.WriteLine("PASS: " + name); }
        [STAThread]
        public static int Main()
        {
            string root = Path.Combine(Path.GetTempPath(), "CitrusDropTests_" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(root);
            try
            {
                string images = Path.Combine(root, "한글 공백 & $ 폴더"); Directory.CreateDirectory(images);
                string input = Path.Combine(images, "투명 이미지.png");
                byte[] source_pixels = new byte[32 * 2 * 4];
                for (int y = 0; y < 2; y++)
                    for (int x = 16; x < 32; x++)
                    { int p = (y * 32 + x) * 4; source_pixels[p + 2] = 255; source_pixels[p + 3] = 255; }
                WritePng(input, source_pixels, 32, 2);
                byte[] original = File.ReadAllBytes(input);
                string first = Converter.ConvertOne(input, "png", "", CancellationToken.None);
                string second = Converter.ConvertOne(input, "png", "", CancellationToken.None);
                Check(first != second && File.Exists(first) && File.Exists(second), "collision-safe output files");
                Check(File.ReadAllBytes(input).SequenceEqual(original), "original file unchanged");
                foreach (string target in new[] { "jpg", "bmp", "tiff", "gif" })
                {
                    string output = Converter.ConvertOne(input, target, "", CancellationToken.None);
                    BitmapFrame image = ReadFrame(output);
                    Check(image.PixelWidth == 32 && image.PixelHeight == 2, target + " dimensions");
                    if (target == "jpg" || target == "bmp")
                    {
                        BitmapSource decoded = new FormatConvertedBitmap(image, PixelFormats.Bgra32, null, 0);
                        byte[] pixels = new byte[32 * 2 * 4]; decoded.CopyPixels(pixels, 32 * 4, 0);
                        Check(pixels[0] + pixels[1] + pixels[2] > 650, target + " transparent pixel on white");
                    }
                }
                WriteOrientedJpeg(Path.Combine(images, "oriented.jpg"));
                string oriented = Converter.ConvertOne(Path.Combine(images, "oriented.jpg"), "png", "", CancellationToken.None);
                BitmapFrame rotated = ReadFrame(oriented);
                Check(rotated.PixelWidth == 3 && rotated.PixelHeight == 2, "EXIF orientation applied");

                string a = Path.Combine(root, "a"), b = Path.Combine(root, "b"); Directory.CreateDirectory(a); Directory.CreateDirectory(b);
                string fa = Path.Combine(a, "same.txt"), fb = Path.Combine(b, "same.txt");
                File.WriteAllText(fa, "first", Encoding.UTF8); File.WriteAllText(fb, "second", Encoding.UTF8);
                string archive = Converter.Archive(new[] { fa, fb }, CancellationToken.None);
                using (FileStream stream = File.OpenRead(archive))
                using (ZipArchive zip = new ZipArchive(stream, ZipArchiveMode.Read))
                {
                    Check(zip.Entries.Count == 2, "ZIP retains both duplicate basenames");
                    Check(zip.Entries.Select(e => e.FullName).Distinct(StringComparer.OrdinalIgnoreCase).Count() == 2, "ZIP unique entry names");
                    using (StreamReader reader = new StreamReader(zip.Entries[0].Open())) Check(reader.ReadToEnd() == "first", "ZIP entry content");
                }
                Check(!Plans.ForFiles(new[] { input }, false).Any(o => o.Id == "webp"), "WebP disabled without FFmpeg");
                Check(Plans.ForFiles(new[] { input }, false).Any(o => o.Id == "pdf"), "image-to-PDF available without external tools");
                string made_pdf = PdfTools.FromImages(new[] { input, Path.Combine(images, "oriented.jpg") }, "", CancellationToken.None, null);
                byte[] pdf_bytes = File.ReadAllBytes(made_pdf);
                string pdf_syntax = Encoding.ASCII.GetString(pdf_bytes);
                Check(pdf_syntax.StartsWith("%PDF-1.4") && pdf_syntax.Contains("/Count 2"), "two ordered image pages in a PDF");
                Check(pdf_syntax.Contains("/DCTDecode") && pdf_syntax.Contains("%%EOF"), "PDF image objects and trailer");
                Check(File.ReadAllBytes(input).SequenceEqual(original), "PDF creation preserves original image");
                Check(Plans.Kind(made_pdf) == "pdf", "PDF input classification");
                Check(!Plans.ForFiles(new[] { made_pdf }, false).Any(o => o.Id.StartsWith("pdf_")), "PDF extraction disabled without engine");
                Check(Plans.ForFiles(new[] { made_pdf }, false, true, false).Any(o => o.Id == "pdf_png") && !Plans.ForFiles(new[] { made_pdf }, false, true, false).Any(o => o.Id == "pdf_txt"), "renderer and text capabilities separate");
                Check(Plans.ForFiles(new[] { input, fa }, true).All(o => o.Id == "zip" || o.Id == "path"), "mixed formats expose only shared actions");
                Check(Plans.Quote("C:\\한글 공백\\file.png") == "\"C:\\한글 공백\\file.png\"", "argument quoting with spaces");
                Check(Plans.Quote("trailing\\") == "\"trailing\\\\\"", "argument quoting trailing backslash");
                Check(Plans.Quote("a\"b") == "\"a\\\"b\"", "argument quoting embedded quote");
                string sentinel_temp = Path.Combine(root, "new.tmp"); File.WriteAllText(sentinel_temp, "new");
                string existing = Path.Combine(root, "protected.txt"); File.WriteAllText(existing, "old");
                string published = Plans.Publish(sentinel_temp, root, "protected", "txt");
                Check(File.ReadAllText(existing) == "old" && File.ReadAllText(published) == "new", "publish never overwrites existing file");
                CancellationTokenSource cancelled = new CancellationTokenSource(); cancelled.Cancel();
                bool cancelled_image = false, cancelled_zip = false;
                try { Converter.ConvertOne(input, "png", "", cancelled.Token); } catch (OperationCanceledException) { cancelled_image = true; }
                try { Converter.Archive(new[] { input }, cancelled.Token); } catch (OperationCanceledException) { cancelled_zip = true; }
                Check(cancelled_image && cancelled_zip, "cancelled jobs do not start");
                bool cancelled_pdf = false;
                try { PdfTools.FromImages(new[] { input }, "", cancelled.Token, null); } catch (OperationCanceledException) { cancelled_pdf = true; }
                Check(cancelled_pdf, "cancelled PDF job does not start");
                Check(Directory.GetDirectories(root, ".citrus-drop-*", SearchOption.AllDirectories).Length == 0, "temporary directories cleaned");
                Console.WriteLine("ALL PASSED: " + checks + " checks"); return 0;
            }
            catch (Exception ex) { Console.Error.WriteLine(ex); return 1; }
            finally { try { Directory.Delete(root, true); } catch (IOException) { } }
        }
        private static BitmapFrame ReadFrame(string path)
        { using (FileStream stream = File.OpenRead(path)) return BitmapDecoder.Create(stream, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad).Frames[0]; }
        private static void WritePng(string path, byte[] bytes, int width, int height)
        {
            BitmapSource source = BitmapSource.Create(width, height, 96, 96, PixelFormats.Bgra32, null, bytes, width * 4);
            PngBitmapEncoder encoder = new PngBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(source));
            using (FileStream stream = File.Create(path)) encoder.Save(stream);
        }
        private static void WriteOrientedJpeg(string path)
        {
            byte[] pixels = new byte[2 * 3 * 4];
            for (int i = 0; i < pixels.Length; i += 4) { pixels[i] = 120; pixels[i + 1] = 80; pixels[i + 2] = 240; pixels[i + 3] = 255; }
            BitmapSource source = BitmapSource.Create(2, 3, 96, 96, PixelFormats.Bgra32, null, pixels, 8);
            BitmapMetadata metadata = new BitmapMetadata("jpg"); metadata.SetQuery("/app1/ifd/{ushort=274}", (ushort)6);
            JpegBitmapEncoder encoder = new JpegBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(source, null, metadata, null));
            using (FileStream stream = File.Create(path)) encoder.Save(stream);
        }
    }
}
