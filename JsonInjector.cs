// simple translator
/* language:
    lines starts with "//[]":
      command that is a list separated at every '/'.
      first element means function, others are parameters.
      commands do not read or modify any other command.
      any command that reads files can not accept any file name includes special characters.

      commands:
        byKey:
          param0: 
            directory
          param1..(joined with '/'):
            regex
          usage:
            generates file names in JSON object.
            regex should contains a group as key. and treats entire file names as elements.
          example:
            script:
              //[]byKey/mydir/([a-z]+)_[0-9]+\.txt
            files:
              mydir/
                abc_0.txt
                abc_2.txt
                def_0.txt
            output(not in this format):
              { "abc" : [ "abc_0.txt", "abc_2.txt" ]
              , "def" : [ "def_0.txt" ] } 
        all:
          param0: 
            directory
          param1..(joined with '/'):
            regex (optional)
          usage:
            generates file names in JSON array.
            regex is guard. if omitted, all files are accepted.
          example:
            script:
              //[]all/mydir/[a-z]+\.txt
            files:
              mydir/
                abc_0.txt
                abc_1.bin
                abc_2.txt
                def_1.bin
                def_4.txt
            output:
              [ "abc_0.txt"
              , "abc_2.txt"
              , "def_4.txt"
              ]
        (not implemented):
        defineComment:
          param0:
            label
          param1:
            regex
          usage:
            defines line-comments.
        undefComment:
          param0:
            label
          usage:
            defines line-comments.
          example:
            input:
              //[]defineComment/div/\/.*
              var x = (1
              / 2
              / 3
              + 4
              )
              //[]undefComment/div
              var y = (1
              / 2
              / 3
              + 4
              )
            output:
              var x = (1
              + 4
              )
              var y = (1
              / 2
              / 3
              + 4
              )
        beginScan:
          param0:
            label
          param1:
            regex with 1 group
          param2:
            integer. size of queue. (optional. default=256)
          usage:
            begins to scan input. group values to queue.
        endScan:
          param0:
            label
          usage:
            ends scanning.
        scanned:
          param0:
            label
          usage:
            dump scanned values as array.
          example:
            input:
              //[]beginScan/enum/var\s+(TYPE_[A-Z_]+[A-Z_0-9]*)\s*\=\s*[0-9]+\s*\;
              //[]beginScan/name/var\s+TYPE_([A-Z_]+[A-Z_0-9]*)\s*\=\s*[0-9]+\s*\;
              var TYPE_INT = 0;
              var TYPE_STR = 1;
              var TYPE_ARRAY = 2;
              //[]endScan/enum
              //[]endScan/name
              var typeNameByEnum =
              //[]scanned/name
              var stringifiedByEnum =
              //[]scanned/enum
            output:
              var TYPE_INT = 0;
              var TYPE_STR = 1;
              var TYPE_ARRAY = 2;
              var typeNameByEnum =
              [ "INT"
              , "STR"
              , "ARRAY"
              ]
              var stringifiedByEnum =
              [ "TYPE_INT"
              , "TYPE_STR"
              , "TYPE_ARRAY"
              ]
    other lines:
      just print.
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;


public class JsonInjector
{
    public static void Main(string[] args)
    {
        if (args.Length > 0)
            Eval(args, Console.Out);
        else
            Translate(Console.In, Console.Out);
    }

    public static void Translate(TextReader input, TextWriter output)
    {
        string s;

        while (true)
        {
            try
            {
                s = input.ReadLine();
            }
            catch (Exception _)
            {
                break;
            }

            if (s == null)
                break;

            if (!s.StartsWith("//[]"))
            {
                output.WriteLine(s);

                continue;
            }

            if (!Eval(s.Substring(4).Split('/'), output))
                output.WriteLine("//][ unknown command: {0}", s);
        }
    }

    static bool Eval(string[] cmd, TextWriter output)
    {
        if (cmd[0] == "byKey" && cmd.Length >= 3)
        {
            var dirPath = cmd[1];
            var regex = RegexFromSlicedPatterns(cmd.Skip(2));

            DumpFileDic(output, dirPath, regex);

            return true;
        }

        if (cmd[0] == "all" && cmd.Length >= 2)
        {
            var dirPath = cmd[1];
            Regex regex = cmd.Length >= 3
                ? RegexFromSlicedPatterns(cmd.Skip(2))
                : null;

            DumpFileList(output, dirPath, regex);

            return true;
        }

        return false;
    }

    static string CompleteRegexStr(string regexStr)
    {
        if (!regexStr.StartsWith("^")) regexStr = "^" + regexStr;
        if (!regexStr.EndsWith("$")) regexStr = regexStr + "$";

        return regexStr;
    }

    static Regex RegexFromSlicedPatterns(IEnumerable<string> src)
    {
        var regexStr = CompleteRegexStr(string.Join("/", src));

        return new Regex(regexStr, RegexOptions.ECMAScript);
    }

    static List<string> ListFromDir(string dirPath, Regex regex = null)
    {
        var r = new List<string>();

        dirPath = dirPath.Trim();

        if (dirPath.Contains("\\"))
        {
            IEnumerable<string> r2 = r;
            var ds = dirPath.Split('\\');

            foreach (var d in ds)
                if (d != "")
                    r2 = r2.Concat(ListFromDir(d, regex));
            
            return r2.ToList();
        }

        if (new Regex("^(?:.*(?:\\:|\\;|\\,|\\s).*|\\~|\\.{2,})$").IsMatch(dirPath))
            return r;

        try
        {
            var d = new DirectoryInfo(dirPath);

            foreach (var f in d.GetFiles())
            {
                var fileName = f.Name;

                if (regex != null)
                {
                    var match = regex.Match(fileName);

                    if (!match.Success) continue;
                }
                
                r.Add(fileName);
            }
        }
        catch (Exception _)
        { }

        return r;
    }

    static Dictionary<string, List<string>> DicFromDir(string dirPath, Regex regex)
    {
        var r = new Dictionary<string, List<string>>();
        var list = ListFromDir(dirPath);

        foreach (var fileName in list)
        {
            var match = regex.Match(fileName);

            if (!match.Success || match.Groups.Count == 1) continue;

            var v = FirstNotEmptyGroupValue(match.Groups);

            if (!r.ContainsKey(v))
                r.Add(v, new List<string>());

            r[v].Add(fileName);
        }

        return r;
    }

    // first filled group
    static string FirstNotEmptyGroupValue(GroupCollection groups)
    {
        for (int i = 1; i < groups.Count; ++i)
            if (groups[i].Value != "")
                return groups[i].Value;
        
        return "";
    }

    static void DumpFileDic(TextWriter output, string dirPath, Regex regex)
    {
        var dic = DicFromDir(dirPath, regex);

        Dump(output, dic);
    }

    static void DumpFileList(TextWriter output, string dirPath, Regex regex = null)
    {
        var list = ListFromDir(dirPath, regex);

        Dump(output, list);
    }

    static void Dump(TextWriter output, Dictionary<string, List<string>> dic)
    {
        Action act_colon = () => output.Write(", ");

        Action sep = () => { };

        output.Write("{ ");

        foreach (var key in dic.Keys)
        {
            sep();

            output.WriteLine("\"{0}\" :", key);

            Dump(output, dic[key]);

            sep = act_colon;
        }

        output.WriteLine("}");
    }

    static void Dump(TextWriter output, List<string> list)
    {
        Action act_colon = () => output.Write(", ");

        Action sep = () => { };

        output.Write("[ ");

        foreach (var key in list)
        {
            sep();

            output.WriteLine("\"{0}\"", key);

            sep = act_colon;
        }

        output.WriteLine("]");
    }
}
