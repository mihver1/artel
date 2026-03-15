from __future__ import annotations


def test_write_diff_result_keeps_single_tool_lifecycle_card():
    from worker_core.tool_display import build_file_diff_display, format_tool_call_display, format_tool_result_display

    call = format_tool_call_display("write", {"path": "demo.py", "content": "print(1)\n"})
    result = format_tool_result_display(
        tool_name="write",
        content="Created 1 lines to /tmp/demo.py",
        is_error=False,
        display=build_file_diff_display(tool_name="write", path="demo.py", before="", after="print(1)\n"),
    )

    assert call.title == "⚙ write demo.py"
    assert result.title == "demo.py"
    assert result.kind == "file_diff"
    assert result.status_badge == "+1  -0"
    assert result.markdown is False
