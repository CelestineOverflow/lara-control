
from typing import List, Dict
import numpy as np
from space import Pose, Vector3, Quaternion, Euler
from scipy.spatial.transform import Rotation as R

class Tray:
    def __init__(
        self,
        pose: Pose,
        offsets: Vector3 = Vector3(-0.016, 0.014605, 0.0),
        rows: int = 3,
        cols: int = 3,
    ):
        self.pose = pose  
        self.original_orientation = self.pose.orientation
        # rotate the quat by 30 deg in x axis
        offset = Euler(0.0, 0.0, Euler.to_rad(24)).to_quaternion()
        self.pose.orientation = self.pose.orientation * offset
        self.offsets = offsets
        self.rows = rows
        self.cols = cols

    def to_dict(self):
        return {
            'pose': {
                'position': {
                    'x': self.pose.position.x,
                    'y': self.pose.position.y,
                    'z': self.pose.position.z,
                },
                'orientation': {
                    'x': self.original_orientation.x,
                    'y': self.original_orientation.y,
                    'z': self.original_orientation.z,
                    'w': self.original_orientation.w,
                }
            },
            'offsets': {
                'x': self.offsets.x,
                'y': self.offsets.y,
                'z': self.offsets.z,
            },
            'rows': self.rows,
            'cols': self.cols,
        }

    @classmethod
    def from_dict(cls, data):
        pose = Pose(
            Vector3(data['pose']['position']['x'], data['pose']['position']['y'], data['pose']['position']['z']),
            Quaternion(data['pose']['orientation']['x'], data['pose']['orientation']['y'], data['pose']['orientation']['z'], data['pose']['orientation']['w'])
        )
        offsets = Vector3(
            data['offsets']['x'],
            data['offsets']['y'],
            data['offsets']['z']
        )
        rows = data['rows']
        cols = data['cols']
        return cls(pose, offsets, rows, cols)



    def get_cell_position(self, row: int, col: int) -> Pose:
        # Check if row and col are within the bounds
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            raise ValueError(f"Invalid row or column: {row}, {col} for tray with {self.rows} rows and {self.cols} columns")
        _cell_local_position = Vector3(self.offsets.x * col, self.offsets.y * row, self.offsets.z)
        _cell_local_position = _cell_local_position @ self.pose.orientation.to_matrix()
        _new_position = self.pose.position + _cell_local_position
        return Pose(_new_position, self.pose.orientation)

    def get_cell_robot_orientation(self, row: int, col: int) -> Pose:
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            raise ValueError(f"Invalid row or column: {row}, {col} for tray with {self.rows} rows and {self.cols} columns")
        
        # Compute cell local position
        _cell_local_position = Vector3(self.offsets.x * col, self.offsets.y * row, 0)
        # Rotate local position by tray's orientation
        _cell_local_position = _cell_local_position @ self.pose.orientation.to_matrix()
        # Compute new global position
        _new_position = self.pose.position + _cell_local_position
        return Pose(_new_position, self.original_orientation)


    def get_cell_positions(self) -> List[Pose]:
        positions = []
        for row in range(self.rows):
            for col in range(self.cols):
                positions.append(self.get_cell_position(row, col))
        return positions
    