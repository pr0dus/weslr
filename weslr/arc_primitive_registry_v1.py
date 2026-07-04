"""ARC-AGI-2 primitive registry V1.

Defines a shared, trace-safe primitive vocabulary for discovery and runner
architecture work. This module is registry/manifest only: no public ARC data,
no solver execution, and no family search.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

UNSAFE_TRACE_METADATA_LABELS_V1 = {
    "raw_grid",
    "expected_output",
    "solution",
    "answer_key",
    "public_solution",
}

REQUIRED_DESCRIPTOR_FIELDS_V1 = (
    "primitive_name",
    "family",
    "input_type",
    "output_type",
    "preconditions",
    "effect_summary",
    "train_inference_fn_name",
    "executor_fn_name",
    "inverse_or_comparable_relation",
    "rejection_reasons",
    "trace_safe_metadata",
)


@dataclass(frozen=True)
class PrimitiveDescriptor:
    primitive_name: str
    family: str
    input_type: str
    output_type: str
    preconditions: tuple[str, ...] = field(default_factory=tuple)
    effect_summary: str = ""
    train_inference_fn_name: str = ""
    executor_fn_name: str = ""
    inverse_or_comparable_relation: str = ""
    rejection_reasons: tuple[str, ...] = field(default_factory=tuple)
    trace_safe_metadata: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "primitive_name", _safe_text(self.primitive_name))
        object.__setattr__(self, "family", _safe_text(self.family))
        object.__setattr__(self, "input_type", _safe_text(self.input_type))
        object.__setattr__(self, "output_type", _safe_text(self.output_type))
        object.__setattr__(self, "effect_summary", _safe_text(self.effect_summary))
        object.__setattr__(self, "train_inference_fn_name", _safe_text(self.train_inference_fn_name))
        object.__setattr__(self, "executor_fn_name", _safe_text(self.executor_fn_name))
        object.__setattr__(self, "preconditions", _normalize_tuple(self.preconditions))
        object.__setattr__(self, "rejection_reasons", _normalize_tuple(self.rejection_reasons))
        object.__setattr__(self, "trace_safe_metadata", _normalize_tuple(self.trace_safe_metadata))
        object.__setattr__(self, "inverse_or_comparable_relation", _safe_text(self.inverse_or_comparable_relation))
        _validate_descriptor(self)

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "primitive_name": self.primitive_name,
            "family": self.family,
            "input_type": self.input_type,
            "output_type": self.output_type,
            "preconditions": list(self.preconditions),
            "effect_summary": self.effect_summary,
            "train_inference_fn_name": self.train_inference_fn_name,
            "executor_fn_name": self.executor_fn_name,
            "inverse_or_comparable_relation": self.inverse_or_comparable_relation,
            "rejection_reasons": list(self.rejection_reasons),
            "trace_safe_metadata": list(self.trace_safe_metadata),
        }


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _normalize_tuple(values: Any) -> tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes, bytearray)):
        return (_safe_text(values),)
    if not isinstance(values, Iterable):
        return (_safe_text(values),)
    return tuple(_safe_text(value) for value in values)


def _validate_trace_metadata_labels(labels: Sequence[str]) -> None:
    for label in labels:
        if label in UNSAFE_TRACE_METADATA_LABELS_V1:
            raise ValueError(f"unsafe_trace_metadata_label:{label}")


def _validate_descriptor(descriptor: PrimitiveDescriptor) -> None:
    missing_fields = []
    for field_name in REQUIRED_DESCRIPTOR_FIELDS_V1:
        value = getattr(descriptor, field_name)
        if field_name in {"preconditions", "rejection_reasons", "trace_safe_metadata"}:
            if not value:
                missing_fields.append(field_name)
        elif not _safe_text(value):
            missing_fields.append(field_name)
    if descriptor.inverse_or_comparable_relation is None:
        pass
    if missing_fields:
        raise ValueError(f"missing_required_fields:{','.join(sorted(missing_fields))}")
    _validate_trace_metadata_labels(descriptor.trace_safe_metadata)


class PrimitiveRegistry:
    def __init__(self, primitives: Sequence[PrimitiveDescriptor] | None = None) -> None:
        self._primitives: dict[str, PrimitiveDescriptor] = {}
        if primitives is not None:
            for primitive in primitives:
                self.register(primitive)

    def register(self, descriptor: PrimitiveDescriptor) -> None:
        if not isinstance(descriptor, PrimitiveDescriptor):
            raise TypeError("descriptor_must_be_primitive_descriptor")
        if descriptor.primitive_name in self._primitives:
            raise ValueError(f"duplicate_primitive_name:{descriptor.primitive_name}")
        self._primitives[descriptor.primitive_name] = descriptor

    def get(self, primitive_name: str) -> PrimitiveDescriptor | None:
        return self._primitives.get(_safe_text(primitive_name))

    def list_primitives(self) -> list[PrimitiveDescriptor]:
        return [self._primitives[name] for name in sorted(self._primitives)]

    def list_by_family(self, family: str) -> list[PrimitiveDescriptor]:
        family_text = _safe_text(family)
        return [descriptor for descriptor in self.list_primitives() if descriptor.family == family_text]

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        seen: set[str] = set()
        for descriptor in self.list_primitives():
            if descriptor.primitive_name in seen:
                errors.append(f"duplicate_primitive_name:{descriptor.primitive_name}")
            seen.add(descriptor.primitive_name)
            try:
                _validate_descriptor(descriptor)
            except Exception as exc:
                errors.append(f"{descriptor.primitive_name}:{exc}")
        return {
            "valid": not errors,
            "primitive_count": len(self._primitives),
            "errors": errors,
        }

    def export_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": "ArcPrimitiveRegistryV1",
            "primitive_count": len(self._primitives),
            "primitives": [descriptor.to_json_safe_dict() for descriptor in self.list_primitives()],
        }


_BUILTIN_DESCRIPTOR_SPECS_V1 = (
    {
        "primitive_name": "crop_foreground_bbox",
        "family": "object_bbox",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("stable_background", "foreground_bbox_available"),
        "effect_summary": "Crop the foreground bounding box from a grid.",
        "train_inference_fn_name": "arc_object_bbox_solver_v1.solve_object_bbox_task",
        "executor_fn_name": "arc_object_extraction_v1.crop_to_foreground_bbox_v1",
        "inverse_or_comparable_relation": "compare_to_crop_largest_object",
        "rejection_reasons": ("no_foreground", "bbox_out_of_bounds", "background_ambiguous"),
        "trace_safe_metadata": ("primitive_name", "family", "bbox_mode", "train_fit"),
    },
    {
        "primitive_name": "crop_largest_object",
        "family": "object_bbox",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("stable_background", "largest_object_unique"),
        "effect_summary": "Crop the bounding box of the single largest object.",
        "train_inference_fn_name": "arc_object_bbox_solver_v1.solve_object_bbox_task",
        "executor_fn_name": "arc_object_extraction_v1.crop_to_largest_object_bbox_v1",
        "inverse_or_comparable_relation": "compare_to_crop_foreground_bbox",
        "rejection_reasons": ("no_foreground", "largest_object_ambiguous", "background_ambiguous"),
        "trace_safe_metadata": ("primitive_name", "family", "object_size_rank", "train_fit"),
    },
    {
        "primitive_name": "crop_selected_color_object",
        "family": "object_bbox",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("stable_background", "selected_color_unique_object"),
        "effect_summary": "Crop the object associated with a selected foreground color.",
        "train_inference_fn_name": "arc_object_bbox_solver_v1.solve_object_bbox_task",
        "executor_fn_name": "arc_object_extraction_v1.crop_selected_color_object_v1",
        "inverse_or_comparable_relation": "compare_to_recolor_source_color",
        "rejection_reasons": ("selected_color_not_found", "selected_color_ambiguous", "background_ambiguous"),
        "trace_safe_metadata": ("primitive_name", "family", "selected_color", "train_fit"),
    },
    {
        "primitive_name": "translate_single_object",
        "family": "object_bbox",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("single_object", "background_inferable"),
        "effect_summary": "Translate a single object by a bounded offset.",
        "train_inference_fn_name": "arc_object_bbox_solver_v1.solve_object_bbox_task",
        "executor_fn_name": "arc_object_extraction_v1.translate_object_v1",
        "inverse_or_comparable_relation": "compare_to_rotate_object_90",
        "rejection_reasons": ("translation_ambiguous", "translation_out_of_bounds", "background_ambiguous"),
        "trace_safe_metadata": ("primitive_name", "family", "delta_row", "delta_col", "train_fit"),
    },
    {
        "primitive_name": "rotate_object_90",
        "family": "shape_geometry",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("single_object", "angle_discrete"),
        "effect_summary": "Rotate a single object by 90 degrees.",
        "train_inference_fn_name": "arc_shape_geometry_v1.infer_shape_geometry_hypotheses_v1",
        "executor_fn_name": "arc_shape_geometry_v1.rotate_object_mask_v1",
        "inverse_or_comparable_relation": "rotate_object_270",
        "rejection_reasons": ("single_object_required", "orientation_mismatch", "dimensions_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "turns", "train_fit"),
    },
    {
        "primitive_name": "rotate_object_180",
        "family": "shape_geometry",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("single_object", "angle_discrete"),
        "effect_summary": "Rotate a single object by 180 degrees.",
        "train_inference_fn_name": "arc_shape_geometry_v1.infer_shape_geometry_hypotheses_v1",
        "executor_fn_name": "arc_shape_geometry_v1.rotate_object_mask_v1",
        "inverse_or_comparable_relation": "rotate_object_180",
        "rejection_reasons": ("single_object_required", "orientation_mismatch", "dimensions_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "turns", "train_fit"),
    },
    {
        "primitive_name": "rotate_object_270",
        "family": "shape_geometry",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("single_object", "angle_discrete"),
        "effect_summary": "Rotate a single object by 270 degrees.",
        "train_inference_fn_name": "arc_shape_geometry_v1.infer_shape_geometry_hypotheses_v1",
        "executor_fn_name": "arc_shape_geometry_v1.rotate_object_mask_v1",
        "inverse_or_comparable_relation": "rotate_object_90",
        "rejection_reasons": ("single_object_required", "orientation_mismatch", "dimensions_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "turns", "train_fit"),
    },
    {
        "primitive_name": "reflect_object_horizontal",
        "family": "shape_geometry",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("single_object", "axis_known"),
        "effect_summary": "Reflect a single object across the horizontal axis.",
        "train_inference_fn_name": "arc_shape_geometry_v1.infer_shape_geometry_hypotheses_v1",
        "executor_fn_name": "arc_shape_geometry_v1.reflect_object_mask_v1",
        "inverse_or_comparable_relation": "reflect_object_horizontal",
        "rejection_reasons": ("single_object_required", "orientation_mismatch", "dimensions_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "axis", "train_fit"),
    },
    {
        "primitive_name": "reflect_object_vertical",
        "family": "shape_geometry",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("single_object", "axis_known"),
        "effect_summary": "Reflect a single object across the vertical axis.",
        "train_inference_fn_name": "arc_shape_geometry_v1.infer_shape_geometry_hypotheses_v1",
        "executor_fn_name": "arc_shape_geometry_v1.reflect_object_mask_v1",
        "inverse_or_comparable_relation": "reflect_object_vertical",
        "rejection_reasons": ("single_object_required", "orientation_mismatch", "dimensions_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "axis", "train_fit"),
    },
    {
        "primitive_name": "preserve_shape_translate",
        "family": "shape_geometry",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("single_object", "translation_known"),
        "effect_summary": "Translate a single object while preserving its canonical shape.",
        "train_inference_fn_name": "arc_shape_geometry_v1.infer_shape_geometry_hypotheses_v1",
        "executor_fn_name": "arc_shape_geometry_v1.translate_object_v1",
        "inverse_or_comparable_relation": "translate_single_object",
        "rejection_reasons": ("translation_ambiguous", "translation_out_of_bounds", "shape_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "delta_row", "delta_col", "train_fit"),
    },
    {
        "primitive_name": "recolor_global",
        "family": "color_role",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("global_color_mapping_known",),
        "effect_summary": "Replace one color everywhere with another.",
        "train_inference_fn_name": "arc_color_role_abstraction_v1.infer_color_role_hypotheses_v1",
        "executor_fn_name": "arc_color_role_abstraction_v1._apply_mapping",
        "inverse_or_comparable_relation": "recolor_global",
        "rejection_reasons": ("color_mapping_mismatch", "background_ambiguous", "shape_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "color_mapping", "train_fit"),
    },
    {
        "primitive_name": "recolor_foreground",
        "family": "color_role",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("foreground_color_mapping_known",),
        "effect_summary": "Recolor foreground cells while preserving the background.",
        "train_inference_fn_name": "arc_color_role_abstraction_v1.infer_color_role_hypotheses_v1",
        "executor_fn_name": "arc_color_role_abstraction_v1._apply_mapping",
        "inverse_or_comparable_relation": "recolor_background",
        "rejection_reasons": ("color_mapping_mismatch", "background_ambiguous", "foreground_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "foreground_colors", "train_fit"),
    },
    {
        "primitive_name": "recolor_source_color",
        "family": "color_role",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("source_color_unique",),
        "effect_summary": "Recolor the source color object or cells to a target color.",
        "train_inference_fn_name": "arc_color_role_abstraction_v1.infer_color_role_hypotheses_v1",
        "executor_fn_name": "arc_color_role_abstraction_v1._apply_mapping",
        "inverse_or_comparable_relation": "crop_selected_color_object",
        "rejection_reasons": ("selected_color_ambiguous", "selected_color_not_found", "color_mapping_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "source_color", "target_color", "train_fit"),
    },
    {
        "primitive_name": "recolor_background",
        "family": "color_role",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("background_inferable",),
        "effect_summary": "Recolor the background while leaving foreground structure stable.",
        "train_inference_fn_name": "arc_color_role_abstraction_v1.infer_color_role_hypotheses_v1",
        "executor_fn_name": "arc_color_role_abstraction_v1._apply_mapping",
        "inverse_or_comparable_relation": "recolor_foreground",
        "rejection_reasons": ("background_ambiguous", "color_mapping_mismatch", "foreground_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "background_color", "train_fit"),
    },
    {
        "primitive_name": "swap_two_colors",
        "family": "color_role",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("two_color_mapping_known",),
        "effect_summary": "Swap two colors while leaving others unchanged.",
        "train_inference_fn_name": "arc_color_role_abstraction_v1.infer_color_role_hypotheses_v1",
        "executor_fn_name": "arc_color_role_abstraction_v1._apply_mapping",
        "inverse_or_comparable_relation": "swap_two_colors",
        "rejection_reasons": ("swap_ambiguous", "color_mapping_mismatch", "background_ambiguous"),
        "trace_safe_metadata": ("primitive_name", "family", "swapped_colors", "train_fit"),
    },
    {
        "primitive_name": "tile_grid",
        "family": "resize_tile",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("repeat_factor_known",),
        "effect_summary": "Repeat a grid by bounded row and column factors.",
        "train_inference_fn_name": "arc_resize_tile_canvas_v1.infer_resize_tile_hypotheses_v1",
        "executor_fn_name": "arc_resize_tile_canvas_v1._tile_grid",
        "inverse_or_comparable_relation": "crop_then_tile",
        "rejection_reasons": ("invalid_repeat_factor", "dimension_mismatch", "pattern_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "repeat_rows", "repeat_cols", "train_fit"),
    },
    {
        "primitive_name": "scale_cells_integer",
        "family": "resize_tile",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("integer_scale_known",),
        "effect_summary": "Scale each cell into an integer block while preserving colors.",
        "train_inference_fn_name": "arc_resize_tile_canvas_v1.infer_resize_tile_hypotheses_v1",
        "executor_fn_name": "arc_resize_tile_canvas_v1._repeat_grid",
        "inverse_or_comparable_relation": "tile_grid",
        "rejection_reasons": ("invalid_scale_factor", "dimension_mismatch", "pattern_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "scale_rows", "scale_cols", "train_fit"),
    },
    {
        "primitive_name": "add_uniform_border",
        "family": "resize_tile",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("border_thickness_known", "border_color_known"),
        "effect_summary": "Add a uniform border around the grid.",
        "train_inference_fn_name": "arc_resize_tile_canvas_v1.infer_resize_tile_hypotheses_v1",
        "executor_fn_name": "arc_resize_tile_canvas_v1._pad_grid",
        "inverse_or_comparable_relation": "crop_foreground_bbox",
        "rejection_reasons": ("invalid_border_padding", "dimension_mismatch", "border_color_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "border_color", "padding", "train_fit"),
    },
    {
        "primitive_name": "crop_then_tile",
        "family": "resize_tile",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("foreground_crop_known", "repeat_factor_known"),
        "effect_summary": "Crop the foreground bbox, then tile the cropped region.",
        "train_inference_fn_name": "arc_resize_tile_canvas_v1.infer_resize_tile_hypotheses_v1",
        "executor_fn_name": "arc_resize_tile_canvas_v1._tile_grid",
        "inverse_or_comparable_relation": "crop_foreground_bbox",
        "rejection_reasons": ("no_foreground", "invalid_repeat_factor", "pattern_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "repeat_rows", "repeat_cols", "train_fit"),
    },
    {
        "primitive_name": "count_objects_to_line",
        "family": "count_quantity",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("foreground_objects_countable", "line_orientation_known"),
        "effect_summary": "Emit a line whose length equals the foreground object count.",
        "train_inference_fn_name": "arc_count_quantity_relations_v1.infer_count_quantity_hypotheses_v1",
        "executor_fn_name": "arc_count_quantity_relations_v1._line_grid",
        "inverse_or_comparable_relation": "object_count_to_square",
        "rejection_reasons": ("ambiguous_background", "output_not_line", "count_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "object_count", "line_color", "train_fit"),
    },
    {
        "primitive_name": "foreground_cell_count_to_line",
        "family": "count_quantity",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("foreground_cells_countable", "line_orientation_known"),
        "effect_summary": "Emit a line whose length equals the foreground cell count.",
        "train_inference_fn_name": "arc_count_quantity_relations_v1.infer_count_quantity_hypotheses_v1",
        "executor_fn_name": "arc_count_quantity_relations_v1._line_grid",
        "inverse_or_comparable_relation": "count_objects_to_line",
        "rejection_reasons": ("ambiguous_background", "output_not_line", "count_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "foreground_cell_count", "line_color", "train_fit"),
    },
    {
        "primitive_name": "unique_color_count_to_line",
        "family": "count_quantity",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("foreground_colors_countable", "line_orientation_known"),
        "effect_summary": "Emit a line whose length equals the number of unique foreground colors.",
        "train_inference_fn_name": "arc_count_quantity_relations_v1.infer_count_quantity_hypotheses_v1",
        "executor_fn_name": "arc_count_quantity_relations_v1._line_grid",
        "inverse_or_comparable_relation": "count_objects_to_line",
        "rejection_reasons": ("ambiguous_background", "output_not_line", "count_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "unique_color_count", "line_color", "train_fit"),
    },
    {
        "primitive_name": "object_count_to_square",
        "family": "count_quantity",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("foreground_objects_countable", "square_size_known"),
        "effect_summary": "Emit a filled square whose size equals the foreground object count.",
        "train_inference_fn_name": "arc_count_quantity_relations_v1.infer_count_quantity_hypotheses_v1",
        "executor_fn_name": "arc_count_quantity_relations_v1._filled_square",
        "inverse_or_comparable_relation": "count_objects_to_line",
        "rejection_reasons": ("ambiguous_background", "output_not_square", "count_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "object_count", "fill_color", "train_fit"),
    },
    {
        "primitive_name": "select_most_frequent_foreground_color",
        "family": "count_quantity",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("foreground_color_frequency_known",),
        "effect_summary": "Select or mask the most frequent foreground color.",
        "train_inference_fn_name": "arc_count_quantity_relations_v1.infer_count_quantity_hypotheses_v1",
        "executor_fn_name": "arc_count_quantity_relations_v1._mask_color",
        "inverse_or_comparable_relation": "recolor_foreground",
        "rejection_reasons": ("ambiguous_background", "frequency_tie", "color_selection_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "selected_color", "output_mode", "train_fit"),
    },
    {
        "primitive_name": "select_largest_object",
        "family": "count_quantity",
        "input_type": "grid",
        "output_type": "grid",
        "preconditions": ("largest_object_unique",),
        "effect_summary": "Crop the largest object by size.",
        "train_inference_fn_name": "arc_count_quantity_relations_v1.infer_count_quantity_hypotheses_v1",
        "executor_fn_name": "arc_count_quantity_relations_v1.crop_to_largest_object_bbox_v1",
        "inverse_or_comparable_relation": "crop_largest_object",
        "rejection_reasons": ("ambiguous_background", "largest_object_ambiguous", "crop_mismatch"),
        "trace_safe_metadata": ("primitive_name", "family", "largest_object_size", "train_fit"),
    },
)


def build_arc_primitive_registry_v1() -> PrimitiveRegistry:
    registry = PrimitiveRegistry()
    for spec in _BUILTIN_DESCRIPTOR_SPECS_V1:
        registry.register(PrimitiveDescriptor(**spec))
    return registry


__all__ = [
    "PrimitiveDescriptor",
    "PrimitiveRegistry",
    "REQUIRED_DESCRIPTOR_FIELDS_V1",
    "UNSAFE_TRACE_METADATA_LABELS_V1",
    "build_arc_primitive_registry_v1",
]
