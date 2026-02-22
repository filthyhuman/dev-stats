"""Unit tests for SortSchema."""

from __future__ import annotations

from dev_stats.output.sort_schema import SortAttribute, SortSchema, SortType


class TestSortType:
    """Tests for the SortType enum."""

    def test_all_types_defined(self) -> None:
        """All expected sort types exist."""
        assert SortType.STRING.value == "string"
        assert SortType.INTEGER.value == "integer"
        assert SortType.FLOAT.value == "float"
        assert SortType.BOOLEAN.value == "boolean"
        assert SortType.DATE.value == "date"


class TestSortAttribute:
    """Tests for SortAttribute frozen dataclass."""

    def test_creation(self) -> None:
        """SortAttribute can be created with required fields."""
        attr = SortAttribute(
            key="file.path",
            label="Path",
            sort_type=SortType.STRING,
            entity="file",
        )
        assert attr.key == "file.path"
        assert attr.label == "Path"
        assert attr.sort_type is SortType.STRING
        assert attr.entity == "file"
        assert attr.default_descending is False
        assert attr.js_accessor == ""

    def test_frozen(self) -> None:
        """SortAttribute is frozen (immutable)."""
        attr = SortAttribute(key="x", label="X", sort_type=SortType.INTEGER, entity="file")
        try:
            attr.key = "y"  # type: ignore[misc]
            raise AssertionError("Should have raised FrozenInstanceError")
        except AttributeError:
            pass


class TestSortSchema:
    """Tests for SortSchema registry."""

    def test_attributes_returns_tuple(self) -> None:
        """attributes() returns a non-empty tuple."""
        schema = SortSchema()
        attrs = schema.attributes()
        assert isinstance(attrs, tuple)
        assert len(attrs) >= 45

    def test_all_attributes_have_required_fields(self) -> None:
        """Every attribute has a key, label, sort_type, and entity."""
        schema = SortSchema()
        for attr in schema.attributes():
            assert attr.key, f"Missing key on {attr}"
            assert attr.label, f"Missing label on {attr}"
            assert isinstance(attr.sort_type, SortType)
            assert attr.entity, f"Missing entity on {attr}"

    def test_keys_are_unique(self) -> None:
        """All attribute keys are unique."""
        schema = SortSchema()
        keys = [a.key for a in schema.attributes()]
        assert len(keys) == len(set(keys))

    def test_for_entity_file(self) -> None:
        """for_entity('file') returns file attributes only."""
        schema = SortSchema()
        file_attrs = schema.for_entity("file")
        assert len(file_attrs) > 0
        assert all(a.entity == "file" for a in file_attrs)

    def test_for_entity_method(self) -> None:
        """for_entity('method') returns method attributes only."""
        schema = SortSchema()
        method_attrs = schema.for_entity("method")
        assert len(method_attrs) > 0
        assert all(a.entity == "method" for a in method_attrs)

    def test_for_entity_unknown(self) -> None:
        """for_entity with unknown entity returns empty tuple."""
        schema = SortSchema()
        assert schema.for_entity("nonexistent") == ()

    def test_by_key_found(self) -> None:
        """by_key returns the correct attribute."""
        schema = SortSchema()
        attr = schema.by_key("file.code_lines")
        assert attr is not None
        assert attr.label == "Code Lines"
        assert attr.sort_type is SortType.INTEGER

    def test_by_key_not_found(self) -> None:
        """by_key returns None for unknown key."""
        schema = SortSchema()
        assert schema.by_key("nonexistent.key") is None

    def test_entity_names(self) -> None:
        """entity_names returns sorted unique entity strings."""
        schema = SortSchema()
        names = schema.entity_names()
        assert isinstance(names, tuple)
        assert "file" in names
        assert "method" in names
        assert "class" in names
        assert "language" in names
        assert names == tuple(sorted(names))

    def test_file_attributes_include_expected(self) -> None:
        """File entity includes path, language, and line counts."""
        schema = SortSchema()
        keys = {a.key for a in schema.for_entity("file")}
        assert "file.path" in keys
        assert "file.language" in keys
        assert "file.total_lines" in keys
        assert "file.code_lines" in keys

    def test_coupling_attributes_present(self) -> None:
        """Coupling entity attributes are registered."""
        schema = SortSchema()
        keys = {a.key for a in schema.for_entity("coupling")}
        assert "coupling.instability" in keys
        assert "coupling.abstractness" in keys
        assert "coupling.distance" in keys
