using System;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Threading;
using Forms = System.Windows.Forms;

namespace CitrusDrop
{
    internal static class Native
    {
        [StructLayout(LayoutKind.Sequential)] internal struct Point { public int X; public int Y; }
        [DllImport("user32.dll")] internal static extern short GetAsyncKeyState(int key);
        [DllImport("user32.dll")] internal static extern bool GetCursorPos(out Point point);
        [DllImport("user32.dll")] internal static extern int GetSystemMetrics(int index);
        public static bool Down(int key) { return GetAsyncKeyState(key) < 0; }
        public static bool PrimaryDown() { return Down(GetSystemMetrics(23) != 0 ? 0x02 : 0x01); }

        public static void PositionAtCursor(Window window)
        {
            Point cursor;
            if (!GetCursorPos(out cursor)) return;
            IntPtr handle = new WindowInteropHelper(window).EnsureHandle();
            HwndSource source = HwndSource.FromHwnd(handle);
            System.Windows.Media.Matrix transform = source.CompositionTarget.TransformFromDevice;
            System.Windows.Point pos = transform.Transform(new System.Windows.Point(cursor.X, cursor.Y));
            System.Drawing.Rectangle rect = Forms.Screen.FromPoint(new System.Drawing.Point(cursor.X, cursor.Y)).WorkingArea;
            System.Windows.Point min = transform.Transform(new System.Windows.Point(rect.Left, rect.Top));
            System.Windows.Point max = transform.Transform(new System.Windows.Point(rect.Right, rect.Bottom));
            window.Left = Math.Max(min.X, Math.Min(pos.X - window.Width / 2, max.X - window.Width));
            window.Top = Math.Max(min.Y, Math.Min(pos.Y - window.Height / 2, max.Y - window.Height));
        }
    }

    // Observes key/button state only. No key logging, injected input, shell extension,
    // or assumption that a mouse gesture contains files: FileDrop is checked by the wheel.
    internal sealed class GestureMonitor : IDisposable
    {
        private readonly DispatcherTimer timer;
        private readonly WheelWindow wheel;
        private bool previous_primary;
        private bool previous_shift;
        private Native.Point start;
        private DateTime released_at = DateTime.MinValue;
        public bool Enabled = true;

        public GestureMonitor(WheelWindow window)
        {
            wheel = window;
            timer = new DispatcherTimer(DispatcherPriority.Input) { Interval = TimeSpan.FromMilliseconds(25) };
            timer.Tick += Tick; timer.Start();
        }
        private void Tick(object sender, EventArgs e)
        {
            bool primary = Native.PrimaryDown();
            bool shift = Native.Down(0x10);
            Native.Point cursor;
            bool has_cursor = Native.GetCursorPos(out cursor);
            if (primary && !previous_primary && has_cursor) start = cursor;
            double dx = cursor.X - start.X, dy = cursor.Y - start.Y;
            bool moved = dx * dx + dy * dy >= 64;
            if (Enabled && primary && previous_primary && shift && !previous_shift && moved && has_cursor && !wheel.IsVisible)
                wheel.Open();
            if (wheel.IsVisible && Native.Down(0x1B)) wheel.Hide();
            if (wheel.IsVisible && !primary)
            {
                if (released_at == DateTime.MinValue) released_at = DateTime.UtcNow;
                // OLE Drop must finish before hiding the target window.
                if ((DateTime.UtcNow - released_at).TotalMilliseconds > 300) wheel.Hide();
            }
            else released_at = DateTime.MinValue;
            if (!Enabled && wheel.IsVisible) wheel.Hide();
            previous_primary = primary; previous_shift = shift;
        }
        public void Dispose() { timer.Stop(); timer.Tick -= Tick; }
    }
}
