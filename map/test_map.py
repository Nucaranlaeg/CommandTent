import pytest
from map.map import Map, terrain_types
from map.terrain import MAX_SIGHT

@pytest.fixture
def test_map():
	# Create a 10x10 map for testing
	return Map(10, 10)

def test_find_cell_valid(test_map):
	# Test valid cell locations
	cell = test_map.find_cell("A1")
	assert cell is not None
	assert any(isinstance(cell, terrain) for terrain in terrain_types)

	cell = test_map.find_cell("J10")
	assert cell is not None
	assert any(isinstance(cell, terrain) for terrain in terrain_types)

def test_find_cell_invalid(test_map):
	# Test invalid cell locations
	with pytest.raises(ValueError):
		test_map.find_cell("Z99")

	with pytest.raises(ValueError):
		test_map.find_cell("Invalid")

def test_find_cell_edge_cases(test_map):
	# Test edge cases
	with pytest.raises(ValueError):
		test_map.find_cell("A0")  # Column 0 is invalid

	with pytest.raises(ValueError):
		test_map.find_cell("K1")  # Row K is out of bounds

	with pytest.raises(ValueError):
		test_map.find_cell("")  # Empty string is invalid

	with pytest.raises(ValueError):
		test_map.find_cell("A11")  # Column out of bounds

def test_line_cells(test_map):
	# Test diagonal line from (0, 0) to (4, 4)
	line = list(test_map.line_cells(0, 0, 4, 4))
	assert len(line) == 5  # Diagonal line should have 5 cells
	assert line[0] == test_map.map[0][0]  # Start cell
	assert line[-1] == test_map.map[4][4]  # End cell

	# Test vertical line from (0, 0) to (0, 4)
	line = list(test_map.line_cells(0, 0, 0, 4))
	assert len(line) == 5  # Vertical line should have 5 cells
	assert line[0] == test_map.map[0][0]  # Start cell
	assert line[-1] == test_map.map[4][0]  # End cell

	# Test horizontal line from (0, 0) to (4, 0)
	line = list(test_map.line_cells(0, 0, 4, 0))
	assert len(line) == 5  # Horizontal line should have 5 cells
	assert line[0] == test_map.map[0][0]  # Start cell
	assert line[-1] == test_map.map[0][4]  # End cell

	# Test single-point line (start and end are the same)
	line = list(test_map.line_cells(2, 2, 2, 2))
	assert len(line) == 1  # One cell should be yielded for a single-point line

def test_determine_sight(test_map):
	# Mock terrain with no vision blocking
	for row in test_map.map:
		for cell in row:
			cell.vision_block = 0

	# Test full sightline from (0, 0) to (4, 4)
	sight = test_map.determine_sight(source="A1", target="E5")
	assert sight == MAX_SIGHT  # MAX_SIGHT should remain unchanged

	# Add vision blocking to some cells
	test_map.map[1][1].vision_block = 3
	test_map.map[2][2].vision_block = 4

	# Test sightline with vision blocking
	sight = test_map.determine_sight(source="A1", target="E5")
	assert sight == MAX_SIGHT - 3 - 4  # Sight should be reduced by the blocking cells

	# Test completely blocked sightline
	test_map.map[3][3].vision_block = MAX_SIGHT - 6
	sight = test_map.determine_sight(source="A1", target="E5")
	assert sight == 0  # Sightline should be completely blocked
