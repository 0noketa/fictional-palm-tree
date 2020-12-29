// 分割のみ
using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;


public class SplitPager
{
    TextReader input;
    TextWriter output;

    public bool HasNext { get; set; } = true;

    int offset = 0;
    public int Offset
    {
        get => offset;
        set
        {
            if (value > 0)
                offset = value;
        }
    }

    int displayWidth = 120;
    public int DisplayWidth
    { 
        get => displayWidth;
        set
        {
            if (UpdatePageWidth(value, Columns, Separator.Length))
                displayWidth = value;
        }
    }

    public int PageWidth { get; private set; } = 59;
    public int PageHeight { get; set; } = 29;

    int columns = 2;
    public int Columns
    {
        get => columns;
        set
        {
            if (UpdatePageWidth(DisplayWidth, value, Separator.Length))
                columns = value;
        }
    }

    int tabWidth = 4;
    public int TabWidth
    {
        get => tabWidth;
        set
        {
            if (value > 0 && value < PageWidth)
                tabWidth = value;
        }
    }

    string separator = "|";
    public string Separator
    {
        get => separator;
        set
        {
            if (UpdatePageWidth(DisplayWidth, Columns, value.Length))
                separator = value;
        }
    }

    bool UpdatePageWidth(int dispW, int cols, int sepW)
    {
        if (dispW < 1 || cols < 1 || sepW < 0) return false;
        if (dispW < cols * (sepW + 1)) return false;

        PageWidth = dispW / cols - sepW;

        return true;
    }

    public SplitPager(TextReader input = null, TextWriter output = null)
    {
        if (input == null) input = Console.In;
        if (output == null) output = Console.Out;

        this.input = input;
        this.output = output;
    }

    static int SrcHeightToDstHeight(int h, int cols)
    {
        return h / cols + (h % cols > 0 ? 1 : 0);
    }

    string ReplaceTabs(string src)
    {
        string f(string s) =>
            Substring(s, Offset, MaxCharsIntoCharColumns(s, Offset, PageWidth));

        return f(src.Replace("\r", "")
            .Replace("\t", new String(' ', TabWidth)));        
    }

    public string[] LoadPage()
    {
        string[] src;

        if (PageHeight < 0)
        {
            HasNext = false;
            src = input.ReadToEnd()
                .Split('\n')
                .Select(s => ReplaceTabs(s))
                .ToArray();
            PageHeight = SrcHeightToDstHeight(src.Length, Columns);
        }
        else
            src = new string[PageHeight * Columns]
                .Select(_ =>
                {
                    var s = input.ReadLine();

                    if (s == null)
                    {
                        HasNext = false;

                        return "";
                    }
                    else
                        return ReplaceTabs(s);
                })
                .ToArray();

        return src;
    }

    static int RequiredCharColumns(string s)
    {
        int r = 0;

        foreach (char c in s.ToArray())
            if (c >= 256) r += 2;
            else ++r;

        return r;
    }

    static int MaxCharsIntoCharColumns(string s, int offset, int w)
    {
        int i;
        int r = 0;
        int len2 = s.Length > offset ? s.Length - offset : 0;

        for (i = 0; i < len2; ++i)
        {
            if (s[offset + i] >= 256) r += 2;
            else ++r;

            if (r > w)
                return i;
        }

        return i;
    }

    // 範囲外は空白に
    string Substring(string s, int startIndex = -1, int length = -1)
    {
        if (startIndex == -1) startIndex = Offset;
        if (length == -1 || length > s.Length) length = s.Length;

        if (startIndex >= s.Length)
            return "";

        if (startIndex + length > s.Length)
            length = s.Length - startIndex;

        return s.Substring(startIndex, length);
    }

    void DumpPage(string[] src) 
    {
        string fill(string s) => 
            s.Length >= PageWidth
            ? s 
            : s + new String(' ', PageWidth - RequiredCharColumns(s));

        for (int row = 0; row < PageHeight; ++row)
        {
            string s = fill(src[row]);

            for (int col = 1; col < Columns; ++col)
            {
                int idx = PageHeight * col + row;

                if (idx < src.Length) s += Separator + fill(src[idx]);
            }

            output.WriteLine("{0}", s);
        }
    }

    void DumpPage()
    {
        DumpPage(LoadPage());
    }


    public static void Main(string[] args)
    {
        var opts = new Dictionary<string, string>();

        foreach (var arg in args)
        {
            if (!"/-".Contains(arg[0])) continue;

            var kv = arg.Substring(1).Split('=');

            if (kv.Length == 1)
                kv = kv[0].Split(':');
            
            if (kv.Length == 0) continue;

            var key = kv[0];
            var val = kv.Length > 1 ? kv[1] : "";

            opts.Add(key, val);
        }

        if (opts.ContainsKey("help"))
        {
            Console.WriteLine("SplitPager [opts] < input |more");
            Console.WriteLine("outions: -help -cols=N -w=N -h=N -sep=S -tab=N -offset=N");

            return;
        }

        var pager = new SplitPager(Console.In, Console.Out);

        if (opts.ContainsKey("cols"))
            pager.Columns = Int32.Parse(opts["cols"]);
        if (opts.ContainsKey("w"))
            pager.DisplayWidth = Int32.Parse(opts["w"]);
        if (opts.ContainsKey("h"))
            pager.PageHeight = Int32.Parse(opts["h"]);
        if (opts.ContainsKey("sep"))
            pager.Separator = opts["sep"];
        if (opts.ContainsKey("tab"))
            pager.TabWidth = Int32.Parse(opts["tab"]);
        if (opts.ContainsKey("offset"))
            pager.Offset = Int32.Parse(opts["offset"]);
        
        while (pager.HasNext)
        {
            pager.DumpPage();
        }
    }
}
