# Tasks 03 — Python Parser, Aggregator & Terminal Output

## AbstractParser & Utilities

- [ ] T03-001  Create src/dev_stats/core/parsers/__init__.py — empty
- [ ] T03-002  Create src/dev_stats/core/parsers/abstract_parser.py — _RawLOCCounts dataclass (total, code, comment, blank)
- [ ] T03-003  Add count_loc(source: str, comment_prefixes: tuple[str,...]) -> _RawLOCCounts to abstract_parser.py — module-level function
- [ ] T03-004  Add count_todos(source: str) -> int to abstract_parser.py — regex for TODO/FIXME/HACK/XXX/BUG
- [ ] T03-005  Add detect_encoding(path: Path) -> str to abstract_parser.py — try chardet, fallback utf-8
- [ ] T03-006  Add AbstractParser(ABC) class — supported_extensions property (abstract), language_name property (abstract), comment_prefixes property (returns ("#",)), can_parse(path) -> bool, parse(path) template method that calls all hooks, abstract _extract_classes, _extract_functions, _detect_imports

## GenericParser

- [ ] T03-007  Create src/dev_stats/core/parsers/generic_parser.py — _EXT_MAP: dict[str, tuple[str, tuple[str,...]]] mapping 40+ extensions to (language, comment_prefixes)
- [ ] T03-008  Add GenericParser(AbstractParser) class — _language_for(path), _prefixes_for(path), can_parse always True, override parse() to inject correct prefixes, return FileReport with no classes/functions
- [ ] T03-009  Implement _extract_classes, _extract_functions, _detect_imports as empty return [] (required by abstract)

## PythonParser

- [ ] T03-010  Create src/dev_stats/core/parsers/python_parser.py — _COMPLEXITY_NODES tuple of AST node types
- [ ] T03-011  Add _cyclomatic_complexity(node: ast.AST) -> int — walk node, count branching nodes, add BoolOp extra operands
- [ ] T03-012  Add _nesting_depth(node: ast.AST) -> int — recursive depth counter for if/for/while/with/try
- [ ] T03-013  Add _extract_parameters(func_node) -> list[ParameterReport] — exclude self/cls, detect defaults, type annotations via ast.unparse
- [ ] T03-014  Add _collect_attributes(class_node) -> list[str] — walk for ast.Assign and ast.AnnAssign where target is self.x or cls.x
- [ ] T03-015  Add _build_method_report(func_node, source_lines) -> MethodReport — use all helpers above, detect is_constructor/is_static/is_property/is_abstract from decorators
- [ ] T03-016  Add PythonParser(AbstractParser) class — extensions {".py", ".pyi"}, language_name "Python", comment_prefixes ("#",)
- [ ] T03-017  Implement PythonParser._extract_classes() — ast.parse, walk for ClassDef, build ClassReport for each, catch SyntaxError (log warning, return [])
- [ ] T03-018  Implement PythonParser._extract_functions() — only direct children of Module that are FunctionDef/AsyncFunctionDef
- [ ] T03-019  Implement PythonParser._detect_imports() — walk for Import and ImportFrom, extract top-level module name, deduplicate, sort
- [ ] T03-020  Register PythonParser and GenericParser in ParserRegistry default construction

## Aggregator

- [ ] T03-021  Create src/dev_stats/core/aggregator.py — class Aggregator with aggregate(files: list[FileReport], git_data: GitData | None = None) -> RepoReport
- [ ] T03-022  Implement Aggregator._compute_totals(files) -> dict — sum loc_total, loc_code, loc_comment, loc_blank, count classes, methods, functions
- [ ] T03-023  Implement Aggregator._compute_averages(files, totals) -> dict — avg_loc_per_file, avg_loc_per_class, avg_loc_per_method, avg_cyclomatic_complexity (weighted by method count), avg_parameters, avg_attributes
- [ ] T03-024  Implement Aggregator._compute_language_summaries(files) -> tuple[LanguageSummary,...] — group by language, compute per-language LanguageSummary
- [ ] T03-025  Implement Aggregator._compute_module_reports(files) -> tuple[ModuleReport,...] — group by parent directory

## Terminal Reporter & Wire-up

- [ ] T03-026  Create src/dev_stats/output/__init__.py — empty
- [ ] T03-027  Create src/dev_stats/output/exporters/__init__.py — empty
- [ ] T03-028  Create src/dev_stats/output/exporters/abstract_exporter.py — class AbstractExporter(ABC): __init__(report, config), abstract export(output_dir: Path) -> list[Path]
- [ ] T03-029  Create src/dev_stats/output/exporters/terminal_reporter.py — class TerminalReporter(AbstractExporter): export() prints to stdout using Rich Console: hero card panel (files/LOC/classes/methods/languages), language table, top-N files by LOC, top-N classes by WMC, top-N methods by CC
- [ ] T03-030  Update cli/analyse_command.py — call Scanner → Dispatcher → Aggregator → TerminalReporter in sequence, add basic error handling

## Tests & Fixtures

- [ ] T03-031  Create tests/fixtures/sample_files/python/sample.py — Calculator class with __init__, add (CC=3), reset; standalone helper function; hand-verify expected values in file header comment
- [ ] T03-032  Create tests/unit/core/parsers/test_python_parser.py — test cases: class found, method count, CC=1 for simple, CC=3 for if/elif, CC=2 for loop, parameters extracted, default detected, self.x as attribute, import detection, no-dups import, async function found, abstract class detected, static method detected, property detected, syntax error returns empty, file not found raises, empty file zero counts, nested class found
- [ ] T03-033  Create tests/unit/core/parsers/test_generic_parser.py — LOC count for shell script, comment lines for # prefix, blank lines counted, can_parse returns True for .xyz, language detected from extension
- [ ] T03-034  Create tests/unit/core/test_aggregator.py — give known list of FileReports, assert totals correct, assert avg_loc_per_file = sum/count, assert LanguageSummary built per language
