"""
Reading order algorithms for content blocks.

The XY-Cut algorithm recursively partitions blocks to determine
natural reading order for multi-column layouts.
"""

from __future__ import annotations
from typing import List, Tuple, TypeVar, Callable
from dataclasses import dataclass

from ocr_perfect.geometry.bboxes import BBox


T = TypeVar("T")


@dataclass
class BlockWithBBox:
    """Wrapper to associate any object with a bounding box."""
    item: object
    bbox: BBox


def get_bbox_from_block(block: object) -> BBox:
    """
    Extract BBox from a block object.

    Supports objects with 'bbox' attribute (as list or BBox).
    """
    if hasattr(block, "bbox"):
        bbox_val = block.bbox
        if isinstance(bbox_val, BBox):
            return bbox_val
        elif isinstance(bbox_val, (list, tuple)) and len(bbox_val) == 4:
            return BBox.from_list(list(bbox_val))
    raise ValueError(f"Cannot extract bbox from {type(block)}")


def sort_blocks_xy_cut(
    blocks: List[T],
    min_col_gap: float = 5.0,
    min_row_gap: float = 2.0,
    bbox_getter: Callable[[T], BBox] = get_bbox_from_block,
) -> List[T]:
    """
    Sort blocks using the XY-Cut algorithm for reading order.

    The XY-Cut algorithm recursively partitions blocks:
    1. Try to find a vertical gap (column separator)
    2. If found, recursively process left and right partitions
    3. If not, try to find a horizontal gap (row separator)
    4. If found, recursively process top and bottom partitions
    5. If neither found, sort by Y then X

    Args:
        blocks: List of block objects to sort
        min_col_gap: Minimum gap width to consider a column separator
        min_row_gap: Minimum gap height to consider a row separator
        bbox_getter: Function to extract BBox from a block

    Returns:
        Sorted list of blocks in reading order
    """
    if len(blocks) <= 1:
        return blocks

    # Get bboxes for all blocks
    items = [(block, bbox_getter(block)) for block in blocks]

    # Recursively apply XY-Cut
    sorted_items = _xy_cut_recursive(items, min_col_gap, min_row_gap)

    return [item[0] for item in sorted_items]


def _xy_cut_recursive(
    items: List[Tuple[T, BBox]],
    min_col_gap: float,
    min_row_gap: float,
) -> List[Tuple[T, BBox]]:
    """Recursive XY-Cut implementation."""
    if len(items) <= 1:
        return items

    # Try vertical cut first (column detection)
    v_cut = _find_vertical_cut(items, min_col_gap)
    if v_cut is not None:
        left = [(item, bbox) for item, bbox in items if bbox.x2 <= v_cut]
        right = [(item, bbox) for item, bbox in items if bbox.x1 >= v_cut]

        # Handle items that span the cut
        spanning = [(item, bbox) for item, bbox in items
                    if bbox.x1 < v_cut < bbox.x2]

        left_sorted = _xy_cut_recursive(left, min_col_gap, min_row_gap)
        right_sorted = _xy_cut_recursive(right, min_col_gap, min_row_gap)
        spanning_sorted = sorted(spanning, key=lambda x: (x[1].y1, x[1].x1))

        return left_sorted + spanning_sorted + right_sorted

    # Try horizontal cut (row detection)
    h_cut = _find_horizontal_cut(items, min_row_gap)
    if h_cut is not None:
        top = [(item, bbox) for item, bbox in items if bbox.y2 <= h_cut]
        bottom = [(item, bbox) for item, bbox in items if bbox.y1 >= h_cut]

        # Handle items that span the cut
        spanning = [(item, bbox) for item, bbox in items
                    if bbox.y1 < h_cut < bbox.y2]

        top_sorted = _xy_cut_recursive(top, min_col_gap, min_row_gap)
        bottom_sorted = _xy_cut_recursive(bottom, min_col_gap, min_row_gap)
        spanning_sorted = sorted(spanning, key=lambda x: (x[1].y1, x[1].x1))

        return top_sorted + spanning_sorted + bottom_sorted

    # No cuts found - sort by Y then X
    return sorted(items, key=lambda x: (x[1].y1, x[1].x1))


def _find_vertical_cut(
    items: List[Tuple[T, BBox]],
    min_gap: float,
) -> float | None:
    """
    Find a vertical cutting line (for column separation).

    Returns the x-coordinate of the cut, or None if no suitable cut found.
    """
    if len(items) < 2:
        return None

    # Get all x-coordinates where blocks start or end
    events: List[Tuple[float, str]] = []
    for _, bbox in items:
        events.append((bbox.x1, "start"))
        events.append((bbox.x2, "end"))

    events.sort(key=lambda e: e[0])

    # Find gaps
    active_count = 0
    last_end = None
    best_gap = None
    best_gap_size = 0

    for x, event_type in events:
        if event_type == "end":
            active_count -= 1
            if active_count == 0:
                last_end = x
        else:  # start
            if last_end is not None and active_count == 0:
                gap_size = x - last_end
                if gap_size >= min_gap and gap_size > best_gap_size:
                    best_gap = (last_end + x) / 2
                    best_gap_size = gap_size
            active_count += 1

    return best_gap


def _find_horizontal_cut(
    items: List[Tuple[T, BBox]],
    min_gap: float,
) -> float | None:
    """
    Find a horizontal cutting line (for row separation).

    Returns the y-coordinate of the cut, or None if no suitable cut found.
    """
    if len(items) < 2:
        return None

    # Get all y-coordinates where blocks start or end
    events: List[Tuple[float, str]] = []
    for _, bbox in items:
        events.append((bbox.y1, "start"))
        events.append((bbox.y2, "end"))

    events.sort(key=lambda e: e[0])

    # Find gaps
    active_count = 0
    last_end = None
    best_gap = None
    best_gap_size = 0

    for y, event_type in events:
        if event_type == "end":
            active_count -= 1
            if active_count == 0:
                last_end = y
        else:  # start
            if last_end is not None and active_count == 0:
                gap_size = y - last_end
                if gap_size >= min_gap and gap_size > best_gap_size:
                    best_gap = (last_end + y) / 2
                    best_gap_size = gap_size
            active_count += 1

    return best_gap


def sort_blocks_simple(
    blocks: List[T],
    bbox_getter: Callable[[T], BBox] = get_bbox_from_block,
    y_tolerance: float = 5.0,
) -> List[T]:
    """
    Simple sorting by Y position then X position.

    Groups blocks with similar Y values and sorts left-to-right within groups.

    Args:
        blocks: List of block objects to sort
        bbox_getter: Function to extract BBox from a block
        y_tolerance: Tolerance for considering blocks on the same line

    Returns:
        Sorted list of blocks
    """
    if not blocks:
        return blocks

    # Get (block, bbox) pairs
    items = [(block, bbox_getter(block)) for block in blocks]

    # Sort by Y first
    items.sort(key=lambda x: x[1].y1)

    # Group by similar Y and sort each group by X
    result = []
    current_group = [items[0]]

    for item in items[1:]:
        # Check if this item is on the same "line" as the current group
        group_y = sum(i[1].y1 for i in current_group) / len(current_group)
        if abs(item[1].y1 - group_y) <= y_tolerance:
            current_group.append(item)
        else:
            # Sort current group by X and add to result
            current_group.sort(key=lambda x: x[1].x1)
            result.extend(current_group)
            current_group = [item]

    # Don't forget the last group
    current_group.sort(key=lambda x: x[1].x1)
    result.extend(current_group)

    return [item[0] for item in result]
