"""
Test source ingestion execution boundary packet helper v1
"""
import pytest
from weslr.source_ingestion_execution_boundary import (
    build_source_ingestion_execution_packet_v1,
    validate_source_ingestion_execution_packet_v1,
    summarize_source_ingestion_execution_packet_v1,
    render_source_ingestion_execution_markdown_v1,
    to_source_ingestion_execution_json_safe_v1,
    build_initial_source_ingestion_execution_examples_v1
)

def test_build_and_validate_packet():
    packet = build_source_ingestion_execution_packet_v1("test-source", {"key": "value"})
    assert validate_source_ingestion_execution_packet_v1(packet)
    assert not validate_source_ingestion_execution_packet_v1({})


def test_summarize_packet():
    packet = build_source_ingestion_execution_packet_v1("test-source", {"key": "value"})
    summary = summarize_source_ingestion_execution_packet_v1(packet)
    assert "test-source" in summary


def test_render_markdown():
    packet = build_source_ingestion_execution_packet_v1("test-source", {"key": "value"})
    markdown = render_source_ingestion_execution_markdown_v1(packet)
    assert "Source Ingestion Execution Packet v1" in markdown
    assert "key" in markdown


def test_json_safe_conversion():
    packet = build_source_ingestion_execution_packet_v1("test-source", {"key": "value"})
    json_safe = to_source_ingestion_execution_json_safe_v1(packet)
    assert isinstance(json_safe, dict)
    assert json_safe["source_id"] == "test-source"


def test_initial_examples():
    examples = build_initial_source_ingestion_execution_examples_v1()
    assert len(examples) == 2
    for example in examples:
        assert validate_source_ingestion_execution_packet_v1(example)
