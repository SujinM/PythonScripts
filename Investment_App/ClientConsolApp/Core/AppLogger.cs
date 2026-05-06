namespace ClientConsolApp.Core;

/// <summary>
/// Lightweight timestamped console logger with per-level colour coding.
/// Does NOT log sensitive data (tokens, keys, secrets).
/// </summary>
public static class AppLogger
{
    public static void Info(string message)    => Write($"  {message}", ConsoleColor.Gray);
    public static void Success(string message) => Write($"  ✓ {message}", ConsoleColor.Green);
    public static void Warn(string message)    => Write($"  ⚠ {message}", ConsoleColor.Yellow);
    public static void Error(string message)   => Write($"  ✗ {message}", ConsoleColor.Red);

    public static void Header(string title)
    {
        Console.WriteLine();
        Write($"  {title}", ConsoleColor.Cyan);
        Write($"  {new string('─', title.Length)}", ConsoleColor.DarkCyan);
    }

    public static void Blank() => Console.WriteLine();

    private static void Write(string text, ConsoleColor color)
    {
        var saved = Console.ForegroundColor;
        Console.ForegroundColor = color;
        Console.WriteLine(text);
        Console.ForegroundColor = saved;
    }
}
