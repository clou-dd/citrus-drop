using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Threading;

namespace CitrusDrop
{
    internal sealed class PdfImagePage
    {
        public string JpegPath;
        public int PixelWidth;
        public int PixelHeight;
    }

    // Writes only our own JPEG image pages. It does not parse arbitrary PDFs.
    // PDF 1.4: RGB JPEG XObjects, a page tree and a conventional cross-reference table.
    internal static class PdfDocumentWriter
    {
        private static string Number(double value) { return value.ToString("0.###", CultureInfo.InvariantCulture); }
        private static void Text(Stream stream, string value)
        { byte[] bytes = Encoding.ASCII.GetBytes(value); stream.Write(bytes, 0, bytes.Length); }

        public static void Write(string output, IList<PdfImagePage> pages, CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            if (pages == null || pages.Count == 0) throw new ArgumentException("PDF에 넣을 이미지가 없습니다.");
            foreach (PdfImagePage page in pages)
                if (page.PixelWidth <= 0 || page.PixelHeight <= 0 || !File.Exists(page.JpegPath))
                    throw new ArgumentException("PDF 페이지의 이미지 정보가 올바르지 않습니다.");
            int objects = checked(2 + pages.Count * 3);
            long[] offsets = new long[objects + 1];
            using (FileStream stream = new FileStream(output, FileMode.CreateNew, FileAccess.Write))
            {
                Text(stream, "%PDF-1.4\n");
                stream.Write(new byte[] { 37, 226, 227, 207, 211, 10 }, 0, 6);
                Object(stream, offsets, 1, "<< /Type /Catalog /Pages 2 0 R >>");
                StringBuilder kids = new StringBuilder();
                for (int i = 0; i < pages.Count; i++) kids.Append((3 + i * 3).ToString(CultureInfo.InvariantCulture)).Append(" 0 R ");
                Object(stream, offsets, 2, "<< /Type /Pages /Count " + pages.Count.ToString(CultureInfo.InvariantCulture) + " /Kids [ " + kids + "] >>");
                byte[] buffer = new byte[65536];
                for (int i = 0; i < pages.Count; i++)
                {
                    token.ThrowIfCancellationRequested();
                    PdfImagePage image = pages[i];
                    bool landscape = image.PixelWidth > image.PixelHeight;
                    double page_width = landscape ? 841.89 : 595.276;
                    double page_height = landscape ? 595.276 : 841.89;
                    const double margin = 24;
                    double ratio = Math.Min((page_width - 2 * margin) / image.PixelWidth, (page_height - 2 * margin) / image.PixelHeight);
                    double width = image.PixelWidth * ratio, height = image.PixelHeight * ratio;
                    int page_id = 3 + i * 3, content_id = page_id + 1, image_id = page_id + 2;
                    Object(stream, offsets, page_id, "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + Number(page_width) + " " + Number(page_height)
                        + "] /Resources << /XObject << /Im0 " + image_id + " 0 R >> >> /Contents " + content_id + " 0 R >>");
                    string commands = "q\n" + Number(width) + " 0 0 " + Number(height) + " " + Number((page_width - width) / 2)
                        + " " + Number((page_height - height) / 2) + " cm\n/Im0 Do\nQ\n";
                    offsets[content_id] = stream.Position;
                    Text(stream, content_id + " 0 obj\n<< /Length " + Encoding.ASCII.GetByteCount(commands) + " >>\nstream\n" + commands + "endstream\nendobj\n");
                    offsets[image_id] = stream.Position;
                    long length = new FileInfo(image.JpegPath).Length;
                    if (length == 0) throw new IOException("비어 있는 이미지는 PDF에 넣을 수 없습니다.");
                    Text(stream, image_id + " 0 obj\n<< /Type /XObject /Subtype /Image /Width " + image.PixelWidth + " /Height " + image.PixelHeight
                        + " /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length " + length.ToString(CultureInfo.InvariantCulture) + " >>\nstream\n");
                    using (FileStream input = File.OpenRead(image.JpegPath))
                    {
                        int count;
                        while ((count = input.Read(buffer, 0, buffer.Length)) > 0)
                        { token.ThrowIfCancellationRequested(); stream.Write(buffer, 0, count); }
                    }
                    Text(stream, "\nendstream\nendobj\n");
                }
                token.ThrowIfCancellationRequested();
                long xref = stream.Position;
                Text(stream, "xref\n0 " + (objects + 1).ToString(CultureInfo.InvariantCulture) + "\n0000000000 65535 f \n");
                for (int i = 1; i <= objects; i++)
                {
                    if (offsets[i] > 9999999999L) throw new IOException("PDF 출력이 지원 크기를 초과했습니다.");
                    Text(stream, offsets[i].ToString("D10", CultureInfo.InvariantCulture) + " 00000 n \n");
                }
                Text(stream, "trailer\n<< /Size " + (objects + 1).ToString(CultureInfo.InvariantCulture) + " /Root 1 0 R >>\nstartxref\n"
                    + xref.ToString(CultureInfo.InvariantCulture) + "\n%%EOF\n");
            }
        }
        private static void Object(Stream stream, long[] offsets, int id, string body)
        { offsets[id] = stream.Position; Text(stream, id + " 0 obj\n" + body + "\nendobj\n"); }
    }
}
