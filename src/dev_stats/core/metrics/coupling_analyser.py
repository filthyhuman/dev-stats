"""Coupling analyser computing Ce/Ca/I/A/D per module from import graphs."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from dev_stats.core.models import CouplingReport, ModuleCoupling

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport


class CouplingAnalyser:
    """Analyses inter-module coupling from import data in file reports.

    Computes afferent coupling (Ca), efferent coupling (Ce), instability (I),
    abstractness (A), and distance from the main sequence (D) for each module.
    """

    def analyse(self, files: list[FileReport]) -> CouplingReport:
        """Compute coupling metrics for all modules.

        Args:
            files: File reports containing import lists.

        Returns:
            A ``CouplingReport`` with per-module metrics.
        """
        # Group files by module (parent directory)
        modules: dict[str, list[FileReport]] = defaultdict(list)
        for f in files:
            parent = str(f.path.parent)
            module_name = parent if parent != "." else "(root)"
            modules[module_name].append(f)

        # Build import graph: module -> set of modules it depends on
        module_imports: dict[str, set[str]] = defaultdict(set)
        # Map top-level import names to module names
        import_to_module = self._build_import_map(modules)

        for mod_name, mod_files in modules.items():
            for f in mod_files:
                for imp in f.imports:
                    target = import_to_module.get(imp)
                    if target and target != mod_name:
                        module_imports[mod_name].add(target)

        # Compute Ce (efferent) and Ca (afferent) for each module
        efferent: dict[str, int] = {}
        afferent: dict[str, int] = defaultdict(int)

        for mod_name in modules:
            deps = module_imports.get(mod_name, set())
            efferent[mod_name] = len(deps)
            for dep in deps:
                afferent[dep] += 1

        # Compute per-module metrics
        results: list[ModuleCoupling] = []
        for mod_name, mod_files in modules.items():
            ca = afferent.get(mod_name, 0)
            ce = efferent.get(mod_name, 0)
            instability = ce / (ca + ce) if (ca + ce) > 0 else 0.0

            # Abstractness: ratio of abstract classes to total classes
            total_classes = 0
            abstract_classes = 0
            for f in mod_files:
                for cls in f.classes:
                    total_classes += 1
                    # Heuristic: class is abstract if it has "abstract" base
                    # or "ABC" in base classes, or "Abstract" in name
                    if any(
                        "abc" in b.lower() or "abstract" in b.lower() for b in cls.base_classes
                    ) or cls.name.startswith("Abstract"):
                        abstract_classes += 1

            abstractness = abstract_classes / total_classes if total_classes > 0 else 0.0
            distance = abs(abstractness + instability - 1.0)

            results.append(
                ModuleCoupling(
                    name=mod_name,
                    afferent=ca,
                    efferent=ce,
                    instability=round(instability, 3),
                    abstractness=round(abstractness, 3),
                    distance=round(distance, 3),
                )
            )

        return CouplingReport(modules=tuple(sorted(results, key=lambda m: m.name)))

    @staticmethod
    def _build_import_map(
        modules: dict[str, list[FileReport]],
    ) -> dict[str, str]:
        """Build a mapping from import names to module names.

        Uses file stems and directory names as possible import targets.

        Args:
            modules: Mapping of module name to file reports.

        Returns:
            ``{import_name: module_name}`` mapping.
        """
        result: dict[str, str] = {}
        for mod_name, mod_files in modules.items():
            # Module directory name could be an import target
            if mod_name != "(root)":
                parts = mod_name.replace("\\", "/").split("/")
                for part in parts:
                    if part:
                        result[part] = mod_name

            # File stems could be import targets
            for f in mod_files:
                stem = f.path.stem
                if stem != "__init__":
                    result[stem] = mod_name

        return result
