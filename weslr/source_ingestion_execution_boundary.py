"""
Source ingestion execution boundary packet helper v1
"""
from typing import Dict, Any, List


def build_source_ingestion_execution_packet_v1(source_id: str, execution_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Build a source ingestion execution packet v1."""
    packet = {
        "version": "v1",
        "source_id": source_id,
        "execution_metadata": execution_metadata
    }
    return packet


def validate_source_ingestion_execution_packet_v1(packet: Dict[str, Any]) -> bool:
    """Validate the source ingestion execution packet v1."""
    if not isinstance(packet, dict):
        return False
    if packet.get("version") != "v1":
        return False
    if not isinstance(packet.get("source_id"), str):
        return False
    if not isinstance(packet.get("execution_metadata"), dict):
        return False
    return True


def summarize_source_ingestion_execution_packet_v1(packet: Dict[str, Any]) -> str:
    """Summarize the source ingestion execution packet v1."""
    source_id = packet.get("source_id", "?")
    metadata_keys = list(packet.get("execution_metadata", {}).keys())
    return f"SourceIngestionExecutionPacket(v1) source_id={source_id} keys={metadata_keys}"


def render_source_ingestion_execution_markdown_v1(packet: Dict[str, Any]) -> str:
    """Render the source ingestion execution packet as markdown v1."""
    summary = summarize_source_ingestion_execution_packet_v1(packet)
    lines = ["# Source Ingestion Execution Packet v1", f"**Summary:** {summary}"]
    exec_meta = packet.get("execution_metadata", {})
    for key, value in exec_meta.items():
        lines.append(f"- **{key}**: {value}")
    return "\n".join(lines)


def to_source_ingestion_execution_json_safe_v1(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Convert the source ingestion execution packet to a JSON-safe dict v1."""
    # This implementation assumes the packet is already JSON serializable
    return packet


def build_initial_source_ingestion_execution_examples_v1() -> List[Dict[str, Any]]:
    """Build initial example packets for source ingestion execution v1."""
    examples = [
        build_source_ingestion_execution_packet_v1(
            "source-1234",
            {"status": "started", "timestamp": "2026-06-18T07:00:00Z"}
        ),
        build_source_ingestion_execution_packet_v1(
            "source-5678",
            {"status": "completed", "timestamp": "2026-06-18T07:05:00Z", "result": "success"}
        )
    ]
    return examples
