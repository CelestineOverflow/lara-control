import json
from scipy.spatial.transform import Rotation as R
from typing import List
import numpy as np



class Vector3:
   def __init__(self, x: float, y: float, z: float):
       self.x = x
       self.y = y
       self.z = z
   def to_list(self) -> List[float]:
       return [self.x, self.y, self.z]
   def __str__(self):
       return f"({self.x}, {self.y}, {self.z})"
   # Addition of two vectors
   def __add__(self, other: 'Vector3') -> 'Vector3':
       return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
   # Subtraction of two vectors
   def __sub__(self, other: 'Vector3') -> 'Vector3':
       return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
   # Scalar multiplication
   def __mul__(self, scalar: float) -> 'Vector3':
       return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
   def __rmul__(self, scalar: float) -> 'Vector3':
       return self.__mul__(scalar)
   # Scalar division
   def __truediv__(self, scalar: float) -> 'Vector3':
       return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)
   # Dot product
   def dot(self, other: 'Vector3') -> float:
       return self.x * other.x + self.y * other.y + self.z * other.z
   # Cross product
   def cross(self, other: 'Vector3') -> 'Vector3':
       return Vector3(
           self.y * other.z - self.z * other.y,
           self.z * other.x - self.x * other.z,
           self.x * other.y - self.y * other.x
       )
   
   def distance(self, other: 'Vector3') -> float:
        return np.linalg.norm(np.array(self.to_list()) - np.array(other.to_list()))
   
   def magnitude(self) -> float:
        return np.linalg.norm(self.to_list())
   
   # convert to threejs format  
   def to_threejs(self) -> List[float]:
         return [self.x, self.z, -self.y]
   
   def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z
        }
   def from_dict(data) -> 'Vector3':
        return Vector3(data['x'], data['y'], data['z'])
   
   # TypeError: unsupported operand type(s) for @: 'Vector3' and 'Matrix3'
   def __matmul__(self, other: 'Matrix3') -> 'Vector3':
    result = [0.0, 0.0, 0.0]
    for i in range(3):
        for j in range(3):
            result[i] += other.data[i][j] * self.to_list()[j]
    return Vector3(*result)
   



class Vector2:
   def __init__(self, x: float, y: float):
       self.x = x
       self.y = y
   def to_list(self) -> List[float]:
       return [self.x, self.y]
   def __str__(self):
       return f"({self.x}, {self.y})"
class Euler:
   def __init__(self, x: float, y: float, z: float):
       # Angles in radians
       self.x = x  # Rotation around X-axis
       self.y = y  # Rotation around Y-axis
       self.z = z  # Rotation around Z-axis
   def to_list(self) -> List[float]:
       return [self.x, self.y, self.z]
   def __str__(self):
       return f"({self.x}, {self.y}, {self.z})"
   def to_quaternion(self) -> 'Quaternion':
       q = R.from_euler('xyz', self.to_list()).as_quat()
       return Quaternion(*q)
   @staticmethod
   def to_rad(deg: float) -> float:
       return np.deg2rad(deg)
   @staticmethod
   def to_deg(rad: float) -> float:
       return np.rad2deg(rad)
   def __str__deg(self):
       x_deg = self.to_deg(self.x)
       y_deg = self.to_deg(self.y)
       z_deg = self.to_deg(self.z)
       return f"({x_deg}°, {y_deg}°, {z_deg}°)"
class Quaternion:
   def __init__(self, x: float, y: float, z: float, w: float):
       # Quaternion components
       self.x = x  # x-component
       self.y = y  # y-component
       self.z = z  # z-component
       self.w = w  # scalar component
   def to_list(self) -> List[float]:
       return [self.x, self.y, self.z, self.w]
   def __str__(self):
       return f"({self.x}, {self.y}, {self.z}, {self.w})"
   def to_euler(self, order='xyz', degrees=False) -> Euler:
       '''
       Returns the Euler angles (in radians) corresponding to this quaternion.
       '''
       r = R.from_quat(self.to_list())
       return Euler(*r.as_euler(order, degrees=degrees))

   def multiply(self, q: 'Quaternion') -> 'Quaternion':
       '''
       Multiplies this quaternion by another quaternion (self * q).
       '''
       r1 = R.from_quat(self.to_list())
       r2 = R.from_quat(q.to_list())
       r3 = r1 * r2
       q_new = r3.as_quat()
       return Quaternion(*q_new)
   def __mul__(self, other: 'Quaternion') -> 'Quaternion':
       '''
       Overloads the * operator for quaternion multiplication.
       '''
       return self.multiply(other)
   def conjugate(self) -> 'Quaternion':
       '''
       Returns the conjugate of the quaternion.
       '''
       return Quaternion(-self.x, -self.y, -self.z, self.w)
   def rotate_vector(self, v: Vector3) -> Vector3:
       '''
       Rotates the vector v by this quaternion.
       '''
       rot = R.from_quat(self.to_list())
       rotated_v = rot.apply(v.to_list())
       return Vector3(*rotated_v)
   def invert(self) -> 'Quaternion':
       '''
       Returns the inverse of the quaternion (for unit quaternions, inverse is the conjugate).
       '''
       return self.conjugate()
   @staticmethod
   def from_euler(euler: Euler) -> 'Quaternion':
       '''
       Creates a quaternion from Euler angles.
       '''
       return euler.to_quaternion()
   @staticmethod
   def identity() -> 'Quaternion':
       '''
       Returns the identity quaternion (no rotation).
       '''
       return Quaternion(0.0, 0.0, 0.0, 1.0)
   
   def clone(self) -> 'Quaternion':
       return Quaternion(self.x, self.y, self.z, self.w)
   
   def to_matrix(self) -> 'Matrix3':
       return Matrix3.from_quaternion(self)
   

   def to_threejs(self) -> List[float]:
         return [self.x, self.z, -self.y, self.w]
   
   def to_dict(self) -> dict:
         return {
              "x": self.x,
              "y": self.y,
              "z": self.z,
              "w": self.w
         }

class Matrix3:
    def __init__(self, data: List[List[float]]):
         self.data = data
    def __str__(self):
         return str(self.data)
    def __mul__(self, other: 'Matrix3') -> 'Matrix3':
         result = [[0.0 for _ in range(3)] for _ in range(3)]
         for i in range(3):
              for j in range(3):
                for k in range(3):
                     result[i][j] += self.data[i][k] * other.data[k][j]
         return Matrix3(result)
    def __matmul__(self, other: 'Vector3') -> Vector3:
         result = [0.0, 0.0, 0.0]
         for i in range(3):
              for j in range(3):
                result[i] += self.data[i][j] * other.to_list()[j]
         return Vector3(*result)
    def transpose(self) -> 'Matrix3':
        result = [[0.0 for _ in range(3)] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                result[i][j] = self.data[j][i]
        return Matrix3(result)
    def to_list(self) -> List[List[float]]:
        return self.data
    
    def to_quaternion(self) -> Quaternion:
        q = R.from_matrix(self.data).as_quat()
        return Quaternion(*q)
    @staticmethod
    def identity() -> 'Matrix3':
        return Matrix3([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    @staticmethod
    def from_quaternion(q: Quaternion) -> 'Matrix3':
        q = R.from_quat(q.to_list())
        return Matrix3(q.as_matrix())
    
    

class Pose():
    position: Vector3
    orientation: Quaternion
    def __init__(self, position: Vector3, orientation: Quaternion):
        self.position = position
        self.orientation = orientation

    def to_dict(self) -> dict:
        return {
            "position": self.position.to_list(),
            "orientation": self.orientation.to_list()
        }
    
    @staticmethod
    def from_json(data) -> 'Pose':
        return Pose(
            position=Vector3(*data['position']),
            orientation=Quaternion(*data['orientation'])
        )

class PoseCartesian():
    position: Vector3
    orientation: Euler
    def __init__(self, position: Vector3, orientation: Euler):
        self.position = position
        self.orientation = orientation