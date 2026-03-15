from __future__ import annotations


def test_rendered_write_tool_result_uses_diff_markdown():
    from worker_core.tool_display import build_file_diff_display, format_tool_result_display

    display = format_tool_result_display(
        tool_name="write",
        content="Created 1 lines to /tmp/demo.py",
        is_error=False,
        display=build_file_diff_display(tool_name="write", path="demo.py", before="", after="print(1)\n"),
    )

    assert display.title == "demo.py"
    assert display.kind == "file_diff"
    assert display.status_badge == "+1  -0"
    assert display.markdown is False
    assert "+print(1)" in display.body
