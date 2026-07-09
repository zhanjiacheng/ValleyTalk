using System;
using System.Diagnostics;

namespace ValleyTalk;

/// <summary>
/// 对话生成流程耗时诊断工具。受 Config.DebugTiming 开关控制。
/// 用法：在关键节点调用 TimingLog.Checkpoint("描述")，最终调用 TimingLog.Stop()。
/// </summary>
public static class TimingLog
{
    private static Stopwatch _sw;
    private static long _lastMs;

    public static bool Enabled => ModEntry.Config.DebugTiming;

    /// <summary>
    /// 开始计时。重置所有状态。
    /// </summary>
    public static void Start(string label = "开始生成")
    {
        if (!Enabled) return;
        _sw = Stopwatch.StartNew();
        _lastMs = 0;
        LogTiming("═══════ 计时开始 ═══════");
        LogTiming($"[    0ms] {label}");
    }

    /// <summary>
    /// 记录一个检查点，输出从上一个检查点（或 Start）以来的耗时。
    /// </summary>
    public static void Checkpoint(string label)
    {
        if (!Enabled || _sw == null) return;
        long total = _sw.ElapsedMilliseconds;
        long delta = total - _lastMs;
        string deltaStr = delta > 0 ? $"+{delta}ms" : "+0ms";
        LogTiming($"[{total,5}ms] {deltaStr,8}  {label}");
        _lastMs = total;
    }

    /// <summary>
    /// 结束计时，输出总耗时。
    /// </summary>
    public static void Stop(string label = "完成")
    {
        if (!Enabled || _sw == null) return;
        _sw.Stop();
        long total = _sw.ElapsedMilliseconds;
        long delta = total - _lastMs;
        string deltaStr = delta > 0 ? $"+{delta}ms" : "+0ms";
        LogTiming($"[{total,5}ms] {deltaStr,8}  {label}");
        LogTiming("═══════ 计时结束 ═══════");
        _sw = null;
    }

    private static void LogTiming(string msg)
    {
        ModEntry.SMonitor?.Log($"[VT-Timing] {msg}", StardewModdingAPI.LogLevel.Debug);
    }
}
