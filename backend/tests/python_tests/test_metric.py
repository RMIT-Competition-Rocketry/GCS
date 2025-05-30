import pytest
import backend.includes_python.metric as metric
import re

# ASCII extended printable
_allowed_pattern = re.compile(
    r'^[\x20-\x7E\x80\x82-\x8C\x8E\x91-\x9C\x9E-\xFF]*$')


def test_to_visible_repr_output():
    for i in range(0x110000):
        c = chr(i)
        output = metric.Metric.to_visible_repr(c)
        assert len(output) >= 1, f"Empty output for codepoint {i}"
        assert _allowed_pattern.match(output), (
            f"Output contains illegal chars for decimal {i}: {output}"
        )


def test_to_visible_repr_output_multiple():
    for i in range(0, 0x110000-10, 10):
        c = "".join(chr(x) for x in range(i, i + 10))
        output = metric.Metric.to_visible_repr(c)
        assert len(output) >= 1, f"Empty output for codepoint {i}"
        assert _allowed_pattern.match(output), (
            f"Output contains illegal chars for decimal {i}: {output}"
        )
