#!/usr/bin/env python3
"""Resolve literal git commit targets without executing the submitted shell command."""
import os
from pathlib import Path
import shlex
import subprocess
import sys


def commit_roots(command, cwd):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    segments, segment = [], []
    for word in lexer:
        if word and all(c in ";&|()\n" for c in word):
            segments.append(segment)
            segment = []
        else:
            segment.append(word)
    segments.append(segment)
    for words in segments:
        if not words:
            continue
        if words[0] in ("command", "exec", "env"):
            words = words[1:]
        # Inspect syntax only. Never import PATH or other command-supplied environment
        # values into the resolver process used for read-only Git discovery.
        while words and "=" in words[0] and not words[0].startswith("-"):
            words.pop(0)
        if not words:
            continue
        # Expansions and shell aliases are outside static inspection. Never eval them.
        if words[0] == "cd" and len(words) == 2:
            if not any(c in words[1] for c in "$`~"):
                target = Path(cwd, words[1]).resolve()
                if target.is_dir():
                    cwd = str(target)
            continue
        if Path(words[0]).name != "git":
            continue
        prefix, index = ["git"], 1
        while index < len(words):
            arg = words[index]
            if arg in ("-C", "--git-dir", "--work-tree", "-c"):
                if index + 1 >= len(words):
                    break
                value = words[index + 1]
                if any(c in value for c in "$`~"):
                    break
                # Configuration overrides are unnecessary for worktree discovery.
                if arg != "-c":
                    prefix.extend((arg, value))
                index += 2
                continue
            if arg.startswith(("--git-dir=", "--work-tree=", "-C")):
                if any(c in arg for c in "$`~"):
                    break
                prefix.append(arg)
            elif arg in ("--no-pager", "--paginate", "--literal-pathspecs", "--no-optional-locks"):
                pass
            elif arg == "commit":
                result = subprocess.run(prefix + ["rev-parse", "--show-toplevel"],
                                        cwd=cwd, capture_output=True)
                if result.returncode == 0:
                    yield os.fsdecode(result.stdout[:-1] if result.stdout.endswith(b"\n") else result.stdout)
                break
            else:
                break
            index += 1


if __name__ == "__main__":
    try:
        for root in dict.fromkeys(commit_roots(sys.stdin.read(), sys.argv[1])):
            sys.stdout.buffer.write(os.fsencode(root) + b"\0")
    except (OSError, ValueError):
        # Keep the hook's existing fail-open policy for unresolvable input.
        pass
