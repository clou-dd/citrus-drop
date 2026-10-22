using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Forms = System.Windows.Forms;

namespace CitrusDrop
{
    internal sealed class MainWindow : Window
    {
        private readonly List<string> files = new List<string>();
        private readonly ListBox file_list = new ListBox();
        private readonly ListBox history = new ListBox();
        private readonly ComboBox formats = new ComboBox();
        private readonly Button run = new Button();
        private readonly Button cancel = new Button();
        private readonly TextBlock status = new TextBlock();
        private readonly TextBlock file_count = new TextBlock();
        private readonly TextBlock ffmpeg_status = new TextBlock();
        private readonly TextBlock pdf_status = new TextBlock();
        private readonly ProgressBar progress = new ProgressBar();
        private readonly Func<string> ffmpeg_path;
        private readonly Action<string> set_ffmpeg;
        private readonly Func<string> pdf_directory;
        private readonly Action<string> set_pdf_engine;
        public event Action<string[], Operation> Requested;
        public event Action CancelRequested;
        public event Action<bool> GestureToggled;

        private static Brush ColorBrush(string color)
        { return new SolidColorBrush((Color)ColorConverter.ConvertFromString(color)); }
        private static readonly Brush White = ColorBrush("#F2F4F8");
        private static readonly Brush Muted = ColorBrush("#A9B3C4");
        private static readonly Brush Orange = ColorBrush("#FFAA5C");

        public MainWindow(Func<string> get_ffmpeg, Action<string> save_ffmpeg, Func<string> get_pdf_directory, Action<string> save_pdf_engine)
        {
            ffmpeg_path = get_ffmpeg; set_ffmpeg = save_ffmpeg;
            pdf_directory = get_pdf_directory; set_pdf_engine = save_pdf_engine;
            Title = "Citrus Drop 0.2 · 로컬 파일 변환"; Width = 780; Height = 900;
            MinWidth = 650; MinHeight = 680; WindowStartupLocation = WindowStartupLocation.CenterScreen;
            Background = ColorBrush("#10151E"); Foreground = White;
            FontFamily = new FontFamily("Malgun Gothic"); FontSize = 13;
            Closing += delegate(object sender, System.ComponentModel.CancelEventArgs e) { e.Cancel = true; Hide(); };
            Resources.Add(typeof(Button), ButtonStyle());

            ScrollViewer scroll = new ScrollViewer { VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
            StackPanel root = new StackPanel { Margin = new Thickness(28) }; scroll.Content = root; Content = scroll;
            root.Children.Add(Text("CITRUS DROP", 12, Orange, FontWeights.Bold));
            TextBlock heading = Text("파일을 놓으면, 변환됩니다.", 28, White, FontWeights.Bold);
            heading.Margin = new Thickness(0, 8, 0, 9); root.Children.Add(heading);
            root.Children.Add(Text("탐색기에서 파일을 끌다가 Shift를 누르고, 원형 메뉴의 형식 위에 놓으세요.", 13, Muted, FontWeights.Normal));
            CheckBox gesture = new CheckBox { Content = "Shift 원형 메뉴 사용", IsChecked = true, Foreground = White, Margin = new Thickness(0, 16, 0, 18) };
            gesture.Checked += delegate { if (GestureToggled != null) GestureToggled(true); };
            gesture.Unchecked += delegate { if (GestureToggled != null) GestureToggled(false); };
            root.Children.Add(gesture);

            StackPanel drop_content = new StackPanel();
            drop_content.Children.Add(Text("여기로 파일을 끌어 놓으셔도 됩니다", 17, White, FontWeights.Bold));
            TextBlock drop_hint = Text("이미지 · PDF · 영상 · 음성 · 여러 파일 ZIP 압축", 12, Muted, FontWeights.Normal);
            drop_hint.Margin = new Thickness(0, 8, 0, 0); drop_content.Children.Add(drop_hint);
            Border drop_area = new Border { Child = drop_content, Padding = new Thickness(22), CornerRadius = new CornerRadius(14), Background = ColorBrush("#1B2432"), BorderBrush = ColorBrush("#46536A"), BorderThickness = new Thickness(1), AllowDrop = true };
            drop_area.DragOver += delegate(object sender, DragEventArgs e)
            { e.Effects = e.Data.GetDataPresent(DataFormats.FileDrop) && (e.AllowedEffects & DragDropEffects.Copy) != 0 ? DragDropEffects.Copy : DragDropEffects.None; e.Handled = true; };
            drop_area.Drop += delegate(object sender, DragEventArgs e)
            {
                e.Effects = DragDropEffects.None;
                if (e.Data.GetDataPresent(DataFormats.FileDrop) && (e.AllowedEffects & DragDropEffects.Copy) != 0)
                { AddFiles(e.Data.GetData(DataFormats.FileDrop) as string[]); e.Effects = DragDropEffects.Copy; }
                e.Handled = true;
            };
            root.Children.Add(drop_area);

            DockPanel file_toolbar = new DockPanel { Margin = new Thickness(0, 17, 0, 9) };
            Button add = Button("파일 추가"); add.Click += PickFiles; DockPanel.SetDock(add, Dock.Right);
            Button clear = Button("목록 비우기"); clear.Margin = new Thickness(8, 0, 0, 0); clear.Click += delegate { files.Clear(); RefreshFiles(); }; DockPanel.SetDock(clear, Dock.Right);
            Button up = Button("위로"); up.Margin = new Thickness(8, 0, 0, 0); up.Click += delegate { MoveSelected(-1); }; DockPanel.SetDock(up, Dock.Right);
            Button down = Button("아래로"); down.Margin = new Thickness(8, 0, 0, 0); down.Click += delegate { MoveSelected(1); }; DockPanel.SetDock(down, Dock.Right);
            file_toolbar.Children.Add(clear); file_toolbar.Children.Add(down); file_toolbar.Children.Add(up); file_toolbar.Children.Add(add);
            file_count.Foreground = Muted; file_count.VerticalAlignment = VerticalAlignment.Center; file_toolbar.Children.Add(file_count);
            root.Children.Add(file_toolbar);
            file_list.Height = 100; file_list.Background = ColorBrush("#151C28"); file_list.Foreground = White;
            file_list.BorderBrush = ColorBrush("#2D3747"); file_list.Padding = new Thickness(7); root.Children.Add(file_list);
            root.Children.Add(Spacer(16));

            root.Children.Add(Text("출력 형식 / 작업", 12, Muted, FontWeights.Normal));
            formats.Margin = new Thickness(0, 7, 0, 9); formats.Height = 34; formats.FontSize = 14;
            formats.Foreground = Brushes.Black; formats.Background = Brushes.White; root.Children.Add(formats);
            root.Children.Add(Text("결과는 원본 폴더에 새 파일로 저장됩니다. 같은 이름이 있으면 번호를 붙입니다.", 12, Muted, FontWeights.Normal));
            TextBlock pdf_note = Text("PDF 만들기: 목록 순서대로 A4 페이지에 배치합니다. PDF → 이미지는 페이지별 결과 폴더를 만듭니다.", 11, Muted, FontWeights.Normal);
            pdf_note.Margin = new Thickness(0, 5, 0, 0); root.Children.Add(pdf_note);
            TextBlock note = Text("GIF·여러 페이지 TIFF는 첫 프레임만 변환합니다. JPG·BMP의 투명 영역은 흰색으로 채웁니다.", 11, Muted, FontWeights.Normal);
            note.Margin = new Thickness(0, 5, 0, 0); root.Children.Add(note);

            Grid actions = new Grid { Margin = new Thickness(0, 18, 0, 12) };
            actions.ColumnDefinitions.Add(new ColumnDefinition()); actions.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            run.Content = "변환 실행"; run.Height = 42; run.Background = Orange; run.Foreground = ColorBrush("#171D26"); run.FontWeight = FontWeights.Bold;
            run.Click += delegate { Operation op = formats.SelectedItem as Operation; if (op != null && Requested != null) Requested(files.ToArray(), op); };
            cancel.Content = "취소"; cancel.Margin = new Thickness(10, 0, 0, 0); cancel.MinWidth = 75; cancel.IsEnabled = false;
            cancel.Click += delegate { if (CancelRequested != null) CancelRequested(); };
            Grid.SetColumn(cancel, 1); actions.Children.Add(run); actions.Children.Add(cancel); root.Children.Add(actions);
            progress.Height = 5; progress.Foreground = Orange; progress.Background = ColorBrush("#263145"); progress.BorderThickness = new Thickness(0); root.Children.Add(progress);
            status.Foreground = Muted; status.TextWrapping = TextWrapping.Wrap; status.Margin = new Thickness(0, 9, 0, 16); root.Children.Add(status);

            DockPanel settings = new DockPanel();
            Button choose = Button("FFmpeg 선택"); choose.Click += PickFfmpeg; DockPanel.SetDock(choose, Dock.Right); settings.Children.Add(choose);
            ffmpeg_status.Foreground = Muted; ffmpeg_status.TextWrapping = TextWrapping.Wrap; ffmpeg_status.VerticalAlignment = VerticalAlignment.Center; ffmpeg_status.Margin = new Thickness(0, 0, 12, 0); settings.Children.Add(ffmpeg_status); root.Children.Add(settings);
            DockPanel pdf_settings = new DockPanel { Margin = new Thickness(0, 12, 0, 0) };
            Button choose_pdf = Button("PDF 엔진 선택"); choose_pdf.Click += PickPdfEngine; DockPanel.SetDock(choose_pdf, Dock.Right); pdf_settings.Children.Add(choose_pdf);
            pdf_status.Foreground = Muted; pdf_status.TextWrapping = TextWrapping.Wrap; pdf_status.VerticalAlignment = VerticalAlignment.Center;
            pdf_status.Margin = new Thickness(0, 0, 12, 0); pdf_settings.Children.Add(pdf_status); root.Children.Add(pdf_settings);
            root.Children.Add(Spacer(16)); root.Children.Add(Text("작업 기록 · 이번 실행", 12, Muted, FontWeights.Normal));
            history.Height = 135; history.Margin = new Thickness(0, 8, 0, 0); history.Background = ColorBrush("#151C28"); history.Foreground = White; history.BorderBrush = ColorBrush("#2D3747"); history.Padding = new Thickness(7); root.Children.Add(history);
            TextBlock footer = Text("창을 닫아도 트레이에 남습니다. 완전히 종료하려면 트레이 아이콘 → 종료를 선택하세요.", 11, Muted, FontWeights.Normal);
            footer.Margin = new Thickness(0, 14, 0, 0); root.Children.Add(footer);
            RefreshFiles(); RefreshFfmpeg(); RefreshPdf(); SetStatus("준비되었습니다. 파일은 서버로 업로드되지 않습니다.");
        }

        private static Style ButtonStyle()
        {
            Style style = new Style(typeof(Button));
            style.Setters.Add(new Setter(Control.PaddingProperty, new Thickness(12, 7, 12, 7)));
            style.Setters.Add(new Setter(Control.BackgroundProperty, ColorBrush("#2A3547")));
            style.Setters.Add(new Setter(Control.ForegroundProperty, White));
            style.Setters.Add(new Setter(Control.BorderThicknessProperty, new Thickness(0)));
            return style;
        }
        private static Button Button(string text) { return new Button { Content = text }; }
        private static FrameworkElement Spacer(double height) { return new Border { Height = height }; }
        private static TextBlock Text(string text, double size, Brush color, FontWeight weight)
        { return new TextBlock { Text = text, FontSize = size, Foreground = color, FontWeight = weight, TextWrapping = TextWrapping.Wrap }; }

        private void PickFiles(object sender, RoutedEventArgs e)
        {
            Microsoft.Win32.OpenFileDialog picker = new Microsoft.Win32.OpenFileDialog { Multiselect = true, CheckFileExists = true, Title = "변환할 파일 선택", Filter = "모든 파일|*.*" };
            if (picker.ShowDialog(this) == true) AddFiles(picker.FileNames);
        }
        private void AddFiles(string[] incoming)
        {
            try
            {
                foreach (string path in Plans.Files(incoming))
                    if (!files.Contains(path, StringComparer.OrdinalIgnoreCase)) files.Add(path);
                RefreshFiles();
            }
            catch (Exception ex) { SetStatus("파일 목록을 읽지 못했습니다: " + ex.Message); }
        }
        private void RefreshFiles()
        {
            file_list.Items.Clear();
            foreach (string file in files)
                file_list.Items.Add(new ListBoxItem { Content = Path.GetFileName(file), ToolTip = file, Foreground = White });
            file_count.Text = files.Count + "개 파일 선택";
            string previous = formats.SelectedItem is Operation ? ((Operation)formats.SelectedItem).Id : "";
            string folder = pdf_directory();
            List<Operation> options = Plans.ForFiles(files.ToArray(), File.Exists(ffmpeg_path()), File.Exists(PdfTools.Tool(folder, "pdftoppm")), File.Exists(PdfTools.Tool(folder, "pdftotext")));
            formats.ItemsSource = options;
            formats.SelectedItem = options.FirstOrDefault(o => o.Id == previous) ?? options.FirstOrDefault();
            run.IsEnabled = files.Count > 0 && !cancel.IsEnabled;
        }
        private void MoveSelected(int direction)
        {
            int index = file_list.SelectedIndex, destination = index + direction;
            if (index < 0 || destination < 0 || destination >= files.Count) return;
            string item = files[index]; files.RemoveAt(index); files.Insert(destination, item);
            RefreshFiles(); file_list.SelectedIndex = destination; file_list.ScrollIntoView(file_list.SelectedItem);
        }
        private void PickPdfEngine(object sender, RoutedEventArgs e)
        {
            Microsoft.Win32.OpenFileDialog picker = new Microsoft.Win32.OpenFileDialog
            { CheckFileExists = true, Filter = "Poppler PDF 엔진|pdftoppm.exe", Title = "Poppler의 pdftoppm.exe 선택 (주변 DLL·data 폴더를 그대로 유지해 주세요)" };
            if (picker.ShowDialog(this) != true) return;
            try { set_pdf_engine(picker.FileName); RefreshPdf(); RefreshFiles(); }
            catch (Exception ex) { SetStatus("PDF 엔진 설정을 저장하지 못했습니다: " + ex.Message); }
        }
        private void RefreshPdf()
        {
            string folder = pdf_directory();
            bool renderer = File.Exists(PdfTools.Tool(folder, "pdftoppm")), text = File.Exists(PdfTools.Tool(folder, "pdftotext"));
            pdf_status.Text = renderer ? "PDF 엔진 연결됨 · PNG / JPG" + (text ? " / TXT 추출 (OCR 제외)" : " · TXT 도구 없음")
                : "이미지 → PDF 기본 지원 · PDF → PNG / JPG / TXT는 Poppler 연결 필요";
            pdf_status.ToolTip = folder;
        }
        private void PickFfmpeg(object sender, RoutedEventArgs e)
        {
            Microsoft.Win32.OpenFileDialog picker = new Microsoft.Win32.OpenFileDialog { CheckFileExists = true, Filter = "FFmpeg 실행 파일|ffmpeg.exe", Title = "사용할 ffmpeg.exe 선택" };
            if (picker.ShowDialog(this) == true)
            {
                try { set_ffmpeg(picker.FileName); RefreshFfmpeg(); RefreshFiles(); }
                catch (Exception ex) { SetStatus("설정을 저장하지 못했습니다: " + ex.Message); }
            }
        }
        private void RefreshFfmpeg()
        {
            string path = ffmpeg_path();
            ffmpeg_status.Text = File.Exists(path) ? "FFmpeg 연결됨 · WebP / 영상 / 음성 메뉴 사용 가능" : "FFmpeg 미연결 · 기본 이미지 변환 / ZIP 사용 가능";
            ffmpeg_status.ToolTip = path;
        }
        public void SetBusy(bool busy)
        { cancel.IsEnabled = busy; run.IsEnabled = !busy && files.Count > 0; progress.IsIndeterminate = busy; }
        public void SetStatus(string message) { status.Text = message; }
        public void AddHistory(string message, bool failed)
        {
            ListBoxItem item = new ListBoxItem { Content = DateTime.Now.ToString("HH:mm:ss") + "  " + message, ToolTip = message, Foreground = failed ? ColorBrush("#FF9B95") : White };
            history.Items.Insert(0, item);
            if (history.Items.Count > 100) history.Items.RemoveAt(100);
        }
        public void Reveal() { Show(); WindowState = WindowState.Normal; Activate(); }
    }
}
