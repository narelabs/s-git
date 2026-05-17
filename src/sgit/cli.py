"""CLI entry point for s-git: semantic version control."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from sgit.ast_parser import parse_file
from sgit.commit_gen import generate_commit_message
from sgit.diff_engine import compute_delta, format_deltas
from sgit.merge_engine import format_merge_result, merge_snapshots
from sgit.models import FileSnapshot, SemanticDelta
from sgit.storage import Repository, init_repo


@click.group()
@click.version_option(package_name="s-git")
def main() -> None:
    """s-git: Semantic Git — version control that tracks meaning, not text."""


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def init(path: str) -> None:
    """Initialize a new s-git repository."""
    try:
        root = init_repo(path)
        click.echo(f"Initialized empty s-git repository in {root / '.sgit'}")
    except FileExistsError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@main.command()
@click.argument("files", nargs=-1, type=click.Path())
def add(files: tuple[str, ...]) -> None:
    """Stage files for the next commit."""
    try:
        repo = Repository()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not files:
        click.echo("Nothing specified to add. Use 'sgit add <file>' or 'sgit add .'")
        return

    added_count = 0
    for file_arg in files:
        if file_arg == ".":
            for py_file in repo.list_tracked_files():
                repo.add_file(py_file)
                added_count += 1
        else:
            if Path(file_arg).is_absolute():
                rel = str(Path(file_arg).relative_to(repo.root))
            else:
                rel = file_arg
            if Path(rel).suffix != ".py":
                click.echo(f"Skipping non-Python file: {rel}")
                continue
            try:
                repo.add_file(rel)
                added_count += 1
            except FileNotFoundError:
                click.echo(f"File not found: {rel}", err=True)

    click.echo(f"Staged {added_count} file(s)")


@main.command()
@click.option("-m", "--message", default=None, help="Override auto-generated commit message.")
def commit(message: str | None) -> None:
    """Create a semantic commit (auto-generates message from AST diff)."""
    try:
        repo = Repository()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    index = repo.read_index()
    if not index:
        click.echo("Nothing to commit. Use 'sgit add' to stage files first.")
        return

    current_snapshots: dict[str, FileSnapshot] = {}
    for rel_path in index:
        full_path = repo.root / rel_path
        if full_path.exists():
            current_snapshots[rel_path] = parse_file(str(full_path))

    if message is None:
        deltas = _compute_deltas_vs_head(repo, current_snapshots)
        message = generate_commit_message(deltas)

    commit_obj = repo.create_commit(message, current_snapshots)

    title = message.split("\n")[0]
    click.echo(f"[{repo.current_branch} {commit_obj.commit_id[:8]}] {title}")
    click.echo(f"  {len(current_snapshots)} file(s) committed")


@main.command()
@click.argument("ref", default=None, required=False)
def diff(ref: str | None) -> None:
    """Show semantic diff (working tree vs HEAD, or between commits)."""
    try:
        repo = Repository()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if ref is not None:
        parts = ref.split("..")
        if len(parts) == 2:
            _diff_commits(repo, parts[0], parts[1])
        else:
            _diff_ref_vs_working(repo, ref)
    else:
        _diff_head_vs_working(repo)


def _diff_head_vs_working(repo: Repository) -> None:
    """Diff working directory against HEAD."""
    py_files = repo.list_tracked_files()
    if not py_files:
        click.echo("No Python files found.")
        return

    current_snapshots: dict[str, FileSnapshot] = {}
    for f in py_files:
        full = repo.root / f
        if full.exists():
            current_snapshots[f] = parse_file(str(full))

    deltas = _compute_deltas_vs_head(repo, current_snapshots)
    active_deltas = [d for d in deltas if d.has_changes]

    if not active_deltas:
        click.echo("No semantic changes detected.")
    else:
        click.echo(format_deltas(active_deltas))


def _diff_ref_vs_working(repo: Repository, ref: str) -> None:
    """Diff a specific commit against working directory."""
    commit_obj = repo.get_commit(ref)
    if commit_obj is None:
        click.echo(f"Commit not found: {ref}", err=True)
        sys.exit(1)

    old_snapshots = repo.get_commit_snapshots(commit_obj)

    py_files = repo.list_tracked_files()
    new_snapshots: dict[str, FileSnapshot] = {}
    for f in py_files:
        full = repo.root / f
        if full.exists():
            new_snapshots[f] = parse_file(str(full))

    deltas = _compute_deltas_between(old_snapshots, new_snapshots)
    active = [d for d in deltas if d.has_changes]

    if not active:
        click.echo("No semantic changes detected.")
    else:
        click.echo(format_deltas(active))


def _diff_commits(repo: Repository, ref_a: str, ref_b: str) -> None:
    """Diff between two commits."""
    commit_a = repo.get_commit(ref_a)
    commit_b = repo.get_commit(ref_b)
    if commit_a is None:
        click.echo(f"Commit not found: {ref_a}", err=True)
        sys.exit(1)
    if commit_b is None:
        click.echo(f"Commit not found: {ref_b}", err=True)
        sys.exit(1)

    old_snaps = repo.get_commit_snapshots(commit_a)
    new_snaps = repo.get_commit_snapshots(commit_b)

    deltas = _compute_deltas_between(old_snaps, new_snaps)
    active = [d for d in deltas if d.has_changes]

    if not active:
        click.echo("No semantic changes detected.")
    else:
        click.echo(format_deltas(active))


@main.command()
@click.option("-n", "--count", default=10, help="Number of commits to show.")
def log(count: int) -> None:
    """Show commit history with semantic messages."""
    try:
        repo = Repository()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    commits = repo.log(max_count=count)
    if not commits:
        click.echo("No commits yet.")
        return

    for c in commits:
        title = c.message.split("\n")[0]
        files = len(c.snapshots)
        click.echo(f"commit {c.commit_id} ({c.branch})")
        click.echo(f"  Date:  {c.timestamp}")
        click.echo(f"  Files: {files}")
        click.echo(f"  {title}")
        click.echo()


@main.command()
def status() -> None:
    """Show repository status."""
    try:
        repo = Repository()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    branch = repo.current_branch
    head = repo.head_commit_id()
    click.echo(f"On branch {branch}")
    if head:
        click.echo(f"HEAD: {head[:8]}")
    else:
        click.echo("No commits yet")

    index = repo.read_index()
    if index:
        click.echo(f"\nStaged files ({len(index)}):")
        for path in sorted(index):
            click.echo(f"  {path}")

    py_files = repo.list_tracked_files()
    if head and py_files:
        head_commit = repo.get_commit(head)
        if head_commit:
            committed_files = set(head_commit.snapshots.keys())
            untracked = [f for f in py_files if f not in committed_files and f not in index]
            if untracked:
                click.echo(f"\nUntracked Python files ({len(untracked)}):")
                for f in untracked:
                    click.echo(f"  {f}")
    elif py_files and not index:
        click.echo(f"\nUntracked Python files ({len(py_files)}):")
        for f in py_files:
            click.echo(f"  {f}")


@main.command()
@click.argument("branch_name")
def branch(branch_name: str) -> None:
    """Create a new branch."""
    try:
        repo = Repository()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    try:
        repo.create_branch(branch_name)
        click.echo(f"Created branch '{branch_name}'")
    except FileExistsError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@main.command()
@click.argument("branch_name")
def checkout(branch_name: str) -> None:
    """Switch to a different branch."""
    try:
        repo = Repository()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    try:
        repo.switch_branch(branch_name)
        click.echo(f"Switched to branch '{branch_name}'")
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@main.command()
@click.argument("branch_name")
def merge(branch_name: str) -> None:
    """Semantically merge a branch into the current branch."""
    try:
        repo = Repository()
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    their_ref = repo.sgit / "refs" / "heads" / branch_name
    if not their_ref.exists():
        click.echo(f"Branch '{branch_name}' not found.", err=True)
        sys.exit(1)

    their_commit_id = their_ref.read_text().strip()
    their_commit = repo.get_commit(their_commit_id)
    our_commit_id = repo.head_commit_id()

    if not their_commit:
        click.echo(f"Could not load commit for branch '{branch_name}'.", err=True)
        sys.exit(1)

    if not our_commit_id:
        click.echo("Current branch has no commits.", err=True)
        sys.exit(1)

    our_commit = repo.get_commit(our_commit_id)
    if not our_commit:
        click.echo("Could not load HEAD commit.", err=True)
        sys.exit(1)

    base_commit_id = _find_common_ancestor(repo, our_commit_id, their_commit_id)

    our_snaps = repo.get_commit_snapshots(our_commit)
    their_snaps = repo.get_commit_snapshots(their_commit)

    if base_commit_id:
        base_commit = repo.get_commit(base_commit_id)
        base_snaps = repo.get_commit_snapshots(base_commit) if base_commit else {}
    else:
        base_snaps = {}

    all_files = set(our_snaps) | set(their_snaps)
    total_conflicts = 0
    total_resolved = 0
    merged_snapshots: dict[str, FileSnapshot] = {}

    for fpath in sorted(all_files):
        base_snap = base_snaps.get(fpath, FileSnapshot(path=fpath))
        our_snap = our_snaps.get(fpath, FileSnapshot(path=fpath))
        their_snap = their_snaps.get(fpath, FileSnapshot(path=fpath))

        result = merge_snapshots(base_snap, our_snap, their_snap)
        click.echo(format_merge_result(result))
        click.echo()

        total_conflicts += len(result.conflicts)
        total_resolved += len(result.auto_resolved)
        merged_snapshots[fpath] = our_snap

    if total_conflicts == 0:
        merge_msg = f"Merge branch '{branch_name}' into {repo.current_branch}"
        if total_resolved:
            merge_msg += f"\n\nAuto-resolved {total_resolved} change(s) semantically."
        repo.create_commit(merge_msg, merged_snapshots)
        click.echo(f"Merge complete! {total_resolved} change(s) auto-resolved, 0 conflicts.")
    else:
        click.echo(
            f"\nMerge has {total_conflicts} conflict(s) and "
            f"{total_resolved} auto-resolved change(s)."
        )
        click.echo("Resolve conflicts manually and run 'sgit commit'.")


def _find_common_ancestor(repo: Repository, commit_a: str, commit_b: str) -> str | None:
    """Find common ancestor commit (simple linear walk)."""
    ancestors_a: set[str] = set()
    current = commit_a
    while current:
        ancestors_a.add(current)
        c = repo.get_commit(current)
        current = c.parent_id if c else None

    current = commit_b
    while current:
        if current in ancestors_a:
            return current
        c = repo.get_commit(current)
        current = c.parent_id if c else None

    return None


def _compute_deltas_vs_head(
    repo: Repository, current_snapshots: dict[str, FileSnapshot]
) -> list[SemanticDelta]:
    """Compute semantic deltas between HEAD and current snapshots."""
    head_id = repo.head_commit_id()
    if head_id is None:
        deltas: list[SemanticDelta] = []
        for path, snap in current_snapshots.items():
            delta = compute_delta(FileSnapshot(path=path), snap)
            deltas.append(delta)
        return deltas

    head_commit = repo.get_commit(head_id)
    if head_commit is None:
        return []

    old_snaps = repo.get_commit_snapshots(head_commit)
    return _compute_deltas_between(old_snaps, current_snapshots)


def _compute_deltas_between(
    old_snaps: dict[str, FileSnapshot],
    new_snaps: dict[str, FileSnapshot],
) -> list[SemanticDelta]:
    """Compute deltas between two sets of snapshots."""
    deltas: list[SemanticDelta] = []
    all_files = set(old_snaps) | set(new_snaps)

    for fpath in sorted(all_files):
        old = old_snaps.get(fpath, FileSnapshot(path=fpath))
        new = new_snaps.get(fpath, FileSnapshot(path=fpath))
        deltas.append(compute_delta(old, new))

    return deltas
