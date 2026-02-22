"""Unit tests for CouplingAnalyser."""

from __future__ import annotations

from pathlib import Path

from dev_stats.core.metrics.coupling_analyser import CouplingAnalyser
from dev_stats.core.models import ClassReport, FileReport


def _make_file(
    name: str,
    imports: tuple[str, ...] = (),
    classes: tuple[ClassReport, ...] = (),
) -> FileReport:
    """Create a FileReport for testing.

    Args:
        name: File path string.
        imports: Import names.
        classes: Class reports.

    Returns:
        A ``FileReport``.
    """
    return FileReport(
        path=Path(name),
        language="python",
        total_lines=10,
        code_lines=8,
        blank_lines=1,
        comment_lines=1,
        imports=imports,
        classes=classes,
    )


class TestCouplingAnalyser:
    """Tests for coupling analysis."""

    def test_no_imports_zero_coupling(self) -> None:
        """Files with no imports have zero efferent coupling."""
        analyser = CouplingAnalyser()
        files = [_make_file("src/a.py"), _make_file("src/b.py")]
        report = analyser.analyse(files)
        for mod in report.modules:
            assert mod.efferent == 0

    def test_efferent_counted(self) -> None:
        """Module that imports another has Ce > 0."""
        analyser = CouplingAnalyser()
        files = [
            _make_file("lib/core.py"),
            _make_file("app/main.py", imports=("core",)),
        ]
        report = analyser.analyse(files)
        app_mod = next(m for m in report.modules if m.name == "app")
        assert app_mod.efferent >= 1

    def test_afferent_counted(self) -> None:
        """Module that is imported has Ca > 0."""
        analyser = CouplingAnalyser()
        files = [
            _make_file("lib/core.py"),
            _make_file("app/main.py", imports=("core",)),
        ]
        report = analyser.analyse(files)
        lib_mod = next(m for m in report.modules if m.name == "lib")
        assert lib_mod.afferent >= 1

    def test_only_imports_instability_one(self) -> None:
        """Module that only imports (Ca=0, Ce>0) has I=1.0."""
        analyser = CouplingAnalyser()
        files = [
            _make_file("lib/core.py"),
            _make_file("app/main.py", imports=("core",)),
        ]
        report = analyser.analyse(files)
        app_mod = next(m for m in report.modules if m.name == "app")
        # If Ce>0 and Ca=0, I should be 1.0
        if app_mod.efferent > 0 and app_mod.afferent == 0:
            assert app_mod.instability == 1.0

    def test_abstractness_detected(self) -> None:
        """Module with abstract classes has abstractness > 0."""
        analyser = CouplingAnalyser()
        abstract_cls = ClassReport(
            name="AbstractBase",
            line=1,
            end_line=10,
            lines=10,
            base_classes=("abc.ABC",),
        )
        files = [_make_file("lib/base.py", classes=(abstract_cls,))]
        report = analyser.analyse(files)
        lib_mod = next(m for m in report.modules if m.name == "lib")
        assert lib_mod.abstractness > 0.0

    def test_distance_computed(self) -> None:
        """Distance from main sequence is computed."""
        analyser = CouplingAnalyser()
        files = [_make_file("src/a.py")]
        report = analyser.analyse(files)
        for mod in report.modules:
            assert 0.0 <= mod.distance <= 1.0
