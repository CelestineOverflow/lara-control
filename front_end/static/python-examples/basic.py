import arm_api

cells = arm_api.Cell.generate_cells((0, 0), (8, 8))

@arm_api.labhandler_sequence
def testers_code():
    print(f"starting test of cell at coordinates {cell.x}, {cell.y}")
    # This function will be called for each cell in the grid
    # it will be called on every cell
    # you can define your own logic here
    # down forget to turn on and off the power supplies!!
    
# Running tests over cells
for cell in cells:
    testers_code(cell)

