#!/usr/bin/env python3
"""Configure and build a pinned Microsoft WSL2 homelab kernel."""

from __future__ import annotations

import argparse
import copy
import os
import pwd
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from catalog_lib import load_manifest, sha256_file, write_manifest
from validate_config import ConfigError, parse_config, validate_config


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAG = "linux-msft-wsl-6.18.35.2"


class BuildError(RuntimeError):
    """The build cannot continue without violating its safety or identity contract."""


@dataclass(frozen=True)
class Baseline:
    record: Path
    manifest: dict[str, Any]
    tag: str
    commit: str
    fragment: Path
    normalized: Path


def command_text(command: Sequence[object]) -> str:
    return shlex.join(str(part) for part in command)


def run(
    command: Sequence[object], *, cwd: Path | None = None, capture: bool = False
) -> str:
    rendered = [str(part) for part in command]
    print(f"+ {command_text(rendered)}", flush=True)
    try:
        result = subprocess.run(
            rendered,
            cwd=cwd,
            check=True,
            capture_output=capture,
            text=True,
        )
    except FileNotFoundError as exc:
        raise BuildError(f"command not found: {rendered[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() if capture and exc.stderr else f"exit status {exc.returncode}"
        raise BuildError(f"command failed ({detail}): {command_text(rendered)}") from exc
    return result.stdout.strip() if capture else ""


def git(source: Path, *arguments: str) -> str:
    return run(["git", "-C", source, *arguments], capture=True)


def resolve_tag(source: Path, tag: str) -> str | None:
    command = ["git", "-C", str(source), "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def ensure_clean_shallow(source: Path, expected_commit: str) -> None:
    if not (source / ".git").exists():
        raise BuildError(f"source is not a Git clone: {source}")
    if git(source, "rev-parse", "--is-shallow-repository") != "true":
        raise BuildError(f"source clone is not shallow: {source}")
    dirty = git(source, "status", "--porcelain=v1", "--untracked-files=all")
    if dirty:
        raise BuildError(
            "source clone is not pristine; refusing to clean or overwrite these paths:\n" + dirty
        )
    head = git(source, "rev-parse", "HEAD")
    if head != expected_commit:
        raise BuildError(f"source HEAD {head} does not equal pinned commit {expected_commit}")


def prepare_source(source: Path, baseline: Baseline, fetch_tag: bool) -> None:
    source = source.resolve()
    if not (source / ".git").exists():
        raise BuildError(f"source is not a Git clone: {source}")
    if git(source, "rev-parse", "--is-shallow-repository") != "true":
        raise BuildError(f"source clone is not shallow: {source}")
    dirty = git(source, "status", "--porcelain=v1", "--untracked-files=all")
    if dirty:
        raise BuildError(
            "source clone is not pristine; refusing to clean or overwrite these paths:\n" + dirty
        )

    tag_commit = resolve_tag(source, baseline.tag)
    if tag_commit is None:
        if not fetch_tag:
            raise BuildError(
                f"source lacks tag {baseline.tag}; rerun with --fetch-tag to fetch only that tag "
                "at depth one and check it out"
            )
        run(
            [
                "git",
                "-C",
                source,
                "fetch",
                "--depth=1",
                "--no-tags",
                "origin",
                f"refs/tags/{baseline.tag}:refs/tags/{baseline.tag}",
            ]
        )
        tag_commit = resolve_tag(source, baseline.tag)

    if tag_commit != baseline.commit:
        raise BuildError(
            f"tag {baseline.tag} resolves to {tag_commit or 'nothing'}, not {baseline.commit}"
        )

    head = git(source, "rev-parse", "HEAD")
    if head != baseline.commit:
        if not fetch_tag:
            raise BuildError(
                f"source HEAD {head} is not the pinned commit; rerun with --fetch-tag to perform "
                "the explicit detached checkout"
            )
        run(["git", "-C", source, "checkout", "--detach", baseline.tag])

    ensure_clean_shallow(source, baseline.commit)
    print(f"Source verified: {baseline.tag} at {baseline.commit} (shallow and pristine).")


def load_baseline(record: Path) -> Baseline:
    record = record.resolve()
    manifest = load_manifest(record / "manifest.yaml")
    try:
        tag = manifest["upstream"]["tag"]
        commit = manifest["upstream"]["commit"]
        fragment = record / manifest["config"]["fragment"]["path"]
        normalized = record / manifest["config"]["normalized"]["path"]
    except (KeyError, TypeError) as exc:
        raise BuildError(f"baseline manifest is missing a required field: {exc}") from exc
    if record.name != tag:
        raise BuildError(f"record directory {record.name} does not match manifest tag {tag}")
    if not fragment.is_file():
        raise BuildError(f"required config fragment does not exist: {fragment}")
    return Baseline(record, manifest, tag, commit, fragment, normalized)


def require_tools(names: Sequence[str]) -> None:
    missing = sorted(name for name in names if shutil.which(name) is None)
    if missing:
        raise BuildError(
            "missing required build tool(s): "
            + ", ".join(missing)
            + "; install the prerequisites documented in docs/build-and-deploy.md"
        )


def configure(source: Path, build: Path, baseline: Baseline) -> tuple[Path, str]:
    require_tools(("make", "gcc", "bison", "flex"))
    build.mkdir(parents=True, exist_ok=True)
    base_config = source / "arch" / "x86" / "configs" / "config-wsl"
    merge_script = source / "scripts" / "kconfig" / "merge_config.sh"
    if not base_config.is_file() or not merge_script.is_file():
        raise BuildError("pinned source is missing config-wsl or merge_config.sh")

    build_base = build / "config-wsl.base"
    shutil.copy2(base_config, build_base)
    run([merge_script, "-m", "-O", build, build_base, baseline.fragment], cwd=ROOT)
    run(["make", "-C", source, f"O={build}", "ARCH=x86_64", "olddefconfig"])

    generated = build / ".config"
    try:
        mismatches = validate_config(baseline.fragment, generated)
    except ConfigError as exc:
        raise BuildError(str(exc)) from exc
    if mismatches:
        detail = "\n".join(f"  - {mismatch.render()}" for mismatch in mismatches)
        raise BuildError(f"generated config violates the homelab contract:\n{detail}")

    normalized = build / "config-wsl-homelab"
    shutil.copy2(generated, normalized)
    checksum = sha256_file(normalized)
    print(f"Config validation passed; normalized SHA-256: {checksum}")
    ensure_clean_shallow(source, baseline.commit)
    return normalized, checksum


def compiler_identity(config: Path) -> str:
    value = parse_config(config).get("CONFIG_CC_VERSION_TEXT")
    if value:
        return value[1:-1] if value.startswith('"') and value.endswith('"') else value
    compiler = shlex.split(os.environ.get("CC", "gcc"))[0]
    return run([compiler, "--version"], capture=True).splitlines()[0]


def verify_stripped_modules(module_release: Path) -> int:
    """Require installed runtime modules and prove none retain .debug* ELF sections."""
    require_tools(("readelf",))
    modules = sorted(module_release.rglob("*.ko"))
    if not modules:
        raise BuildError(f"installed module tree contains no .ko files: {module_release}")
    offenders: list[str] = []
    for module in modules:
        try:
            sections = subprocess.run(
                ["readelf", "--section-headers", "--wide", module],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        except subprocess.CalledProcessError as exc:
            raise BuildError(f"could not inspect ELF sections in {module}: {exc}") from exc
        if re.search(r"\s\.debug(?:_|\b)", sections):
            offenders.append(str(module.relative_to(module_release)))
            if len(offenders) == 5:
                break
    if offenders:
        raise BuildError(
            "installed runtime modules retain .debug* sections after INSTALL_MOD_STRIP=1: "
            + ", ".join(offenders)
        )
    return len(modules)


def render_build_report(
    baseline: Baseline,
    source: Path,
    build: Path,
    release: str,
    compiler: str,
    timestamp: str,
    config_checksum: str,
    kernel_name: str,
    kernel_checksum: str,
    kernel_size: int,
    modules_name: str,
    modules_checksum: str,
    modules_size: int,
    stripped_modules: int,
    jobs: int,
    privilege_option: str,
) -> str:
    return f"""# Build validation: `{baseline.tag}`

Result: PASS

| Check | Expected | Actual | Result |
| --- | --- | --- | --- |
| Source tag | `{baseline.tag}` | `{baseline.tag}` | PASS |
| Source commit | `{baseline.commit}` | `{baseline.commit}` | PASS |
| Shallow/pristine clone | `true` / clean | `true` / clean before and after build | PASS |
| Config merge | no conflicts | completed out of tree | PASS |
| `olddefconfig` | success | success | PASS |
| Required symbols | exact values | all values match | PASS |
| Kernel build | success | `{kernel_name}` | PASS |
| Modules build/install | success | `modules/lib/modules/{release}` | PASS |
| Runtime module stripping | no staged `.debug*` sections | `{stripped_modules}` `.ko` files checked | PASS |
| Kernel release | matches module tree | `{release}` | PASS |
| Kernel checksum | matches manifest | `{kernel_checksum}` | PASS |
| Kernel size | matches manifest | `{kernel_size}` bytes | PASS |
| Modules VHDX checksum | matches manifest | `{modules_checksum}` | PASS |
| Modules VHDX size | matches manifest | `{modules_size}` bytes | PASS |

- Compiler: `{compiler}`
- UTC build timestamp: `{timestamp}`
- Normalized config SHA-256: `{config_checksum}`
- Source: `{source}`
- Ignored build directory: `{build}`
- Entry point: `python3 scripts/build_kernel.py build --source {source} --jobs {jobs} {privilege_option} --record-evidence`
- Kernel artifact: `{kernel_name}`
- Modules artifact: `{modules_name}`

The entry point copied Microsoft's `config-wsl`, merged the versioned homelab fragment, ran
`olddefconfig`, strictly validated every required symbol, built the kernel and modules together,
installed stripped runtime modules under `lib/modules/{release}`, verified that their ELF files
contain no `.debug*` sections, and passed that exact staged release to Microsoft's
`gen_modules_vhdx.sh`. The source clone remained shallow and pristine throughout.
"""


def built_manifest(
    baseline: Baseline,
    release: str,
    compiler: str,
    timestamp: str,
    config_checksum: str,
    kernel_name: str,
    kernel_checksum: str,
    kernel_size: int,
    modules_name: str,
    modules_checksum: str,
    modules_size: int,
    build_report_passed: bool,
) -> dict[str, Any]:
    manifest = copy.deepcopy(baseline.manifest)
    if manifest["status"] in ("planned", "failed"):
        manifest["previous_status"] = manifest["status"]
        manifest["status"] = "built"
    elif manifest["status"] == "validated":
        publication = manifest["publication"]
        if any(publication[key] is not None for key in ("release_tag", "release_url", "published_at")):
            raise BuildError("cannot replace artifacts for a published record")
        manifest["previous_status"] = "validated"
        manifest["status"] = "built"
    elif manifest["status"] != "built":
        raise BuildError(f"cannot record a build from lifecycle status {manifest['status']}")
    manifest["schema_version"] = 2
    manifest["failure"] = {"stage": None, "reason": None}
    manifest["kernel_release"] = release
    manifest["config"]["normalized"]["sha256"] = config_checksum
    manifest["build"].update(compiler=compiler, timestamp=timestamp)
    manifest["artifacts"]["kernel"].update(
        name=kernel_name, sha256=kernel_checksum, size_bytes=kernel_size, kernel_release=release
    )
    manifest["artifacts"]["modules_vhdx"].update(
        name=modules_name, sha256=modules_checksum, size_bytes=modules_size, kernel_release=release
    )
    manifest["validation"]["runtime"]["status"] = "pending"
    manifest["validation"]["validated_at"] = None
    for capability in manifest["capabilities"]:
        manifest["capabilities"][capability] = None
    if build_report_passed:
        manifest["validation"]["build"]["status"] = "pass"
    return manifest


def record_evidence(
    baseline: Baseline,
    normalized: Path,
    manifest: dict[str, Any],
    report: str,
) -> None:
    shutil.copy2(normalized, baseline.normalized)
    (baseline.record / manifest["validation"]["build"]["report"]).write_text(
        report, encoding="utf-8"
    )
    if manifest["validation"]["runtime"]["status"] == "pending":
        runtime_report = baseline.record / manifest["validation"]["runtime"]["report"]
        runtime_report.write_text(
            f"""# Runtime validation: `{baseline.tag}`

Result: PENDING

The artifact pair was replaced by a new build. Prior runtime acceptance is intentionally invalid;
deploy the kernel and modules VHDX together and rerun every check in `docs/validation.md`.
""",
            encoding="utf-8",
        )
    write_manifest(baseline.record / "manifest.yaml", manifest)
    run([sys.executable, ROOT / "scripts" / "catalog.py", "matrix"])
    run([sys.executable, ROOT / "scripts" / "catalog.py", "validate"])
    print(f"Retained normalized config, manifest, and PASS build evidence in {baseline.record}.")


def build_kernel(
    source: Path,
    build: Path,
    baseline: Baseline,
    jobs: int,
    privilege_prefix: Sequence[object],
    privilege_option: str,
    retain: bool,
) -> None:
    require_tools(
        (
            "make",
            "gcc",
            "bc",
            "bison",
            "flex",
            "openssl",
            "pahole",
            "cpio",
            "rsync",
            "qemu-img",
            "losetup",
            "mkfs.ext4",
            "mount",
            "umount",
        )
    )
    if os.geteuid() != 0 and not privilege_prefix:
        raise BuildError(
            "modules VHDX creation requires root for loop-device mounting; explicitly select "
            "--sudo-vhdx or --wsl-root-vhdx for Microsoft's packaging script"
        )

    kernel_name = baseline.tag
    modules_name = f"modules-{baseline.tag}.vhdx"
    kernel_output = build / kernel_name
    modules_output = build / modules_name
    modules_stage = build / "modules"
    for path in (kernel_output, modules_output, modules_stage):
        if path.exists():
            raise BuildError(f"generated output already exists: {path}; run the clean action first")

    normalized, config_checksum = configure(source, build, baseline)
    run(
        [
            "make",
            "-C",
            source,
            f"O={build}",
            "ARCH=x86_64",
            "--silent",
            f"-j{jobs}",
            "bzImage",
            "modules",
        ]
    )
    release = run(
        ["make", "-s", "-C", source, f"O={build}", "ARCH=x86_64", "kernelrelease"],
        capture=True,
    )
    run(
        [
            "make",
            "-C",
            source,
            f"O={build}",
            "ARCH=x86_64",
            "modules_install",
            f"INSTALL_MOD_PATH={modules_stage}",
            "INSTALL_MOD_STRIP=1",
        ]
    )
    module_release = modules_stage / "lib" / "modules" / release
    if not module_release.is_dir():
        raise BuildError(f"installed module tree does not match kernel release {release}")
    stripped_modules = verify_stripped_modules(module_release)

    image = build / "arch" / "x86" / "boot" / "bzImage"
    if not image.is_file():
        raise BuildError(f"kernel build did not produce {image}")
    shutil.copy2(image, kernel_output)

    package_script = source / "Microsoft" / "scripts" / "gen_modules_vhdx.sh"
    package_command: list[object] = [
        *privilege_prefix,
        package_script,
        modules_stage,
        release,
        modules_output,
    ]
    run(package_command)
    if not modules_output.is_file():
        raise BuildError(f"module packaging did not produce {modules_output}")

    ensure_clean_shallow(source, baseline.commit)
    compiler = compiler_identity(build / ".config")
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    kernel_checksum = sha256_file(kernel_output)
    modules_checksum = sha256_file(modules_output)
    kernel_size = kernel_output.stat().st_size
    modules_size = modules_output.stat().st_size
    report = render_build_report(
        baseline,
        source,
        build,
        release,
        compiler,
        timestamp,
        config_checksum,
        kernel_name,
        kernel_checksum,
        kernel_size,
        modules_name,
        modules_checksum,
        modules_size,
        stripped_modules,
        jobs,
        privilege_option,
    )
    manifest = built_manifest(
        baseline,
        release,
        compiler,
        timestamp,
        config_checksum,
        kernel_name,
        kernel_checksum,
        kernel_size,
        modules_name,
        modules_checksum,
        modules_size,
        build_report_passed=retain,
    )
    write_manifest(build / "manifest.yaml", manifest)
    (build / "SHA256SUMS").write_text(
        "".join(
            f"{checksum}  {name}\n"
            for checksum, name in (
                (config_checksum, normalized.name),
                (kernel_checksum, kernel_name),
                (modules_checksum, modules_name),
            )
        ),
        encoding="utf-8",
    )
    if retain:
        record_evidence(baseline, normalized, manifest, report)
    print(f"Build complete for {release}; manifest: {build / 'manifest.yaml'}")


def safe_build_dir(path: Path, tag: str) -> Path:
    build = path.resolve()
    allowed = (ROOT / "build").resolve()
    if build != allowed / tag and allowed not in build.parents:
        raise BuildError(f"build directory must stay beneath ignored path {allowed}")
    return build


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("configure", "build", "clean"))
    parser.add_argument("--record", type=Path, default=ROOT / "kernels" / DEFAULT_TAG)
    parser.add_argument("--source", type=Path, default=ROOT.parent / "WSL2-Linux-Kernel")
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    parser.add_argument(
        "--fetch-tag",
        action="store_true",
        help="explicitly fetch only the pinned tag at depth one and check it out if needed",
    )
    privilege = parser.add_mutually_exclusive_group()
    privilege.add_argument(
        "--sudo-vhdx",
        action="store_true",
        help="authorize sudo for Microsoft's loop-device VHDX packaging script",
    )
    privilege.add_argument(
        "--wsl-root-vhdx",
        metavar="DISTRO",
        help="authorize wsl.exe to run only the VHDX packaging script as root in DISTRO",
    )
    parser.add_argument(
        "--record-evidence",
        action="store_true",
        help="after a successful full build, update the tracked normalized config and build evidence",
    )
    args = parser.parse_args(argv)

    try:
        baseline = load_baseline(args.record)
        build = safe_build_dir(args.build_dir or ROOT / "build" / baseline.tag, baseline.tag)
        if args.jobs < 1:
            raise BuildError("--jobs must be at least 1")
        if args.record_evidence and args.action != "build":
            raise BuildError("--record-evidence is valid only with the build action")
        if args.action == "clean":
            if build.exists():
                shutil.rmtree(build)
                print(f"Removed generated build directory {build}.")
            else:
                print(f"Build directory is already absent: {build}")
            return 0

        source = args.source.resolve()
        prepare_source(source, baseline, args.fetch_tag)
        if args.action == "configure":
            normalized, checksum = configure(source, build, baseline)
            print(f"Configured {normalized} ({checksum}).")
        else:
            privilege_prefix: list[object] = []
            privilege_option = ""
            if os.geteuid() != 0 and args.sudo_vhdx:
                privilege_prefix = ["sudo"]
                privilege_option = "--sudo-vhdx"
            elif os.geteuid() != 0 and args.wsl_root_vhdx:
                require_tools(("wsl.exe",))
                username = pwd.getpwuid(os.getuid()).pw_name
                privilege_prefix = [
                    "wsl.exe",
                    "-d",
                    args.wsl_root_vhdx,
                    "-u",
                    "root",
                    "--",
                    "env",
                    f"SUDO_USER={username}",
                ]
                privilege_option = f"--wsl-root-vhdx {shlex.quote(args.wsl_root_vhdx)}"
            build_kernel(
                source,
                build,
                baseline,
                args.jobs,
                privilege_prefix,
                privilege_option,
                args.record_evidence,
            )
        return 0
    except (BuildError, ConfigError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
