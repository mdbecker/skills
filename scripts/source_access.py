"""Git publication snapshots and guarded source acquisition."""

from pathlib import Path
import os
import posixpath
import subprocess
import tempfile

def _git(root, *arguments, input=None, env=None, allowed=(0,)):
    result = subprocess.run(['git', *arguments], cwd=root, input=input,
                            capture_output=True, env=env)
    if result.returncode not in allowed:
        raise ValueError('Git snapshot unavailable or invalid')
    return result.stdout


def repository_root(root):
    root = Path(root).absolute()
    result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=root, capture_output=True)
    if result.returncode == 0:
        return Path(os.fsdecode(result.stdout).strip()).resolve()
    if any((parent / '.git').exists() for parent in [root, *root.parents]):
        raise ValueError('Repository authority is unavailable; do not use fixture fallback')
    return None


class SourceSnapshot:
    def __init__(self, root, kind='index'):
        self.root = Path(root).absolute()
        self.kind = kind
        top = Path(os.fsdecode(_git(self.root, 'rev-parse', '--show-toplevel')).strip())
        if top.resolve() != self.root.resolve():
            raise ValueError('Source root must be the selected repository root')
        if kind == 'HEAD':
            data = _git(self.root, 'ls-tree', '-rz', '--full-tree', 'HEAD')
        elif kind in {'index', 'worktree'}:
            data = _git(self.root, 'ls-files', '--stage', '-z')
        else:
            raise ValueError('Snapshot must be HEAD or index; worktree is a preview only')
        self.entries = {}
        for record in data.split(b'\0'):
            if not record:
                continue
            metadata, path = record.split(b'\t', 1)
            mode, identity, stage = metadata.decode().split()
            if kind == 'HEAD':
                identity = stage
            elif stage != '0':
                raise ValueError('Unmerged index entries prevent source validation')
            self.entries[os.fsdecode(path)] = (mode, identity)
        self.contents = {}
        self._ignored_cache = {}
        self._local_cache = None

    def _local_guard(self, paths):
        if self._local_cache is None:
            with tempfile.TemporaryDirectory(prefix='skills-local-policy-') as temporary:
                target = Path(temporary)
                env = {**os.environ, 'HOME': temporary, 'XDG_CONFIG_HOME': str(target / '.config'),
                       'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}
                for key in list(env):
                    if key.startswith('GIT_') and key not in {'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_NOSYSTEM'}:
                        del env[key]
                _git(target, 'init', '-q', env=env)
                info = Path(os.fsdecode(_git(self.root, 'rev-parse', '--git-path', 'info/exclude')).strip())
                if not info.is_absolute():
                    info = self.root / info
                if info.is_file():
                    (target / '.git/info/exclude').write_bytes(info.read_bytes())
                configured = os.fsdecode(_git(self.root, 'config', '--path', '--get', 'core.excludesFile', allowed=(0, 1))).strip()
                global_path = Path(configured) if configured else Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'git/ignore'
                if not global_path.is_absolute():
                    global_path = self.root / global_path
                if global_path.is_file():
                    copied = target / 'global-ignore'
                    copied.write_bytes(global_path.read_bytes())
                    _git(target, 'config', 'core.excludesFile', str(copied), env=env)
                data = _git(target, 'check-ignore', '--no-index', '-z', '--stdin',
                            input=b'\0'.join(os.fsencode(path) for path in self.entries) + b'\0',
                            env=env, allowed=(0, 1))
                self._local_cache = {os.fsdecode(path) for path in data.split(b'\0') if path}
        if set(paths) & self._local_cache:
            raise ValueError('Local privacy access stop')

    def physical(self, path):
        target = self.root / path
        if not target.resolve().is_relative_to(self.root.resolve()):
            raise ValueError('Physical source escapes repository')
        for parent in [target, *target.parents]:
            if parent == self.root.parent:
                break
            if parent.is_symlink():
                raise ValueError('Source has a symlink component')
        if not target.is_file():
            raise ValueError('Physical source must be an ordinary file')
        return target

    def _acquire(self, path):
        self._local_guard([path])
        if self.kind == 'worktree':
            return self.physical(path).read_bytes()
        return _git(self.root, 'cat-file', 'blob', self.entries[path][1])

    def read(self, path):
        if path not in self.contents:
            self.eligible(path)
            self.contents[path] = self._acquire(path)
        return self.contents[path]

    def fresh(self, path):
        self.eligible(path)
        return self._acquire(path)

    def ignored(self, paths):
        requested = set(paths)
        unknown = (requested | (set(self.entries) if not self._ignored_cache else set())) - self._ignored_cache.keys()
        if unknown:
            with tempfile.TemporaryDirectory(prefix='skills-ignore-') as temporary:
                root = Path(temporary)
                env = {**os.environ, 'HOME': temporary, 'GIT_CONFIG_NOSYSTEM': '1',
                       'GIT_CONFIG_GLOBAL': os.devnull, 'XDG_CONFIG_HOME': str(root / '.config')}
                for key in list(env):
                    if key.startswith('GIT_') and key not in {'GIT_CONFIG_NOSYSTEM', 'GIT_CONFIG_GLOBAL'}:
                        del env[key]
                _git(root, 'init', '-q', env=env)
                for path in sorted(self.entries, key=lambda value: (value.count('/'), value)):
                    mode, identity = self.entries[path]
                    if Path(path).name != '.gitignore':
                        continue
                    if mode not in {'100644', '100755'}:
                        raise ValueError('Ignore rules must be ordinary snapshot files')
                    parent = posixpath.dirname(path)
                    if parent and _git(root, 'check-ignore', '--no-index', '-z', '--stdin',
                                       input=os.fsencode(parent + '/') + b'\0', env=env, allowed=(0, 1)):
                        continue
                    if _git(root, 'check-ignore', '--no-index', '-z', '--stdin',
                            input=os.fsencode(path) + b'\0', env=env, allowed=(0, 1)):
                        raise ValueError('Excluded policy input; stop before reading')
                    target = root / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(self._acquire(path))
                excluded = set(os.fsdecode(path) for path in _git(
                    root, 'check-ignore', '--no-index', '-z', '--stdin',
                    input=b'\0'.join(os.fsencode(path) for path in sorted(unknown)) + b'\0',
                    env=env, allowed=(0, 1)).split(b'\0') if path)
            self._ignored_cache.update({path: path in excluded for path in unknown})
        return {path for path in requested if self._ignored_cache[path]}

    def eligible(self, path):
        if path in self.ignored([path]):
            raise ValueError('Ignore-policy exclusion')
        if path not in self.entries:
            raise ValueError('Missing or untracked file')
        if self.entries[path][0] not in {'100644', '100755'}:
            raise ValueError('Source target must be an ordinary file')
        parent = posixpath.dirname(path)
        while parent:
            if parent in self.entries:
                raise ValueError('Source target has a non-directory ancestor')
            parent = posixpath.dirname(parent)


def validate_inputs(root, paths):
    snapshot = SourceSnapshot(root, 'worktree')
    excluded = snapshot.ignored(snapshot.entries)
    if excluded:
        raise ValueError('Tracked publication files conflict with repository ignore rules')
    for path in paths:
        snapshot.eligible(path)
        snapshot.physical(path)
    snapshot._local_guard(paths)
