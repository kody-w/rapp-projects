from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import sysconfig
import tempfile
import venv


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, check=True, env=env)


def verify(label: str, artifact: pathlib.Path, sdk_wheel: pathlib.Path) -> None:
    with tempfile.TemporaryDirectory(prefix=f"rapp-projects-{label}-") as temp:
        root = pathlib.Path(temp)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([str(python), "-m", "pip", "install", "--no-deps", str(sdk_wheel)])
        run([str(python), "-m", "pip", "install", "--no-deps", str(artifact)])
        home = root / "home"
        env = dict(os.environ, HOME=str(home), RAPP_PROJECTS_ROOT=str(home / "control"))
        probe = subprocess.check_output(
            [
                str(python),
                "-c",
                (
                    "import json,rapp_projects;"
                    "from rapp_projects.core import ProjectStore;"
                    "s=ProjectStore();"
                    "print(json.dumps({'version':rapp_projects.__version__,"
                    "'board':s.board()['board']}))"
                ),
            ],
            text=True,
            env=env,
        )
        value = json.loads(probe)
        assert value["version"] == "0.1.0"
        assert pathlib.Path(value["board"]).is_file()
        cli = subprocess.check_output(
            [str(python), "-m", "rapp_projects.cli", "board", "--json", "{}"],
            text=True,
            env=env,
        )
        assert json.loads(cli)["status"] == "ok"
        data_root = pathlib.Path(
            subprocess.check_output(
                [
                    str(python),
                    "-c",
                    "import sysconfig;print(sysconfig.get_path('data'))",
                ],
                text=True,
            ).strip()
        )
        assert (
            data_root
            / "share"
            / "rapp-projects"
            / "agents"
            / "rapp_projects_agent.py"
        ).is_file()
        adapter = (
            data_root
            / "share"
            / "rapp-projects"
            / "agents"
            / "rapp_projects_agent.py"
        )
        adapter_result = subprocess.check_output(
            [str(python), str(adapter)],
            text=True,
            env=env,
        )
        assert json.loads(adapter_result)["status"] == "ok"
    print(f"{label}: installed package, CLI, board, and Brainstem adapter verified")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sdk_wheel", type=pathlib.Path)
    parser.add_argument("project_wheel", type=pathlib.Path)
    parser.add_argument("project_sdist", type=pathlib.Path)
    args = parser.parse_args()
    verify("wheel", args.project_wheel, args.sdk_wheel)
    verify("sdist", args.project_sdist, args.sdk_wheel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
