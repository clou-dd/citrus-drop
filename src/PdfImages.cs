using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Windows.Media.Imaging;

namespace CitrusDrop
{
    internal static partial class PdfTools
    {
        public static string FromImages(string[] files, string ffmpeg, CancellationToken token, Action<int, int> progress)
        {
            token.ThrowIfCancellationRequested();
            if (files.Length == 0 || !Plans.ForFiles(files, File.Exists(ffmpeg)).Any(o => o.Id == "pdf"))
                throw new InvalidOperationException("지원되는 이미지 파일만 선택해 주세요. WebP는 FFmpeg가 필요합니다.");
            string folder = Path.GetDirectoryName(files[0]);
            string temporary = Path.Combine(folder, ".citrus-drop-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temporary);
            try
            {
                List<PdfImagePage> pages = new List<PdfImagePage>();
                for (int i = 0; i < files.Length; i++)
                {
                    token.ThrowIfCancellationRequested();
                    if (progress != null) progress(i + 1, files.Length);
                    string jpeg = Path.Combine(temporary, "image-" + i.ToString("D6") + ".jpg");
                    if (Path.GetExtension(files[i]).Equals(".webp", StringComparison.OrdinalIgnoreCase))
                    {
                        // The existing converter normalizes transparency and orientation.
                        // Copy into our temporary directory so its published intermediate stays private.
                        string local_input = Path.Combine(temporary, "source-" + i + ".webp");
                        File.Copy(files[i], local_input, false);
                        string converted = Converter.ConvertOne(local_input, "jpg", ffmpeg, token);
                        File.Move(converted, jpeg); File.Delete(local_input);
                    }
                    else Converter.ConvertImage(files[i], jpeg, "jpg", token);
                    using (FileStream stream = File.OpenRead(jpeg))
                    {
                        BitmapFrame frame = BitmapDecoder.Create(stream, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad).Frames[0];
                        pages.Add(new PdfImagePage { JpegPath = jpeg, PixelWidth = frame.PixelWidth, PixelHeight = frame.PixelHeight });
                    }
                }
                string output = Path.Combine(temporary, "output.pdf");
                PdfDocumentWriter.Write(output, pages, token);
                token.ThrowIfCancellationRequested();
                string stem = files.Length == 1 ? Path.GetFileNameWithoutExtension(files[0]) + "_converted" : "Citrus_images_" + DateTime.Now.ToString("yyyyMMdd_HHmmss");
                return Plans.Publish(output, folder, stem, "pdf");
            }
            finally { Converter.Cleanup(temporary); }
        }

    }
}
