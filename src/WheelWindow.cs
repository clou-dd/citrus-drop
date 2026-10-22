using System;
using System.Collections.Generic;
using System.Globalization;
using System.Windows;
using System.Windows.Media;

namespace CitrusDrop
{
    internal sealed class WheelWindow : Window
    {
        private readonly WheelSurface surface;
        private readonly Func<bool> has_ffmpeg;
        private readonly Func<string> pdf_directory;
        private string[] current_files = new string[0];
        public event Action<string[], Operation> Requested;

        public WheelWindow(Func<bool> available, Func<string> get_pdf_directory)
        {
            has_ffmpeg = available;
            pdf_directory = get_pdf_directory;
            Width = 380; Height = 380; AllowsTransparency = true;
            WindowStyle = WindowStyle.None; ResizeMode = ResizeMode.NoResize;
            Background = Brushes.Transparent; ShowInTaskbar = false; ShowActivated = false;
            Topmost = true; AllowDrop = true;
            surface = new WheelSurface(); Content = surface;
            DragEnter += UpdateDrag;
            DragOver += UpdateDrag;
            Drop += OnDrop;
        }
        public void Open()
        {
            current_files = new string[0];
            surface.Options = new List<Operation>(); surface.Hover = -1;
            surface.Hint = "파일을 이동해 주세요"; surface.Count = 0;
            surface.InvalidateVisual(); Native.PositionAtCursor(this); Show();
        }
        private void UpdateDrag(object sender, DragEventArgs e)
        {
            try
            {
                if (!e.Data.GetDataPresent(DataFormats.FileDrop) || (e.AllowedEffects & DragDropEffects.Copy) == 0)
                { surface.Hint = "파일만 지원합니다"; surface.Hover = -1; e.Effects = DragDropEffects.None; e.Handled = true; surface.InvalidateVisual(); return; }
                // File paths are read only after the OS supplies a real OLE FileDrop.
                if (current_files.Length == 0)
                {
                    current_files = Plans.Files(e.Data.GetData(DataFormats.FileDrop) as string[]);
                    string folder = pdf_directory();
                    surface.Options = Plans.ForFiles(current_files, has_ffmpeg(), System.IO.File.Exists(PdfTools.Tool(folder, "pdftoppm")), System.IO.File.Exists(PdfTools.Tool(folder, "pdftotext")));
                    surface.Count = current_files.Length;
                    surface.Hint = current_files.Length == 0 ? "폴더는 지원하지 않습니다" : "원하는 형식에 놓으세요";
                }
                surface.Hover = surface.Hit(e.GetPosition(surface));
                e.Effects = surface.Hover >= 0 ? DragDropEffects.Copy : DragDropEffects.None;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Trace.WriteLine(ex);
                surface.Hint = "이 파일은 읽을 수 없습니다"; surface.Hover = -1; e.Effects = DragDropEffects.None;
            }
            e.Handled = true; surface.InvalidateVisual();
        }
        private void OnDrop(object sender, DragEventArgs e)
        {
            // Update again: drop may arrive without a preceding DragOver at this exact point.
            UpdateDrag(sender, e);
            int selected = surface.Hover;
            string[] files = current_files;
            Operation op = selected >= 0 && selected < surface.Options.Count ? surface.Options[selected] : null;
            e.Effects = op == null ? DragDropEffects.None : DragDropEffects.Copy;
            e.Handled = true; Hide();
            if (op != null && Requested != null) Requested(files, op);
        }
    }

    internal sealed class WheelSurface : FrameworkElement
    {
        public List<Operation> Options = new List<Operation>();
        public string Hint = "파일을 이동해 주세요";
        public int Count;
        public int Hover = -1;
        private const double Center = 190, Inner = 72, Outer = 174;
        private static readonly Brush Orange = Brush("#FF9F45");
        private static Brush Brush(string color) { return new SolidColorBrush((Color)ColorConverter.ConvertFromString(color)); }

        public int Hit(Point point)
        {
            if (Options.Count == 0) return -1;
            double x = point.X - Center, y = point.Y - Center;
            double radius = Math.Sqrt(x * x + y * y);
            if (radius < Inner || radius > Outer) return -1;
            double step = Math.PI * 2 / Options.Count;
            double angle = Math.Atan2(y, x) + Math.PI / 2 + step / 2;
            angle = (angle + Math.PI * 2) % (Math.PI * 2);
            int selected = (int)(angle / step);
            // Match the visible gaps, so dropping into a gap never selects a neighbor.
            double within = angle - selected * step;
            return within < 0.018 || within > step - 0.018 ? -1 : selected;
        }
        protected override void OnRender(DrawingContext dc)
        {
            base.OnRender(dc);
            // A nonzero transparent background keeps OLE hit testing inside the window.
            dc.DrawRectangle(new SolidColorBrush(Color.FromArgb(1, 0, 0, 0)), null, new Rect(0, 0, 380, 380));
            dc.DrawEllipse(Brush("#161B25"), new Pen(Brush("#343C4A"), 1), new Point(Center, Center), Outer + 4, Outer + 4);
            if (Options.Count > 0)
            {
                double step = Math.PI * 2 / Options.Count;
                for (int i = 0; i < Options.Count; i++)
                {
                    double angle = -Math.PI / 2 + i * step;
                    double from = angle - step / 2 + 0.018, to = angle + step / 2 - 0.018;
                    bool active = i == Hover;
                    dc.DrawGeometry(active ? Orange : Brush("#232B39"), null, Sector(from, to));
                    Point position = Polar(121, angle);
                    Text(dc, Options[i].Label, position.X, position.Y - 9, 15, active ? Brush("#171D26") : Brushes.White, true);
                    Text(dc, active ? "놓아서 실행" : "변환 / 작업", position.X, position.Y + 14, 9, active ? Brush("#57402A") : Brush("#9BA6B8"), false);
                }
            }
            dc.DrawEllipse(Brush("#161B25"), new Pen(Brush("#343C4A"), 1), new Point(Center, Center), Inner - 3, Inner - 3);
            Text(dc, Count > 0 ? Count + "개 파일" : "CITRUS", Center, Center - 17, 14, Orange, true);
            Text(dc, Hover >= 0 ? Options[Hover].Label : "SHIFT + DROP", Center, Center + 9, 11, Brushes.White, false);
            Text(dc, Hint, Center, 370, 11, Brush("#CCD3DE"), false);
        }
        private static Point Polar(double radius, double angle)
        { return new Point(Center + radius * Math.Cos(angle), Center + radius * Math.Sin(angle)); }
        private static Geometry Sector(double from, double to)
        {
            StreamGeometry geometry = new StreamGeometry();
            using (StreamGeometryContext context = geometry.Open())
            {
                context.BeginFigure(Polar(Inner, from), true, true);
                context.LineTo(Polar(Outer, from), true, false);
                context.ArcTo(Polar(Outer, to), new Size(Outer, Outer), 0, to - from > Math.PI, SweepDirection.Clockwise, true, false);
                context.LineTo(Polar(Inner, to), true, false);
                context.ArcTo(Polar(Inner, from), new Size(Inner, Inner), 0, to - from > Math.PI, SweepDirection.Counterclockwise, true, false);
            }
            geometry.Freeze(); return geometry;
        }
        private void Text(DrawingContext dc, string text, double x, double y, double size, Brush color, bool bold)
        {
            Typeface face = new Typeface(new FontFamily("Malgun Gothic"), FontStyles.Normal, bold ? FontWeights.Bold : FontWeights.Normal, FontStretches.Normal);
            FormattedText formatted = new FormattedText(text, CultureInfo.CurrentUICulture, FlowDirection.LeftToRight, face, size, color, VisualTreeHelper.GetDpi(this).PixelsPerDip);
            dc.DrawText(formatted, new Point(x - formatted.Width / 2, y - formatted.Height / 2));
        }
    }
}
