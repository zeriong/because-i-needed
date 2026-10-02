"""free-hands hard-limit check for one shell command line (used by guard.py's `shell` mode).

`check(command, cwd, declared_default)` returns ((category, part) or None, default-branch source). It denies the
ordinary commands a cooperative agent would run to merge into the default branch, delete something remote, or
deploy/publish/send outside. It is a backstop, not a defense against deliberate evasion (the skill's rules forbid
that): heredoc bodies, scripts, interactive sessions, `rm`, database clients and other CLIs are not read.
"""
from fnmatch import fnmatch
import os
import re
import shlex
import subprocess

KEYWORD = re.compile(r"(gh|git|npm|pnpm|yarn|npx|bunx|cargo|twine|gem|docker|vercel|netlify|fly|flyctl|firebase|"
                     r"terraform|kubectl|helm|sendmail|mail|mutt)")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
SEND = {"sendmail", "mail", "mutt"}
SKIP_LEADING = {"!", "{", "}", "then", "else", "elif", "do", "if", "while", "until", "fi", "done", "esac"}
SKIP_COMMAND = {"for", "case", "select", "function"}
GRAPHQL_MERGE = re.compile(r"\b(mergePullRequest|mergeBranch|enablePullRequestAutoMerge)\b")
GRAPHQL_DELETE = re.compile(r"\b(deleteRef|deleteRepository)\b")
UNKNOWN = "<unknown>"


class Unparsable(Exception):
    pass


# ---- tokenizer ---------------------------------------------------------------------------------------------------

REDIRECTS = ("&>>", "<<<", "<<-", "<<", ">>", ">|", "&>", "<&", ">&", "<>", "<", ">")
OPERATORS = ("&&", "||", ";;", "|&", ";", "&", "|", "(", ")")


def tokenize(text):
    """Shell tokens: ("word", value, substitutions) with quotes removed, ("op", op), ("redir", op). Substitutions are
    the `$( … )` / backtick texts that the shell would run (unquoted or in double quotes, not in single quotes)."""
    tokens, i, n = [], 0, len(text)
    word, subs, in_word, heredocs = [], [], False, []

    def end_word():
        nonlocal word, subs, in_word
        if in_word:
            tokens.append(("word", "".join(word), subs))
        word, subs, in_word = [], [], False

    def read_subst(start):
        """text[start] is just after "$(" — return (inner, index after the closing paren)."""
        depth, j, quote = 1, start, None
        while j < n:
            c = text[j]
            if quote:
                if c == quote:
                    quote = None
                elif c == "\\" and quote == '"':
                    j += 1
            elif c in "'\"":
                quote = c
            elif c == "\\":
                j += 1
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return text[start:j], j + 1
            j += 1
        raise Unparsable("unterminated $(")

    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n and text[i + 1] == "\n":  # line continuation: removed by the shell
            i += 2
            continue
        if c == "\n":
            end_word()
            tokens.append(("op", "\n"))
            i += 1
            for delimiter, strip_tabs in heredocs:  # skip each pending heredoc body (data in the core scope)
                while True:
                    if i >= n:
                        raise Unparsable("unterminated heredoc")
                    j = text.find("\n", i)
                    line = text[i:] if j < 0 else text[i:j]
                    i = n if j < 0 else j + 1
                    if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                        break
            heredocs = []
            continue
        if c in " \t\r":
            end_word()
            i += 1
            continue
        if c == "#" and not in_word:
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "'":
            j = text.find("'", i + 1)
            if j < 0:
                raise Unparsable("unterminated single quote")
            word.append(text[i + 1:j])
            in_word, i = True, j + 1
            continue
        if c == '"':
            j, in_word = i + 1, True
            while True:
                if j >= n:
                    raise Unparsable("unterminated double quote")
                d = text[j]
                if d == '"':
                    break
                if d == "\\" and j + 1 < n and text[j + 1] in '"\\$`\n':
                    if text[j + 1] != "\n":
                        word.append(text[j + 1])
                    j += 2
                    continue
                if text.startswith("$((", j):
                    word.append("$((")
                    j += 3
                    continue
                if text.startswith("$(", j):
                    inner, j = read_subst(j + 2)
                    subs.append(inner)
                    word.append("$(" + inner + ")")
                    continue
                if d == "`":
                    k = text.find("`", j + 1)
                    if k < 0:
                        raise Unparsable("unterminated backtick")
                    subs.append(text[j + 1:k])
                    word.append(text[j:k + 1])
                    j = k + 1
                    continue
                word.append(d)
                j += 1
            i = j + 1
            continue
        if c == "\\":
            if i + 1 < n:
                word.append(text[i + 1])
            in_word, i = True, i + 2
            continue
        if text.startswith("$((", i):
            word.append("$((")
            in_word, i = True, i + 3
            continue
        if text.startswith("$(", i):
            inner, i = read_subst(i + 2)
            subs.append(inner)
            word.append("$(" + inner + ")")
            in_word = True
            continue
        if c == "`":
            k = text.find("`", i + 1)
            if k < 0:
                raise Unparsable("unterminated backtick")
            subs.append(text[i + 1:k])
            word.append(text[i:k + 1])
            in_word, i = True, k + 1
            continue
        redirect = next((op for op in REDIRECTS if text.startswith(op, i)), None)
        if redirect:
            if in_word and "".join(word).isdigit():  # an fd number such as 2>
                word, subs, in_word = [], [], False
            end_word()
            tokens.append(("redir", redirect))
            i += len(redirect)
            if redirect in ("<<", "<<-"):
                while i < n and text[i] in " \t":
                    i += 1
                match = re.match(r"(['\"]?)([^\s;&|()<>'\"]+)\1", text[i:])
                if not match:
                    raise Unparsable("heredoc without a delimiter")
                heredocs.append((match.group(2), redirect == "<<-"))
                tokens.append(("word", match.group(2), []))
                i += match.end()
            continue
        operator = next((op for op in OPERATORS if text.startswith(op, i)), None)
        if operator:
            end_word()
            tokens.append(("op", operator))
            i += len(operator)
            continue
        word.append(c)
        in_word, i = True, i + 1
    end_word()
    if heredocs:
        raise Unparsable("unterminated heredoc")
    return tokens


# ---- option helpers ----------------------------------------------------------------------------------------------

def parse_options(args, takes_value):
    """Split args into (positionals, [(option, value)]) — `--opt=v`, `--opt v` and `-Xv` / `-X v` for listed options."""
    positionals, options, i = [], [], 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            positionals.extend(args[i + 1:])
            break
        if arg.startswith("--") and len(arg) > 2:
            name, eq, value = arg.partition("=")
            if eq:
                options.append((name, value))
            elif name in takes_value and i + 1 < len(args):
                options.append((name, args[i + 1]))
                i += 1
            else:
                options.append((name, None))
        elif arg.startswith("-") and len(arg) > 1:
            name = arg[:2]
            if name in takes_value:
                if len(arg) > 2:
                    options.append((name, arg[2:]))
                elif i + 1 < len(args):
                    options.append((name, args[i + 1]))
                    i += 1
                else:
                    options.append((name, None))
            else:
                options.append((arg, None))
        else:
            positionals.append(arg)
        i += 1
    return positionals, options


def has(options, *names):
    return any(name in names for name, _ in options)


def wants_help(options):
    return any(name in ("--help", "-h") and value is None for name, value in options)


def truthy_flag(options, name, negation, dry_values=("true", "1", "yes")):
    """The last occurrence decides: `--name` / `--name=true` on, `--name=false` / `--negation` off."""
    state = False
    for option, value in options:
        if option == name:
            state = value is None or value.lower() in dry_values
        elif option == negation:
            state = False
    return state


# ---- git helpers -------------------------------------------------------------------------------------------------

def git_out(cwd, git_args, *args, env=None):
    try:
        result = subprocess.run(["git", "-C", cwd, *git_args, *args], capture_output=True, text=True, timeout=5,
                                env={**os.environ, **(env or {})})
    except (OSError, subprocess.SubprocessError):
        return None
    out = result.stdout.strip()
    return out if result.returncode == 0 and out else None


class Context:
    def __init__(self, cwd, declared_default):
        self.goal_root = git_out(cwd, [], "rev-parse", "--show-toplevel")
        self.declared = declared_default
        self.branches = {}   # repository root → set of branches it may be on (shared by subshells: HEAD is repo state)
        self.pending = {}    # repository root → branches it keeps if a conditional switch did not run
        self.sources = set()

    def root(self, cwd, git_args, env):
        return git_out(cwd, git_args, "rev-parse", "--show-toplevel", env=env) or cwd

    def current(self, cwd, git_args, env):
        root = self.root(cwd, git_args, env)
        if root not in self.branches:
            head = git_out(cwd, git_args, "rev-parse", "--abbrev-ref", "HEAD", env=env)
            self.branches[root] = {head or UNKNOWN}
        return self.branches[root]

    def switch(self, cwd, git_args, env, branch, conditional, outcome):
        """outcome: "success", "fail" or "unknown" (predicted from the refs). A conditional switch (after && or ||)
        holds on the && path; once the chain ends (;, newline, ||, &, |) the old branch is possible again."""
        root = self.root(cwd, git_args, env)
        before = set(self.current(cwd, git_args, env))
        if outcome == "fail":
            return
        if conditional:
            self.pending.setdefault(root, set()).update(before)
        self.branches[root] = {branch} if outcome == "success" else before | {branch}

    def settle(self):
        for root, older in self.pending.items():
            self.branches[root] = self.branches.get(root, set()) | older
        self.pending = {}

    def defaults(self, cwd, git_args, env, remote=None):
        root = self.root(cwd, git_args, env)
        if self.declared and root == self.goal_root:
            self.sources.add("goal file")
            return {self.declared}
        remote_list = [remote] if remote else (git_out(cwd, git_args, "remote", env=env) or "origin").split()
        for name in remote_list:
            head = git_out(cwd, git_args, "symbolic-ref", "--short", f"refs/remotes/{name}/HEAD", env=env)
            if head and "/" in head:
                self.sources.add(f"{name}/HEAD")
                return {head.split("/", 1)[1]}
        self.sources.add("assumed: main and master")
        return {"main", "master"}


# ---- checker -----------------------------------------------------------------------------------------------------

class Checker:
    def __init__(self, context):
        self.ctx = context

    def line(self, text, cwd):
        return self.run_tokens(tokenize(text), {"cwd": cwd})

    def run_tokens(self, tokens, state):
        command, conditional, i = [], False, 0
        while i < len(tokens):
            kind = tokens[i][0]
            value = tokens[i][1]
            if kind == "op" and value == "(":
                depth, j = 1, i + 1
                while j < len(tokens) and depth:
                    if tokens[j][:2] == ("op", "("):
                        depth += 1
                    elif tokens[j][:2] == ("op", ")"):
                        depth -= 1
                    j += 1
                hit = self.run_tokens(tokens[i + 1:j - 1], dict(state))
                if hit:
                    return hit
                i = j
                continue
            if kind == "op":
                hit = self.simple(command, state, conditional)
                if hit:
                    return hit
                if value != "&&":
                    self.ctx.settle()
                conditional = value in ("&&", "||") or (conditional and value == "|")
                command = []
            elif kind == "redir":
                i += 1  # drop the redirection target
            else:
                command.append(tokens[i])
            i += 1
        return self.simple(command, state, conditional)

    def simple(self, tokens, state, conditional):
        if not tokens:
            return None
        for _, _, subs in tokens:
            for inner in subs:
                hit = self.run_tokens(tokenize(inner), dict(state))
                if hit:
                    return hit
        words = [value for _, value, _ in tokens]
        while words and words[0] in SKIP_LEADING:
            words = words[1:]
        if not words or words[0] in SKIP_COMMAND:
            return None
        env, words, cwd_override = self.unwrap(words, state)
        if not words:
            return None
        if cwd_override:
            state = dict(state, cwd=cwd_override)  # env -C changes the child's directory only
        name, args = os.path.basename(words[0]), words[1:]
        if name in SHELLS:
            script = shell_script(args)
            return self.run_tokens(tokenize(script), dict(state)) if script is not None else None
        if name == "cd":
            while args and re.fullmatch(r"-[LPeqs@]+", args[0]):
                args = args[1:]
            if args and args[0] == "--":
                args = args[1:]
            target = args[0] if args else "~"
            if target != "-":
                state["cwd"] = os.path.normpath(os.path.join(state["cwd"], os.path.expanduser(target)))
            return None
        if name == "git":
            return self.git(args, state, env, conditional)
        if name == "gh":
            return gh(args)
        return publish(name, args)

    def unwrap(self, words, state):
        env, cwd = {}, None
        while words:
            first = os.path.basename(words[0])
            if ASSIGNMENT.match(words[0]):
                key, _, value = words[0].partition("=")
                env[key] = value
                words = words[1:]
            elif first == "env":
                words = words[1:]
                while words:
                    w = words[0]
                    if w in ("-u", "--unset", "-C", "--chdir") and len(words) > 1:
                        if w in ("-C", "--chdir"):
                            cwd = os.path.normpath(os.path.join(cwd or state["cwd"], words[1]))
                        words = words[2:]
                    elif w.startswith("--chdir="):
                        cwd = os.path.normpath(os.path.join(cwd or state["cwd"], w.split("=", 1)[1]))
                        words = words[1:]
                    elif w in ("-S", "--split-string") and len(words) > 1:
                        words = shlex.split(words[1]) + words[2:]
                    elif w.startswith("--split-string="):
                        words = shlex.split(w.split("=", 1)[1]) + words[1:]
                    elif w == "--":
                        words = words[1:]
                        break
                    elif w.startswith("-") or ASSIGNMENT.match(w):
                        if ASSIGNMENT.match(w):
                            key, _, value = w.partition("=")
                            env[key] = value
                        words = words[1:]
                    else:
                        break
            elif first == "sudo":
                words = words[1:]
                while words and words[0].startswith("-"):
                    if words[0] == "--":
                        words = words[1:]
                        break
                    takes = words[0] in ("-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U", "-T")
                    words = words[2:] if takes else words[1:]
            elif first == "command":
                words = words[1:]
                if words and words[0] in ("-v", "-V"):
                    return env, [], cwd
                while words and words[0].startswith("-"):
                    words = words[1:]
            elif first == "exec":
                words = words[1:]
                while words and words[0].startswith("-"):
                    words = words[2:] if words[0] == "-a" else words[1:]
            elif first in ("time", "nohup"):
                words = words[1:]
                while words and words[0].startswith("-"):
                    words = words[1:]
            elif first == "nice":
                words = words[1:]
                if words and words[0] in ("-n", "--adjustment"):
                    words = words[2:]
                elif words and (re.match(r"^-\d+$", words[0]) or words[0].startswith("--adjustment=")):
                    words = words[1:]
            elif first == "timeout":
                words = words[1:]
                while words and words[0].startswith("-"):
                    words = words[2:] if words[0] in ("-s", "--signal", "-k", "--kill-after") else words[1:]
                words = words[1:]
            elif first in ("npx", "bunx") or (first in ("npm", "pnpm", "yarn") and subcommand_index(words[1:], NPM_VALUE, NPM_COMMANDS)[1] in ("exec", "x", "dlx")):
                if first in ("npx", "bunx"):
                    words = words[1:]
                else:
                    index, _ = subcommand_index(words[1:], NPM_VALUE, NPM_COMMANDS)
                    words = words[index + 2:]
                while words and words[0].startswith("-"):
                    w = words[0]
                    if w == "--":
                        words = words[1:]
                        break
                    if w in ("-c", "--call") and len(words) > 1:
                        words = shlex.split(words[1])
                        break
                    takes = w in ("-p", "--package") or (w in NPM_VALUE and "=" not in w)
                    words = words[2:] if takes else words[1:]
            else:
                return env, words, cwd
        return env, words, cwd

    # -- git ------------------------------------------------------------------------------------------------------
    def git(self, args, state, env, conditional):
        cwd, git_args = state["cwd"], []
        git_env = {k: v for k, v in env.items() if k.startswith("GIT_")}
        while args and args[0].startswith("-"):
            option = args[0]
            if option == "-C" and len(args) > 1:
                cwd = os.path.normpath(os.path.join(cwd, os.path.expanduser(args[1])))
                args = args[2:]
            elif option == "-c" and len(args) > 1:
                git_args += ["-c", args[1]]
                args = args[2:]
            elif option in ("--git-dir", "--work-tree", "--namespace") and len(args) > 1:
                git_args += [option, args[1]]
                args = args[2:]
            elif option.startswith(("--git-dir=", "--work-tree=", "--namespace=")):
                git_args.append(option)
                args = args[1:]
            else:
                args = args[1:]
        if not args:
            return None
        sub, rest = args[0], args[1:]
        where = (cwd, git_args, git_env)
        if sub == "switch":
            positionals, options = parse_options(rest, {"-c", "-C", "--create", "--force-create", "--orphan"})
            if wants_help(options):
                return None
            creating = [(name, value) for name, value in options
                        if name in ("-c", "-C", "--create", "--force-create", "--orphan")]
            target = creating[0][1] if creating else (positionals[0] if positionals else None)
            if target and not has(options, "-d", "--detach"):
                force = creating and creating[0][0] in ("-C", "--force-create")
                self.ctx.switch(*where, UNKNOWN if target == "-" else target, conditional,
                                predict(where, target, bool(creating), force))
            return None
        if sub == "checkout":
            return self.git_checkout(rest, where, conditional)
        if sub == "merge":
            return self.git_merge(rest, where)
        if sub == "pull":
            return self.git_pull(rest, where)
        if sub == "push":
            return self.git_push(rest, where)
        return None

    def git_checkout(self, rest, where, conditional):
        if "--" in rest:
            before, paths = rest[:rest.index("--")], rest[rest.index("--") + 1:]
            if paths:
                return None  # restores files; the branch stays
            rest = before
        positionals, options = parse_options(rest, {"-b", "-B", "--orphan"})
        if wants_help(options):
            return None
        creating = [(name, value) for name, value in options if name in ("-b", "-B", "--orphan")]
        if creating:
            self.ctx.switch(*where, creating[0][1], conditional,
                            predict(where, creating[0][1], True, creating[0][0] == "-B"))
            return None
        if len(positionals) != 1:
            return None
        target = positionals[0]
        cwd, git_args, env = where
        is_branch = target == "-" or git_out(cwd, git_args, "rev-parse", "--verify", "--quiet", f"refs/heads/{target}",
                                             env=env) or not os.path.exists(os.path.join(cwd, target))
        if is_branch:
            self.ctx.switch(*where, UNKNOWN if target == "-" else target, conditional,
                            predict(where, target, False, False))
        return None

    def own_upstream(self, branch, where):
        cwd, git_args, env = where
        upstream = git_out(cwd, git_args, "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}", env=env)
        return {upstream} if upstream else set()

    def git_merge(self, rest, where):
        positionals, options = parse_options(rest, {"-m", "--message", "-F", "--file", "-s", "--strategy", "-X",
                                                    "--strategy-option", "--into-name", "--cleanup"})
        if wants_help(options) or has(options, "--abort", "--quit", "--continue"):
            return None
        defaults = self.ctx.defaults(*where)
        for branch in self.ctx.current(*where):
            if branch not in defaults and branch != UNKNOWN:
                continue
            allowed = self.own_upstream(branch, where) | {"@{u}", "@{upstream}", f"{branch}@{{u}}"}
            if positionals and not all(source in allowed for source in positionals):
                return ("merge", "git merge " + " ".join(rest) + f" (on {branch})")
        return None

    def git_pull(self, rest, where):
        positionals, options = parse_options(rest, {"-s", "--strategy", "-X", "--strategy-option", "--depth"})
        if wants_help(options) or len(positionals) < 2:
            return None  # `git pull` / `git pull <remote>` follows the branch's own upstream
        remote, refs = positionals[0], positionals[1:]
        defaults = self.ctx.defaults(*where)
        for branch in self.ctx.current(*where):
            if branch not in defaults and branch != UNKNOWN:
                continue
            upstream = self.own_upstream(branch, where)
            if not all(f"{remote}/{ref.split(':', 1)[0]}" in upstream for ref in refs):
                return ("merge", f"git pull {' '.join(rest)} (on {branch})")
        return None

    def push_remote(self, branch, where):
        cwd, git_args, env = where
        for key in (f"branch.{branch}.pushRemote", "remote.pushDefault", f"branch.{branch}.remote"):
            value = git_out(cwd, git_args, "config", "--get", key, env=env)
            if value and value != ".":
                return value
        return "origin"

    def git_push(self, rest, where):
        positionals, options = parse_options(rest, {"-o", "--push-option", "--repo", "--receive-pack", "--exec"})
        if wants_help(options) or truthy_flag(options, "--dry-run", "--no-dry-run") or has(options, "-n"):
            return None
        if has(options, "--delete", "-d", "--prune", "--mirror"):
            return ("remote deletion", "git push " + " ".join(rest))
        if has(options, "--all", "--branches"):
            return ("merge", "git push " + " ".join(rest) + " (pushes every branch, the default one included)")
        cwd, git_args, env = where
        repo = next((value for name, value in options if name == "--repo"), None)
        explicit_remote = repo or (positionals[0] if positionals else None)
        refspecs = positionals if repo else positionals[1:]
        branches = self.ctx.current(*where)
        for branch in branches:
            remote = explicit_remote or (self.push_remote(branch, where) if branch != UNKNOWN else "origin")
            if (git_out(cwd, git_args, "config", "--get", f"remote.{remote}.mirror", env=env) or "").lower() == "true":
                return ("remote deletion", f"git push {remote} (remote.{remote}.mirror)")
            configured = (git_out(cwd, git_args, "config", "--get-all", f"remote.{remote}.push", env=env) or "").split()
            defaults = self.ctx.defaults(*where, remote)
            specs = list(refspecs)
            if not specs and has(options, "--tags"):
                continue
            if not specs:
                mode = (git_out(cwd, git_args, "config", "--get", "push.default", env=env) or "simple").lower()
                if configured:
                    specs = configured
                elif mode == "matching":
                    return ("merge", f"git push {remote} (push.default=matching)")
                elif explicit_remote:
                    # push.default current/simple push the branch to the same name on the named remote; upstream
                    # mode uses the upstream's name only when the named remote is the upstream's remote
                    name = branch
                    if mode == "upstream":
                        upstream = next(iter(self.own_upstream(branch, where)), "")
                        if upstream.startswith(f"{explicit_remote}/"):
                            name = upstream.split("/", 1)[1]
                    if name in defaults or name == UNKNOWN:
                        return ("merge", f"git push {explicit_remote} (updates {name})")
                    continue
                else:
                    target = None if branch == UNKNOWN else git_out(cwd, git_args, "rev-parse", "--abbrev-ref",
                                                                    f"{branch}@{{push}}", env=env)
                    if target and "/" in target:
                        target_remote, name = target.split("/", 1)
                        defaults = self.ctx.defaults(*where, target_remote)
                    else:
                        name = branch
                    if name in defaults or name == UNKNOWN:
                        return ("merge", f"git push (updates {name})")
                    continue
            elif configured:
                mapped_specs = []
                for spec in specs:
                    mapped = map_configured(spec.lstrip("+"), configured) if ":" not in spec.lstrip("+") else []
                    mapped_specs += [f"{spec.lstrip('+')}:{dst}" for dst in mapped] or [spec]
                specs = mapped_specs
            hit = self.refspecs_hit(remote, specs, defaults, branches)
            if hit:
                return hit
        return None

    @staticmethod
    def refspecs_hit(remote, specs, defaults, branches):
        for spec in specs:
            bare = spec.lstrip("+")
            if bare == ":":
                return ("merge", f"git push {remote} : (matching branches, the default one included)")
            if bare.startswith(":"):
                return ("remote deletion", f"git push {remote} {spec}")
            dst = bare.split(":", 1)[1] if ":" in bare else bare
            if dst.startswith("refs/tags/"):
                continue
            dst = dst[len("refs/heads/"):] if dst.startswith("refs/heads/") else dst
            targets = branches if dst == "HEAD" else {dst}
            for target in targets:
                if target == UNKNOWN or any(fnmatch(default, target) for default in defaults):
                    return ("merge", f"git push {remote} {spec}")
        return None


def predict(where, target, creating, force):
    """Whether `git switch`/`checkout` to target would succeed, judged from the refs that exist now."""
    if target == "-":
        return "unknown"
    cwd, git_args, env = where
    exists = git_out(cwd, git_args, "rev-parse", "--verify", "--quiet", f"refs/heads/{target}", env=env)
    if creating and exists and not force:
        return "fail"
    if exists:
        here = git_out(cwd, git_args, "rev-parse", "--show-toplevel", env=env)
        listing = git_out(cwd, git_args, "worktree", "list", "--porcelain", env=env) or ""
        for block in listing.split("\n\n"):
            lines = block.splitlines()
            path = lines[0][len("worktree "):] if lines and lines[0].startswith("worktree ") else None
            if f"branch refs/heads/{target}" in lines and path and os.path.realpath(path) != os.path.realpath(here or ""):
                return "fail"  # git: "'<branch>' is already checked out at <worktree>"
        return "success"
    if creating:
        return "success"
    remote = git_out(cwd, git_args, "for-each-ref", "--format=%(refname)", f"refs/remotes/*/{target}", env=env)
    return "success" if remote and len(remote.split()) == 1 else "unknown"


def map_configured(source, configured):
    """Destinations a remote.<name>.push refspec gives an explicit source with no destination."""
    ref = source if source.startswith("refs/") else f"refs/heads/{source}"
    out = []
    for spec in configured:
        src, _, dst = spec.lstrip("+").partition(":")
        if not dst:
            continue
        if not src.startswith("refs/"):
            continue  # git maps an explicit source only through full-ref configured sources
        if src == ref:
            out.append(dst)
        elif "*" in src and fnmatch(ref, src):
            stem = ref[len(src.split("*", 1)[0]):len(ref) - len(src.split("*", 1)[1]) or None]
            out.append(dst.replace("*", stem, 1))
    return out


def shell_script(args):
    found_c, i = False, 0
    while i < len(args):
        arg = args[i]
        if arg in ("-o", "+o", "-O", "+O"):
            i += 2
            continue
        if arg == "--":
            i += 1
            continue
        if arg.startswith(("-", "+")) and not arg.startswith("--"):
            found_c = found_c or "c" in arg[1:]
            i += 1
            continue
        if arg.startswith("--"):
            i += 1
            continue
        return arg if found_c else None
    return "" if found_c else None


# ---- gh ----------------------------------------------------------------------------------------------------------

GH_VALUE = {"-R", "--repo", "-b", "--body", "-F", "--body-file", "-t", "--subject", "-A", "--author-email",
            "--match-head-commit", "-X", "--method", "-f", "--raw-field", "--field", "-H", "--header", "--hostname",
            "--input", "-q", "--jq", "--template", "--cache", "-p", "--preview", "--notes", "-n", "--notes-file",
            "--target", "--title"}


def gh(args):
    positionals, options = parse_options(args, GH_VALUE)
    if wants_help(options):
        return None
    head = positionals[:2]
    if head == ["pr", "merge"]:
        return ("merge", "gh pr merge " + " ".join(positionals[2:]))
    if head == ["repo", "delete"]:
        return ("remote deletion", "gh repo delete " + " ".join(positionals[2:]))
    if head == ["release", "delete"]:
        return ("remote deletion", "gh release delete " + " ".join(positionals[2:]))
    if head in (["release", "create"], ["release", "upload"]):
        return ("publish", "gh " + " ".join(positionals))
    if positionals[:1] == ["api"]:
        return gh_api(positionals[1:], options)
    return None


def gh_api(positionals, options):
    explicit = [value for name, value in options if name in ("-X", "--method") and value]
    fields = has(options, "-f", "-F", "--field", "--raw-field", "--input")
    method = explicit[-1].upper() if explicit else ("POST" if fields else "GET")
    endpoint = positionals[0] if positionals else ""
    text = " ".join(positionals + [value or "" for _, value in options])
    if endpoint == "graphql":
        if GRAPHQL_MERGE.search(text):
            return ("merge", "gh api graphql (merge mutation)")
        if GRAPHQL_DELETE.search(text):
            return ("remote deletion", "gh api graphql (delete mutation)")
        return None
    if method == "GET" or not endpoint:
        return None
    path = re.sub(r"^https?://[^/]+/", "", endpoint).split("?", 1)[0].strip("/")
    if re.search(r"(^|/)pulls/\d+/merge$", path) or path.endswith("/merges"):
        return ("merge", f"gh api -X {method} {endpoint}")
    if (method == "POST" and re.fullmatch(r"repos/[^/]+/[^/]+/releases", path)) or \
            (method == "PATCH" and re.fullmatch(r"repos/[^/]+/[^/]+/releases/\d+", path)) or \
            re.search(r"/releases/\d+/assets", path):
        return ("publish", f"gh api -X {method} {endpoint}")
    if method == "DELETE" and (re.search(r"/git/refs/", path) or re.search(r"/releases/", path)
                               or re.fullmatch(r"repos/[^/]+/[^/]+", path)):
        return ("remote deletion", f"gh api -X DELETE {endpoint}")
    return None


# ---- publish / deploy / send -------------------------------------------------------------------------------------

NPM_VALUE = {"--prefix", "-C", "--dir", "-w", "--workspace", "--registry", "--tag", "--access", "--otp", "--userconfig",
             "--filter", "--cache", "--cwd", "--loglevel", "--location", "--scope", "--globalconfig", "--script-shell"}
NPM_COMMANDS = {"publish", "run", "run-script", "exec", "x", "dlx", "install", "i", "add", "ci", "test", "t", "start",
                "stop", "restart", "build", "pack", "uninstall", "remove", "rm", "update", "up", "outdated", "ls", "list",
                "init", "create", "link", "version", "view", "info", "audit", "config", "set", "get", "cache", "login",
                "logout", "whoami", "npm", "workspaces", "why", "dedupe", "prune", "rebuild", "help", "doctor"}
KUBECTL_COMMANDS = {"get", "describe", "apply", "create", "replace", "patch", "delete", "rollout", "edit", "logs", "exec",
                    "port-forward", "diff", "explain", "config", "scale", "set", "label", "annotate", "top", "cp", "run",
                    "expose", "wait", "auth", "api-resources", "api-versions", "version", "cluster-info", "kustomize",
                    "events", "debug", "attach", "autoscale", "certificate", "drain", "cordon", "uncordon", "taint", "proxy",
                    "plugin", "completion"}
HELM_COMMANDS = {"install", "upgrade", "uninstall", "delete", "rollback", "list", "ls", "template", "lint", "package",
                 "pull", "push", "repo", "search", "show", "status", "history", "get", "test", "dependency", "env",
                 "version", "plugin", "registry", "create", "verify", "completion"}


def subcommand_index(args, takes_value, known):
    """(index in args, name) of the first word that is a known subcommand, skipping options and their values."""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            return (i + 1, args[i + 1]) if i + 1 < len(args) and args[i + 1] in known else (-1, None)
        if arg.startswith("-"):
            name = arg.split("=", 1)[0]
            i += 2 if "=" not in arg and (name in takes_value or name[:2] in takes_value and len(name) == 2) else 1
            continue
        if arg in known:
            return i, arg
        i += 1
    return -1, None
DOCKER_VALUE = {"--context", "-c", "-H", "--host", "--config", "--log-level", "-l", "-t", "--tag", "-f", "--file",
                "--platform", "--build-arg", "--target", "-o", "--output", "--builder", "--cache-from", "--cache-to"}
KUBECTL_VALUE = {"--context", "-n", "--namespace", "--kubeconfig", "--cluster", "--user", "-s", "--server", "--token",
                 "-f", "--filename", "-l", "--selector", "-o", "--output", "-k", "--kustomize", "--field-manager",
                 "--request-timeout", "--as", "--as-group", "--certificate-authority", "--client-certificate",
                 "--client-key", "-v", "--v"}
HELM_VALUE = {"--kube-context", "-n", "--namespace", "--kubeconfig", "-f", "--values", "--set", "--version", "--repo",
              "--kube-apiserver", "--kube-token", "--kube-as-user", "--registry-config", "--repository-config"}
VERCEL_VALUE = {"--token", "--scope", "-S", "--cwd", "-A", "--local-config", "-Q", "--global-config", "--team",
                "-e", "--env", "-b", "--build-env", "-m", "--meta", "--regions"}
VERCEL_LOCAL = {"dev", "env", "link", "login", "logout", "logs", "ls", "list", "inspect", "pull", "build", "whoami",
                "help", "init", "domains", "dns", "certs", "secrets", "teams", "switch", "project", "projects", "git",
                "bisect", "integration", "telemetry", "target"}


def publish(name, args):
    line = " ".join([name] + args)
    if name in SEND:
        return ("send", line)
    if name in ("npm", "pnpm", "yarn"):
        positionals, options = parse_options(args, NPM_VALUE)
        if wants_help(options) or truthy_flag(options, "--dry-run", "--no-dry-run"):
            return None
        index, command = subcommand_index(args, NPM_VALUE, NPM_COMMANDS)
        if command == "publish" or (name == "yarn" and command == "npm"
                                    and subcommand_index(args[index + 1:], NPM_VALUE, NPM_COMMANDS)[1] == "publish"):
            return ("publish", line)
        return None
    if name == "cargo":
        positionals, options = parse_options(args, {"--registry", "--token", "--manifest-path", "-p", "--package"})
        if positionals[:1] == ["publish"] and not (has(options, "--dry-run", "-n") or wants_help(options)):
            return ("publish", line)
        return None
    if name in ("twine", "gem", "netlify", "fly", "flyctl", "firebase"):
        positionals, options = parse_options(args, {"-r", "--repository", "--project", "-a", "--app", "--only"})
        wanted = {"twine": "upload", "gem": "push", "netlify": "deploy", "fly": "deploy", "flyctl": "deploy",
                  "firebase": "deploy"}[name]
        if positionals[:1] == [wanted] and not wants_help(options):
            return ("deploy/publish", line)
        return None
    if name == "terraform":
        rest = [arg for arg in args if not arg.startswith("-chdir=")]
        if rest[:1] in (["apply"], ["destroy"]) and "-help" not in rest:
            return ("deploy", line)
        return None
    if name == "docker":
        positionals, options = parse_options(args, DOCKER_VALUE)
        if wants_help(options):
            return None
        if positionals[:1] == ["push"] or positionals[:2] == ["image", "push"]:
            return ("publish", line)
        if positionals[:1] == ["build"] or positionals[:2] in (["buildx", "build"], ["image", "build"],
                                                               ["buildx", "bake"]):
            outputs = " ".join(value or "" for opt, value in options if opt in ("-o", "--output"))
            if truthy_flag(options, "--push", "--no-push") or "type=registry" in outputs or "push=true" in outputs:
                return ("publish", line)
        return None
    if name == "vercel":
        positionals, options = parse_options(args, VERCEL_VALUE)
        if wants_help(options):
            return None
        first = positionals[0] if positionals else None
        second = positionals[1] if len(positionals) > 1 else None
        if first in ("remove", "rm"):
            return ("remote deletion", line)
        if first in ("promote", "rollback") and second == "status":
            return None
        if first == "alias" and second in ("rm", "remove"):
            return ("remote deletion", line)
        if first == "alias" and second not in ("set",):
            return None
        if first is None or first == "deploy" or first not in VERCEL_LOCAL:
            return ("deploy", line)
        return None
    if name == "kubectl":
        positionals, options = parse_options(args, KUBECTL_VALUE)
        if wants_help(options):
            return None
        dry = [value for opt, value in options if opt == "--dry-run"]
        if dry and (dry[-1] is None or dry[-1].lower() in ("client", "server", "true")):
            return None
        index, verb = subcommand_index(args, KUBECTL_VALUE, KUBECTL_COMMANDS)
        after = [arg for arg in args[index + 1:] if not arg.startswith("-")] if index >= 0 else []
        if verb in ("apply", "create", "replace", "patch", "delete") or (verb == "rollout" and after[:1] in (["restart"], ["undo"])):
            return ("deploy", line)
        return None
    if name == "helm":
        positionals, options = parse_options(args, HELM_VALUE)
        if wants_help(options):
            return None
        dry = [value for opt, value in options if opt == "--dry-run"]
        if dry and (dry[-1] is None or dry[-1].lower() in ("client", "server", "true")):
            return None
        _, verb = subcommand_index(args, HELM_VALUE, HELM_COMMANDS)
        if verb in ("install", "upgrade", "uninstall", "delete", "rollback"):
            return ("deploy", line)
        if verb == "push":
            return ("publish", line)
        return None
    return None


def check(command, cwd, declared_default=None):
    """((category, part) or None, where the default branch came from)."""
    ctx = Context(cwd, declared_default)
    try:
        hit = Checker(ctx).line(command, cwd)
    except Unparsable:
        hit = ("unparsable", "the command could not be parsed safely") if KEYWORD.search(command) else None
    return hit, ", ".join(sorted(ctx.sources)) or "not needed"
