import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.utils.files import run_dir_for_topic


def test_run_dir_appends_suffix(tmp_path):
    base_dir = tmp_path / "output"
    topic = "Unique Topic"

    run_dir1, slug1 = run_dir_for_topic(str(base_dir), topic)
    assert os.path.isdir(run_dir1)

    run_dir2, slug2 = run_dir_for_topic(str(base_dir), topic)
    assert os.path.isdir(run_dir2)

    assert slug1 == slug2
    assert run_dir2.endswith("-1")
    assert run_dir1 != run_dir2
