using System;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using Forms = System.Windows.Forms;

namespace CitrusDrop
{
    internal sealed class Settings
    {
        private readonly string file = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CitrusDrop", "ffmpeg-path.txt");
        private string configured = "";
        private readonly string pdf_file = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "CitrusDrop", "poppler-directory.txt");
        private string pdf_configured = "";
        public Settings()
        {
            try { if (File.Exists(file)) configured = File.ReadAllText(file).Trim(); } catch (IOException) { } catch (UnauthorizedAccessException) { }
            try { if (File.Exists(pdf_file)) pdf_configured = File.ReadAllText(pdf_file).Trim(); } catch (IOException) { } catch (UnauthorizedAccessException) { }
        }
        public string Ffmpeg()
        {
            if (!String.IsNullOrEmpty(configured) && File.Exists(configured)) return configured;
            string bundled = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "tools", "ffmpeg.exe");
            return File.Exists(bundled) ? bundled : "";
        }
        public void SaveFfmpeg(string path)
        {
            if (!File.Exists(path)) throw new FileNotFoundException("실행 파일을 찾을 수 없습니다.", path);
            Directory.CreateDirectory(Path.GetDirectoryName(file));
            File.WriteAllText(file, Path.GetFullPath(path)); configured = Path.GetFullPath(path);
        }
        public string PdfDirectory()
        {
            if (File.Exists(PdfTools.Tool(pdf_configured, "pdftoppm"))) return pdf_configured;
            string basis = AppDomain.CurrentDomain.BaseDirectory;
            foreach (string candidate in new[] { Path.Combine(basis, "tools", "poppler", "Library", "bin"), Path.Combine(basis, "tools", "poppler", "bin"), Path.Combine(basis, "tools", "poppler") })
                if (File.Exists(PdfTools.Tool(candidate, "pdftoppm"))) return candidate;
            return "";
        }
        public void SavePdfEngine(string executable)
        {
            string folder = Path.GetDirectoryName(Path.GetFullPath(executable));
            if (!File.Exists(PdfTools.Tool(folder, "pdftoppm"))) throw new FileNotFoundException("pdftoppm.exe가 있는 폴더를 선택해 주세요.");
            Directory.CreateDirectory(Path.GetDirectoryName(pdf_file));
            File.WriteAllText(pdf_file, folder); pdf_configured = folder;
        }
    }

    internal sealed class Controller : IDisposable
    {
        private readonly Application app;
        private readonly Settings settings;
        private readonly MainWindow main;
        private readonly WheelWindow wheel;
        private readonly GestureMonitor gesture;
        private readonly Forms.NotifyIcon tray;
        private CancellationTokenSource cancellation;
        private bool busy;
        private bool exit_after_job;

        public Controller(Application application)
        {
            app = application; settings = new Settings();
            main = new MainWindow(settings.Ffmpeg, settings.SaveFfmpeg, settings.PdfDirectory, settings.SavePdfEngine);
            app.MainWindow = main;
            wheel = new WheelWindow(delegate { return File.Exists(settings.Ffmpeg()); }, settings.PdfDirectory);
            gesture = new GestureMonitor(wheel);
            main.GestureToggled += delegate(bool enabled) { gesture.Enabled = enabled; };
            main.CancelRequested += delegate { if (cancellation != null) cancellation.Cancel(); };
            main.Requested += Execute; wheel.Requested += Execute;
            Forms.ContextMenuStrip menu = new Forms.ContextMenuStrip();
            menu.Items.Add("Citrus Drop 열기", null, delegate { main.Reveal(); });
            menu.Items.Add("종료", null, delegate { Exit(); });
            tray = new Forms.NotifyIcon { Text = "Citrus Drop · Shift + 드래그", Icon = System.Drawing.SystemIcons.Application, ContextMenuStrip = menu, Visible = true };
            tray.DoubleClick += delegate { main.Reveal(); };
            main.Show();
        }

        private async void Execute(string[] requested_files, Operation op)
        {
            if (busy) { main.Reveal(); main.SetStatus("다른 작업이 진행 중입니다. 완료하거나 취소한 뒤 다시 실행해 주세요."); return; }
            string[] files;
            try
            {
                files = Plans.Files(requested_files);
                if (files.Length == 0) throw new IOException("읽을 수 있는 파일이 없습니다.");
                string pdf_directory = settings.PdfDirectory();
                if (!Plans.ForFiles(files, File.Exists(settings.Ffmpeg()), File.Exists(PdfTools.Tool(pdf_directory, "pdftoppm")), File.Exists(PdfTools.Tool(pdf_directory, "pdftotext"))).Any(o => o.Id == op.Id))
                    throw new InvalidOperationException("이 파일 조합에서는 선택한 작업을 지원하지 않습니다.");
                if (op.Id == "path")
                {
                    Clipboard.SetText(String.Join(Environment.NewLine, files));
                    main.AddHistory(files.Length + "개 파일 경로 복사 완료", false);
                    main.SetStatus("클립보드에 파일 경로를 복사했습니다.");
                    Notify("경로 복사 완료", files.Length + "개 파일의 경로를 복사했습니다."); return;
                }
            }
            catch (Exception ex) { main.AddHistory(ex.Message, true); main.Reveal(); main.SetStatus(ex.Message); return; }

            busy = true; cancellation = new CancellationTokenSource();
            main.SetBusy(true); main.SetStatus(op.Label + " 작업을 시작합니다. 원본 파일은 유지됩니다.");
            int succeeded = 0, failed = 0;
            bool was_cancelled = false;
            CancellationToken token = cancellation.Token;
            string ffmpeg = settings.Ffmpeg();
            string poppler = settings.PdfDirectory();
            try
            {
                await OnStaThread(delegate
                {
                    if (op.Id == "zip")
                    {
                        string output = Converter.Archive(files, token); succeeded = 1;
                        PostHistory(output, false); return;
                    }
                    if (op.Id == "pdf")
                    {
                        string output = PdfTools.FromImages(files, ffmpeg, token, delegate(int index, int total)
                        { app.Dispatcher.BeginInvoke(new Action(delegate { main.SetStatus("PDF 페이지 준비 " + index + " / " + total); })); });
                        succeeded = 1; PostHistory(output, false); return;
                    }
                    for (int i = 0; i < files.Length; i++)
                    {
                        token.ThrowIfCancellationRequested();
                        string input = files[i]; int index = i + 1;
                        app.Dispatcher.BeginInvoke(new Action(delegate { main.SetStatus(index + " / " + files.Length + "  " + Path.GetFileName(input)); }));
                        try
                        {
                            string output = op.Id.StartsWith("pdf_", StringComparison.Ordinal)
                                ? PdfTools.ConvertPdf(input, op.Id, poppler, token)
                                : Converter.ConvertOne(input, op.Id, ffmpeg, token);
                            succeeded++; PostHistory(output, false);
                        }
                        catch (OperationCanceledException) { throw; }
                        catch (Exception ex) { failed++; PostHistory(Path.GetFileName(input) + " · " + ex.Message, true); }
                    }
                });
            }
            catch (OperationCanceledException) { was_cancelled = true; }
            catch (Exception ex) { failed++; main.AddHistory(ex.Message, true); }
            finally
            {
                busy = false; main.SetBusy(false); cancellation.Dispose(); cancellation = null;
            }
            string result = (was_cancelled ? "취소됨 · " : "완료 · ") + succeeded + "건 성공 / " + failed + "건 실패";
            main.SetStatus(result + (was_cancelled ? " · 이미 완료된 결과는 유지됩니다." : ""));
            Notify("Citrus Drop", result);
            if (failed > 0) main.Reveal();
            if (exit_after_job) app.Shutdown();
        }

        private void PostHistory(string message, bool failed)
        { app.Dispatcher.BeginInvoke(new Action(delegate { main.AddHistory(message, failed); })); }

        private static Task OnStaThread(Action action)
        {
            TaskCompletionSource<bool> completion = new TaskCompletionSource<bool>();
            Thread worker = new Thread(delegate()
            {
                try { action(); completion.SetResult(true); }
                catch (OperationCanceledException) { completion.SetCanceled(); }
                catch (Exception ex) { completion.SetException(ex); }
            });
            worker.IsBackground = true; worker.SetApartmentState(ApartmentState.STA); worker.Start();
            return completion.Task;
        }
        private void Notify(string title, string message)
        {
            try { tray.ShowBalloonTip(3000, title, message, Forms.ToolTipIcon.Info); }
            catch (InvalidOperationException) { }
        }
        private void Exit()
        {
            if (busy)
            {
                if (MessageBox.Show("진행 중인 작업을 취소하고 종료하시겠습니까?", "Citrus Drop", MessageBoxButton.YesNo, MessageBoxImage.Question) != MessageBoxResult.Yes) return;
                exit_after_job = true; gesture.Enabled = false; if (cancellation != null) cancellation.Cancel();
                main.SetStatus("현재 작업을 취소하고 종료하는 중입니다."); return;
            }
            app.Shutdown();
        }
        public void Dispose()
        { gesture.Dispose(); tray.Visible = false; tray.ContextMenuStrip.Dispose(); tray.Dispose(); }
    }

    internal static class Program
    {
        [STAThread]
        public static void Main()
        {
            bool created;
            using (Mutex mutex = new Mutex(true, "Local\\CitrusDrop_04104769", out created))
            {
                if (!created) { MessageBox.Show("Citrus Drop이 이미 실행 중입니다. 트레이 아이콘을 확인해 주세요."); return; }
                try
                {
                    Application app = new Application { ShutdownMode = ShutdownMode.OnExplicitShutdown };
                    using (Controller controller = new Controller(app)) app.Run();
                }
                catch (Exception ex) { MessageBox.Show("Citrus Drop을 실행하지 못했습니다.\n\n" + ex, "Citrus Drop"); }
                finally { mutex.ReleaseMutex(); }
            }
        }
    }
}
