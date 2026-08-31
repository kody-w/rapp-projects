from __future__ import annotations

import json
import shutil
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import rapp_projects.core as core_module
from rapp_projects.core import Actor, ProjectError, ProjectStore


def actor(name: str) -> Actor:
    return Actor(
        id=name,
        runtime=name,
        session_id="session",
        capabilities=("files",),
    )


def make_project(root: Path) -> ProjectStore:
    store = ProjectStore(root)
    store.open(
        "portable",
        title="Portable",
        goal="Move between runtimes",
        owner="example",
        origin="test",
    )
    store.punchin(
        "portable",
        actor("copilot-cli"),
        location="/workspace",
        intent="build",
        role="builder",
        lease_seconds=60,
    )
    return store


def test_project_egg_round_trip(tmp_path: Path) -> None:
    source = make_project(tmp_path / "source")
    egg = source.export_egg("portable")
    target = ProjectStore(tmp_path / "target")
    imported = target.import_egg(egg)
    assert imported == "portable"
    assert target.frames("portable") == source.frames("portable")
    with zipfile.ZipFile(egg) as archive:
        assert "manifest.json" in archive.namelist()
        assert "frames/" in "\n".join(archive.namelist())


def test_import_refuses_legacy_uri_receipt_before_project_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = make_project(tmp_path / "source")
    original = core_module._is_uri_receipt
    monkeypatch.setattr(core_module, "_is_uri_receipt", lambda value: False)
    source.punchout(
        "portable",
        actor("copilot-cli"),
        outcome="done",
        receipts=["https://example.com/proof.json"],
        summary="Legacy live URL receipt.",
    )
    egg = source.export_egg("portable")
    monkeypatch.setattr(core_module, "_is_uri_receipt", original)
    imported = ProjectStore(tmp_path / "imported")

    with pytest.raises(
        ProjectError,
        match="project egg contains a URI receipt",
    ):
        imported.import_egg(egg)

    assert not imported.project_path("portable").exists()


def test_tampered_egg_is_refused(tmp_path: Path) -> None:
    source = make_project(tmp_path / "source")
    egg = source.export_egg("portable")
    bad = tmp_path / "bad.egg"
    with zipfile.ZipFile(egg) as read, zipfile.ZipFile(bad, "w") as write:
        for name in read.namelist():
            data = read.read(name)
            if name.endswith("rappid.json"):
                data += b" "
            write.writestr(name, data)
    with pytest.raises(ProjectError):
        ProjectStore(tmp_path / "target").import_egg(bad)


def test_manifest_identity_mismatch_is_refused(tmp_path: Path) -> None:
    source = make_project(tmp_path / "source")
    egg = source.export_egg("portable")
    bad = tmp_path / "identity.egg"
    with zipfile.ZipFile(egg) as read, zipfile.ZipFile(bad, "w") as write:
        for name in read.namelist():
            data = read.read(name)
            if name == "manifest.json":
                manifest = json.loads(data)
                manifest["payload"]["project"] = "renamed"
                manifest["payload"]["head_frame_hash"] = "0" * 64
                data = json.dumps(manifest).encode()
            write.writestr(name, data)
    with pytest.raises(ProjectError):
        ProjectStore(tmp_path / "target").import_egg(bad)


def test_divergent_import_is_refused(tmp_path: Path) -> None:
    left = make_project(tmp_path / "left")
    right = ProjectStore(tmp_path / "right")
    right.import_egg(left.export_egg("portable"))
    current = actor("copilot-cli")
    left.status(
        "portable",
        current,
        location="/left",
        status="left",
        artifacts=[],
        blockers=[],
        next_action="left",
        pct=50,
    )
    right.status(
        "portable",
        current,
        location="/right",
        status="right",
        artifacts=[],
        blockers=[],
        next_action="right",
        pct=50,
    )
    with pytest.raises(ProjectError):
        right.import_egg(left.export_egg("portable"))


def test_concurrent_divergent_imports_cannot_both_commit(
    tmp_path: Path,
) -> None:
    base = make_project(tmp_path / "base")
    base_egg = base.export_egg("portable")
    left = ProjectStore(tmp_path / "left")
    right = ProjectStore(tmp_path / "right")
    left.import_egg(base_egg)
    right.import_egg(base_egg)
    current = actor("copilot-cli")
    left.status(
        "portable",
        current,
        location="/left",
        status="left",
        artifacts=[],
        blockers=[],
        next_action="left",
        pct=50,
    )
    right.status(
        "portable",
        current,
        location="/right",
        status="right",
        artifacts=[],
        blockers=[],
        next_action="right",
        pct=50,
    )
    eggs = (left.export_egg("portable"), right.export_egg("portable"))
    target = ProjectStore(tmp_path / "target")
    target.import_egg(base_egg)

    def import_one(path: Path) -> str:
        try:
            target.import_egg(path)
            return "ok"
        except ProjectError:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(import_one, eggs))
    assert sorted(outcomes) == ["blocked", "ok"]
    frames = target.frames("portable")
    assert [frame["seq"] for frame in frames] == list(range(len(frames)))


def test_handoff_document_remains_portable_after_source_deletion(
    tmp_path: Path,
) -> None:
    source = ProjectStore(tmp_path / "source")
    source.open(
        "portable",
        title="Portable",
        goal="Carry handoff evidence",
        owner="example",
        origin="test",
    )
    first = actor("copilot-cli")
    second = actor("claude-code")
    source.punchin(
        "portable",
        first,
        location="/workspace",
        intent="handoff",
        role="builder",
    )
    handoff = tmp_path / "HANDOFF.md"
    handoff.write_text("# Handoff\n\nContinue here.\n", encoding="utf-8")
    source.handoff(
        "portable",
        from_actor=first,
        to_actor=second,
        document=handoff,
        open_questions=["Continue?"],
    )
    exported = tmp_path / "portable.egg"
    source.export_egg("portable", exported)
    shutil.rmtree(source.root)
    target = ProjectStore(tmp_path / "target")
    target.import_egg(exported)
    assert target.verify("portable")["verdict"] == "pass"
    regenerated = target.export_egg("portable")
    with zipfile.ZipFile(regenerated) as archive:
        notes = [
            name for name in archive.namelist()
            if name.startswith("docs/notes/")
        ]
    assert len(notes) == 1


def test_equal_chain_reimport_restores_missing_handoff_document(
    tmp_path: Path,
) -> None:
    source = ProjectStore(tmp_path / "source")
    source.open(
        "portable",
        title="Portable",
        goal="Recover handoff documents",
        owner="example",
        origin="test",
    )
    first = actor("copilot-cli")
    second = actor("claude-code")
    source.punchin(
        "portable",
        first,
        location="/workspace",
        intent="handoff",
        role="builder",
    )
    document = tmp_path / "HANDOFF.md"
    document.write_text("# Handoff\n\nRecover me.\n", encoding="utf-8")
    source.handoff(
        "portable",
        from_actor=first,
        to_actor=second,
        document=document,
        open_questions=[],
    )
    egg = source.export_egg("portable")
    target = ProjectStore(tmp_path / "target")
    target.import_egg(egg)
    note = next(
        (target.project_path("portable") / "docs" / "notes").glob("*.md")
    )
    note.unlink()
    target.import_egg(egg)
    assert note.is_file()


def test_tampered_handoff_document_cannot_be_exported(
    tmp_path: Path,
) -> None:
    store = ProjectStore(tmp_path / "control")
    store.open(
        "portable",
        title="Portable",
        goal="Bind handoff bytes",
        owner="example",
        origin="test",
    )
    first = actor("copilot-cli")
    second = actor("claude-code")
    store.punchin(
        "portable",
        first,
        location="/workspace",
        intent="handoff",
        role="builder",
    )
    document = tmp_path / "HANDOFF.md"
    document.write_text("trusted", encoding="utf-8")
    store.handoff(
        "portable",
        from_actor=first,
        to_actor=second,
        document=document,
        open_questions=[],
    )
    note = next(
        (store.project_path("portable") / "docs" / "notes").glob("*.md")
    )
    note.write_text("tampered", encoding="utf-8")
    with pytest.raises(ProjectError):
        store.export_egg("portable")
