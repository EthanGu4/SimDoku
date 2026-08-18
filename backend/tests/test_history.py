from app.core import Board, SolveResult, SolveStats
from app.core.history import get_runs, record_run


def _fake_result(algorithm: str = "backtracking", solved: bool = True) -> SolveResult:
    return SolveResult(
        solved=solved,
        solved_board=Board(cells=[[1] * 9 for _ in range(9)]),
        steps=[],
        stats=SolveStats(algorithm=algorithm, elapsed_time=0.01, step_count=0, given_count=30),
    )


def test_record_and_read_back_a_run(tmp_path) -> None:
    db_path = tmp_path / "test.db"

    run = record_run("easy-1", _fake_result(), db_path=db_path)
    assert run.puzzle_id == "easy-1"
    assert run.algorithm == "backtracking"
    assert run.solved is True

    runs = get_runs(db_path=db_path)
    assert len(runs) == 1
    assert runs[0].puzzle_id == "easy-1"
    assert runs[0].elapsed_time == 0.01


def test_filters_by_puzzle_id(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    record_run("easy-1", _fake_result(), db_path=db_path)
    record_run("hard-1", _fake_result(), db_path=db_path)

    runs = get_runs(puzzle_id="hard-1", db_path=db_path)
    assert len(runs) == 1
    assert runs[0].puzzle_id == "hard-1"


def test_most_recent_run_comes_first(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    record_run("easy-1", _fake_result(algorithm="backtracking"), db_path=db_path)
    record_run("easy-1", _fake_result(algorithm="dancing_links"), db_path=db_path)

    runs = get_runs(puzzle_id="easy-1", db_path=db_path)
    assert [run.algorithm for run in runs] == ["dancing_links", "backtracking"]


def test_persists_unsolved_runs_too(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    record_run("hard-1", _fake_result(solved=False), db_path=db_path)

    runs = get_runs(db_path=db_path)
    assert runs[0].solved is False
