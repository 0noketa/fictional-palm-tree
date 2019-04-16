// simple translator
/* language:
    lines starts with "//[]":
      command that will be separated at every '/'.
      first element means function, others are parameters.
     
      commands:
        byKey:
          param0: 
            directory
          param1..(joined with '/'):
            regex
          usage:
            generates file names in JSON.
            regex should contains a group as key. and treats entire file names as elements.
          example:
            script:
              //[]byKey/mydir/([a-z]+)_[0-9]+.txt
            files:
              mydir/
                abc_0.txt
                abc_2.txt
                def_0.txt
            output(not in this format):
              { "abc" : [ "abc_0.txt", "abc_2.txt" ]
              , "def" : [ "def_0.txt" ] } 
    lines does not start with "//[]":
      just print.
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;


class JsonInjector
{
    public static void Main(string[] args)
    {
        Translate(Console.In, Console.Out);
    }
    static void Translate(TextReader input, TextWriter output)
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

            var cmdElms = s.Substring(4).Split('/');

            if (cmdElms[0] == "byKeys" && cmdElms.Length == 3)
            {
                var dirPath = cmdElms[1];
                var regexStr = string.Join("/", cmdElms.Skip(2));

                if (!regexStr.StartsWith("^")) regexStr = "^" + regexStr;
                if (!regexStr.EndsWith("$")) regexStr = regexStr + "$";

                var regex = new Regex(regexStr, RegexOptions.ECMAScript);

                Dump(output, dirPath, regex);
            }
            else
            {
                output.WriteLine("// unknown command: {0}", s);
            }
        }
    }

    static Dictionary<string, List<string>> DicFromDir(string dirPath, Regex regex)
    {
        var r = new Dictionary<string, List<string>>();
        var d = new DirectoryInfo(dirPath);

        foreach (var f in d.GetFiles())
        {
            var fileName = f.Name;
            var match = regex.Match(fileName);

            if (!match.Success || match.Groups.Count == 1) continue;

            var v = match.Groups[1].Value;

            if (!r.ContainsKey(v))
                r.Add(v, new List<string>());

            r[v].Add(fileName);
        }

        return r;
    }

    static void Dump(TextWriter output, string dirPath, Regex regex)
    {
        var dic = DicFromDir(dirPath, regex);

        Action act_colon = () => output.Write(", ");

        Action sep = () => { };

        output.Write("{ ");

        foreach (var key in dic.Keys)
        {
            sep();

            output.WriteLine("\"{0}\" :", key);

            Action sep2 = () => { };

            output.Write("[ ");

            foreach (var key2 in dic[key])
            {
                sep2();

                output.WriteLine("\"{0}\"", key2);

                sep2 = act_colon;
            }

            output.WriteLine("]");

            sep = act_colon;
        }

        output.WriteLine("}");
    }
}
