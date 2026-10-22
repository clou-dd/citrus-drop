using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Threading;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace CitrusDrop
{
    internal static class Converter
    {
        public static string ConvertOne(string input, string target, string ffmpeg, CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            if (!File.Exists(input)) throw new FileNotFoundException("원본 파일을 찾을 수 없습니다.", input);
            bool allowed = Plans.ForFiles(new[] { input }, File.Exists(ffmpeg)).Exists(o => o.Id == target);
            if (!allowed || target == "zip" || target == "path" || target == "pdf")
                throw new InvalidOperationException("이 파일에서 지원하지 않는 변환입니다: " + target);
            string folder = Path.GetDirectoryName(input);
            string temp_dir = Path.Combine(folder, ".citrus-drop-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temp_dir);
            try
            {
                string temp_file = Path.Combine(temp_dir, "output." + target);
                bool native = Plans.Kind(input) == "image" && target != "webp";
                if (native)
                {
                    string decoded_input = input;
                    if (Path.GetExtension(input).Equals(".webp", StringComparison.OrdinalIgnoreCase))
                    {
                        decoded_input = Path.Combine(temp_dir, "decoded.png");
                        RunFfmpeg(input, decoded_input, "png", ffmpeg, token);
                    }
                    ConvertImage(decoded_input, temp_file, target, token);
                }
                else RunFfmpeg(input, temp_file, target, ffmpeg, token);
                token.ThrowIfCancellationRequested();
                if (!File.Exists(temp_file) || new FileInfo(temp_file).Length == 0)
                    throw new IOException("변환 결과가 비어 있습니다.");
                return Plans.Publish(temp_file, folder, Path.GetFileNameWithoutExtension(input) + "_converted", target);
            }
            finally { Cleanup(temp_dir); }
        }

        public static string Archive(string[] files, CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            if (files.Length == 0) throw new InvalidOperationException("압축할 파일이 없습니다.");
            string folder = Path.GetDirectoryName(files[0]);
            string temp_dir = Path.Combine(folder, ".citrus-drop-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temp_dir);
            try
            {
                string temporary = Path.Combine(temp_dir, "output.zip");
                HashSet<string> used = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                byte[] buffer = new byte[65536];
                using (FileStream output = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write))
                using (ZipArchive zip = new ZipArchive(output, ZipArchiveMode.Create, false, Encoding.UTF8))
                {
                    foreach (string file in files)
                    {
                        token.ThrowIfCancellationRequested();
                        string entry_name = Path.GetFileName(file);
                        for (int i = 2; !used.Add(entry_name); i++)
                            entry_name = Path.GetFileNameWithoutExtension(file) + "_" + i + Path.GetExtension(file);
                        ZipArchiveEntry entry = zip.CreateEntry(entry_name, CompressionLevel.Optimal);
                        using (Stream source = File.OpenRead(file))
                        using (Stream dest = entry.Open())
                        {
                            int read;
                            while ((read = source.Read(buffer, 0, buffer.Length)) > 0)
                            { token.ThrowIfCancellationRequested(); dest.Write(buffer, 0, read); }
                        }
                    }
                }
                token.ThrowIfCancellationRequested();
                return Plans.Publish(temporary, folder, "Citrus_" + DateTime.Now.ToString("yyyyMMdd_HHmmss"), "zip");
            }
            finally { Cleanup(temp_dir); }
        }

        internal static void Cleanup(string directory)
        {
            try { if (Directory.Exists(directory)) Directory.Delete(directory, true); }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
        }

        internal static void ConvertImage(string input, string output, string target, CancellationToken token)
        {
            BitmapSource source;
            using (FileStream stream = File.OpenRead(input))
            {
                BitmapDecoder decoder = BitmapDecoder.Create(stream, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);
                if (decoder.Frames.Count == 0) throw new IOException("이미지 프레임이 없습니다.");
                BitmapFrame frame = decoder.Frames[0];
                if ((long)frame.PixelWidth * frame.PixelHeight > 100000000)
                    throw new IOException("1억 픽셀보다 큰 이미지는 이 버전에서 처리하지 않습니다.");
                source = new FormatConvertedBitmap(frame, PixelFormats.Bgra32, null, 0);
                int orientation = Orientation(frame.Metadata as BitmapMetadata);
                Matrix matrix = Matrix.Identity;
                switch (orientation)
                {
                    case 2: matrix = new Matrix(-1, 0, 0, 1, 0, 0); break;
                    case 3: matrix = new Matrix(-1, 0, 0, -1, 0, 0); break;
                    case 4: matrix = new Matrix(1, 0, 0, -1, 0, 0); break;
                    case 5: matrix = new Matrix(0, 1, 1, 0, 0, 0); break;
                    case 6: matrix = new Matrix(0, 1, -1, 0, 0, 0); break;
                    case 7: matrix = new Matrix(0, -1, -1, 0, 0, 0); break;
                    case 8: matrix = new Matrix(0, -1, 1, 0, 0, 0); break;
                }
                if (!matrix.IsIdentity) source = new TransformedBitmap(source, new MatrixTransform(matrix));
                source.Freeze();
            }
            token.ThrowIfCancellationRequested();
            if (target == "jpg" || target == "bmp") source = OnWhite(source, token);
            BitmapEncoder encoder;
            switch (target)
            {
                case "png": encoder = new PngBitmapEncoder(); break;
                case "jpg": encoder = new JpegBitmapEncoder { QualityLevel = 90 }; break;
                case "bmp": encoder = new BmpBitmapEncoder(); break;
                case "tiff": encoder = new TiffBitmapEncoder { Compression = TiffCompressOption.Zip }; break;
                case "gif": encoder = new GifBitmapEncoder(); break;
                default: throw new InvalidOperationException("지원하지 않는 이미지 형식입니다.");
            }
            // No source metadata is copied. Animated GIF / multipage TIFF: first frame only.
            encoder.Frames.Add(BitmapFrame.Create(source));
            using (FileStream stream = new FileStream(output, FileMode.CreateNew, FileAccess.Write)) encoder.Save(stream);
            token.ThrowIfCancellationRequested();
        }

        private static int Orientation(BitmapMetadata metadata)
        {
            if (metadata == null) return 1;
            foreach (string query in new[] { "/app1/ifd/{ushort=274}", "/ifd/{ushort=274}" })
            {
                try { object value = metadata.GetQuery(query); if (value != null) return System.Convert.ToInt32(value); }
                catch (Exception ex)
                { if (!(ex is NotSupportedException) && !(ex is ArgumentException) && !(ex is System.Runtime.InteropServices.COMException)) throw; }
            }
            return 1;
        }

        private static BitmapSource OnWhite(BitmapSource source, CancellationToken token)
        {
            BitmapSource bgra = new FormatConvertedBitmap(source, PixelFormats.Bgra32, null, 0);
            int stride = checked(bgra.PixelWidth * 4);
            byte[] pixels = new byte[checked(stride * bgra.PixelHeight)];
            bgra.CopyPixels(pixels, stride, 0);
            for (int row = 0; row < bgra.PixelHeight; row++)
            {
                token.ThrowIfCancellationRequested();
                int end = (row + 1) * stride;
                for (int p = row * stride; p < end; p += 4)
                {
                    int alpha = pixels[p + 3];
                    for (int c = 0; c < 3; c++) pixels[p + c] = (byte)((pixels[p + c] * alpha + 255 * (255 - alpha) + 127) / 255);
                    pixels[p + 3] = 255;
                }
            }
            BitmapSource result = BitmapSource.Create(bgra.PixelWidth, bgra.PixelHeight,
                bgra.DpiX > 0 ? bgra.DpiX : 96, bgra.DpiY > 0 ? bgra.DpiY : 96, PixelFormats.Bgra32, null, pixels, stride);
            result.Freeze(); return result;
        }

        private static void RunFfmpeg(string input, string output, string target, string executable, CancellationToken token)
        {
            if (!File.Exists(executable)) throw new FileNotFoundException("설정에서 ffmpeg.exe를 선택해 주세요.");
            string codec;
            switch (target)
            {
                case "webp": codec = "-frames:v 1 -c:v libwebp -quality 90"; break;
                case "png": codec = "-frames:v 1 -c:v png"; break;
                case "jpg": codec = "-frames:v 1 -c:v mjpeg -q:v 2 -vf format=rgb24"; break;
                case "bmp": codec = "-frames:v 1 -c:v bmp -pix_fmt bgr24"; break;
                case "tiff": codec = "-frames:v 1 -c:v tiff"; break;
                case "gif": codec = "-frames:v 1 -vf split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"; break;
                case "mp4": codec = "-map 0:v:0 -map 0:a:0? -vf scale=trunc(iw/2)*2:trunc(ih/2)*2 -c:v libx264 -crf 22 -preset medium -pix_fmt yuv420p -c:a aac -movflags +faststart"; break;
                case "webm": codec = "-map 0:v:0 -map 0:a:0? -c:v libvpx-vp9 -crf 32 -b:v 0 -c:a libopus"; break;
                case "mp3": codec = "-vn -map 0:a:0 -c:a libmp3lame -q:a 2"; break;
                case "wav": codec = "-vn -map 0:a:0 -c:a pcm_s16le"; break;
                case "flac": codec = "-vn -map 0:a:0 -c:a flac"; break;
                case "ogg": codec = "-vn -map 0:a:0 -c:a libvorbis -q:a 5"; break;
                default: throw new InvalidOperationException("지원하지 않는 FFmpeg 출력 형식입니다.");
            }
            StringBuilder errors = new StringBuilder();
            object error_lock = new object();
            ProcessStartInfo start = new ProcessStartInfo(executable,
                "-nostdin -hide_banner -loglevel error -n -i " + Plans.Quote(input) + " " + codec + " " + Plans.Quote(output));
            start.UseShellExecute = false; start.CreateNoWindow = true; start.RedirectStandardError = true;
            using (Process process = new Process { StartInfo = start })
            {
                process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e)
                { if (e.Data != null) lock (error_lock) { if (errors.Length < 12000) errors.AppendLine(e.Data); } };
                process.Start(); process.BeginErrorReadLine();
                while (!process.WaitForExit(100))
                {
                    if (!token.IsCancellationRequested) continue;
                    try { process.Kill(); } catch (InvalidOperationException) { }
                    process.WaitForExit(); token.ThrowIfCancellationRequested();
                }
                process.WaitForExit(); token.ThrowIfCancellationRequested();
                if (process.ExitCode != 0)
                {
                    string detail; lock (error_lock) detail = errors.ToString().Trim();
                    throw new IOException("FFmpeg 변환 실패 (" + process.ExitCode + "): " + detail);
                }
            }
        }
    }
}
