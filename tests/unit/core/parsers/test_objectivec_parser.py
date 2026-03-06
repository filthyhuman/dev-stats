"""Unit tests for ObjectiveCParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dev_stats.core.parsers.objectivec_parser import ObjectiveCParser

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport


def _parse_source(source: str, filename: str = "test.m") -> FileReport:
    """Parse a source string and return the FileReport.

    Args:
        source: Objective-C source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    tmp = Path("/tmp/_dev_stats_test_objc")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = ObjectiveCParser()
    return parser.parse(test_file, tmp)


class TestObjectiveCParserMetadata:
    """Tests for parser metadata."""

    def test_language_name(self) -> None:
        """ObjectiveCParser reports 'objectivec'."""
        parser = ObjectiveCParser()
        assert parser.language_name == "objectivec"

    def test_supported_extensions(self) -> None:
        """ObjectiveCParser handles .m and .mm."""
        parser = ObjectiveCParser()
        assert ".m" in parser.supported_extensions
        assert ".mm" in parser.supported_extensions

    def test_comment_prefix(self) -> None:
        """ObjectiveCParser uses // for comments."""
        parser = ObjectiveCParser()
        assert "//" in parser.comment_prefixes


class TestObjectiveCParserClasses:
    """Tests for class extraction."""

    def test_implementation_found(self) -> None:
        """ObjectiveCParser finds @implementation."""
        src = '@implementation MyClass\n- (void)doWork {\n    NSLog(@"work");\n}\n@end\n'
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "MyClass"

    def test_interface_found(self) -> None:
        """ObjectiveCParser finds @interface."""
        src = "@interface Foo : NSObject\n@end\n"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_base_class_detected(self) -> None:
        """ObjectiveCParser detects inheritance."""
        src = "@interface Foo : NSObject\n@end\n"
        report = _parse_source(src)
        assert "NSObject" in report.classes[0].base_classes

    def test_category_found(self) -> None:
        """ObjectiveCParser detects categories."""
        src = (
            "@implementation NSString(Utils)\n"
            "- (BOOL)isEmpty {\n"
            "    return self.length == 0;\n"
            "}\n"
            "@end\n"
        )
        report = _parse_source(src)
        assert report.num_classes == 1
        assert "Utils" in report.classes[0].name

    def test_protocol_found(self) -> None:
        """ObjectiveCParser detects @protocol."""
        src = "@protocol MyDelegate\n- (void)didFinish;\n@end\n"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert "protocol" in report.classes[0].name


class TestObjectiveCParserMethods:
    """Tests for method extraction."""

    def test_instance_method(self) -> None:
        """ObjectiveCParser finds instance methods."""
        src = '@implementation Foo\n- (void)bar {\n    NSLog(@"bar");\n}\n@end\n'
        report = _parse_source(src)
        names = [m.name for m in report.classes[0].methods]
        assert "bar" in names

    def test_class_method(self) -> None:
        """ObjectiveCParser finds class methods."""
        src = "@implementation Foo\n+ (instancetype)sharedInstance {\n    return nil;\n}\n@end\n"
        report = _parse_source(src)
        names = [m.name for m in report.classes[0].methods]
        assert "sharedInstance" in names

    def test_method_with_params(self) -> None:
        """ObjectiveCParser extracts method parameters."""
        src = (
            "@implementation Foo\n"
            "- (void)setName:(NSString *)name age:(int)age {\n"
            "    _name = name;\n"
            "    _age = age;\n"
            "}\n"
            "@end\n"
        )
        report = _parse_source(src)
        method = report.classes[0].methods[0]
        assert len(method.parameters) == 2

    def test_init_is_constructor(self) -> None:
        """ObjectiveCParser marks init methods as constructors."""
        src = (
            "@implementation Foo\n"
            "- (instancetype)initWithName:(NSString *)name {\n"
            "    self = [super init];\n"
            "    return self;\n"
            "}\n"
            "@end\n"
        )
        report = _parse_source(src)
        assert report.classes[0].methods[0].is_constructor is True


class TestObjectiveCParserFunctions:
    """Tests for top-level C function extraction."""

    def test_c_function_found(self) -> None:
        """ObjectiveCParser finds top-level C functions."""
        src = 'static void helper(int x) {\n    printf("%d", x);\n}\n'
        report = _parse_source(src)
        assert report.num_functions >= 1
        assert report.functions[0].name == "helper"

    def test_c_function_not_inside_class(self) -> None:
        """C functions inside @implementation are excluded."""
        src = (
            "@implementation Foo\n"
            "static void internal(int x) {\n"
            '    printf("%d", x);\n'
            "}\n"
            "- (void)bar {\n"
            "}\n"
            "@end\n"
            "static void external(int y) {\n"
            '    printf("%d", y);\n'
            "}\n"
        )
        report = _parse_source(src)
        func_names = [f.name for f in report.functions]
        assert "external" in func_names
        assert "internal" not in func_names


class TestObjectiveCParserImports:
    """Tests for import detection."""

    def test_import_detected(self) -> None:
        """ObjectiveCParser detects #import."""
        src = '#import <Foundation/Foundation.h>\n#import "MyClass.h"\n'
        report = _parse_source(src)
        assert "Foundation" in report.imports
        assert "MyClass" in report.imports

    def test_include_detected(self) -> None:
        """ObjectiveCParser detects #include."""
        src = "#include <stdio.h>\n"
        report = _parse_source(src)
        assert "stdio" in report.imports


class TestObjectiveCParserCC:
    """Tests for cyclomatic complexity."""

    def test_simple_method_cc_one(self) -> None:
        """Simple method has CC=1."""
        src = '@implementation Foo\n- (void)simple {\n    NSLog(@"ok");\n}\n@end\n'
        report = _parse_source(src)
        assert report.classes[0].methods[0].cyclomatic_complexity == 1

    def test_if_increases_cc(self) -> None:
        """If/else increases CC."""
        src = (
            "@implementation Foo\n"
            "- (void)branch:(int)x {\n"
            "    if (x > 0) {\n"
            '        NSLog(@"pos");\n'
            "    } else if (x < 0) {\n"
            '        NSLog(@"neg");\n'
            "    }\n"
            "}\n"
            "@end\n"
        )
        report = _parse_source(src)
        assert report.classes[0].methods[0].cyclomatic_complexity >= 3


class TestObjectiveCParserLOC:
    """Tests for line counting."""

    def test_loc_counts(self) -> None:
        """ObjectiveCParser counts lines correctly."""
        src = (
            "// Comment\n"
            "#import <Foundation/Foundation.h>\n"
            "\n"
            "@implementation Foo\n"
            "- (void)bar {\n"
            "}\n"
            "@end\n"
        )
        report = _parse_source(src)
        assert report.total_lines == 7
        assert report.blank_lines == 1
        assert report.comment_lines == 1
        assert report.code_lines == 5

    def test_mm_extension(self) -> None:
        """ObjectiveCParser handles .mm files."""
        src = "@implementation Foo\n@end\n"
        report = _parse_source(src, filename="test.mm")
        assert report.language == "objectivec"
