import json
from scipy.spatial.transform import Rotation as R
from typing import List, Tuple
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
   #Rotate vector by quaternion
   def rotate(self, q: 'Quaternion') -> 'Vector3':
        return q.rotate_vector(self)
   

class Vector2:
   def __init__(self, x: float, y: float):
       self.x = x
       self.y = y
   def to_list(self) -> List[float]:
       return [self.x, self.y]
   def __str__(self):
       return f"({self.x}, {self.y})"
   
   def rotate(self, angle: float) -> 'Vector2':
        """
            Rotate the vector by the given angle (in radians).
        """
        cosA = np.cos(angle)
        sinA = np.sin(angle)
        x = self.x * cosA - self.y * sinA
        y = self.x * sinA + self.y * cosA
        return Vector2(x, y)   
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
    def to_matrix(self) -> 'Matrix3':
        cosA = np.cos(self.x)
        sinA = np.sin(self.x)
        cosB = np.cos(self.y)
        sinB = np.sin(self.y)
        cosC = np.cos(self.z)
        sinC = np.sin(self.z)
        Rx = [
            [1, 0, 0],
            [0, cosA, -sinA],
            [0, sinA, cosA],
        ]
        Ry = [
            [cosB, 0, sinB],
            [0, 1, 0],
            [-sinB, 0, cosB],
        ]
        Rz = [
            [cosC, -sinC, 0],
            [sinC, cosC, 0],
            [0, 0, 1],
        ]
        Rzy = np.matmul(Rz, Ry)
        R = np.matmul(Rzy, Rx)
        return Matrix3(R)
    def to_dict(self, degrees=False) -> dict:
        if degrees:
            return {
                "x": self.to_deg(self.x),
                "y": self.to_deg(self.y),
                "z": self.to_deg(self.z)
            }
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z
        }
           
class Quaternion:
   def __init__(self, x: float, y: float, z: float, w: float):
       self.x = x  
       self.y = y  
       self.z = z  
       self.w = w 
   def to_list(self) -> List[float]:
       return [self.x, self.y, self.z, self.w]
   def __str__(self):
       return f"({self.x}, {self.y}, {self.z}, {self.w})"
   def to_euler(self, order='xyz') -> Euler:
       '''
       Returns the Euler angles (in radians) corresponding to this quaternion.
       '''
       r = R.from_quat(self.to_list())
       return Euler(*r.as_euler(order))

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
    
    def multiplyMatrixAndTransVector(self, vector: Vector3) -> Vector3:
        return self @ vector
    



class PoseCartesian():
    position: Vector3
    orientation: Euler
    def __init__(self, position: Vector3, orientation: Euler):
        self.position = position
        self.orientation = orientation

    def to_dict(self) -> dict:
        return {
            "position": self.position.to_list(),
            "orientation": self.orientation.to_list()
        }
    @staticmethod
    def from_dict(data) -> 'PoseCartesian':
        return PoseCartesian(
            position=Vector3(*data['position']),
            orientation=Euler(*data['orientation'])
        )
    

class Matrix4:
   """
   4x4 homogeneous transformation matrix.
   data is stored internally as a list of lists (4x4), consistent with Matrix3 style.
   """
   def __init__(self, data: List[List[float]] = None):
       if data is None:
           # default to identity
           self.data = [
               [1.0, 0.0, 0.0, 0.0],
               [0.0, 1.0, 0.0, 0.0],
               [0.0, 0.0, 1.0, 0.0],
               [0.0, 0.0, 0.0, 1.0]
           ]
       else:
           # Expecting a 4x4 list of lists
           if len(data) != 4 or any(len(row) != 4 for row in data):
               raise ValueError("Matrix4 data must be 4x4.")
           self.data = data
   def __str__(self):
       return "\n".join(str(row) for row in self.data)
   def to_list(self) -> List[List[float]]:
       return self.data
   @staticmethod
   def identity() -> 'Matrix4':
       return Matrix4()
   @staticmethod
   def from_quaternion_translation(q: 'Quaternion', t: 'Vector3') -> 'Matrix4':
       """
       Build a 4x4 homogeneous transform from a Quaternion + translation vector.
       """
       # 1) Convert quaternion to 3x3 rotation
       rot_mat_3x3 = R.from_quat(q.to_list()).as_matrix()  # shape (3,3)
       # 2) Construct the 4x4
       data = [[0.0]*4 for _ in range(4)]
       # fill rotation
       for i in range(3):
           for j in range(3):
               data[i][j] = rot_mat_3x3[i][j]
       # fill translation
       data[0][3] = t.x
       data[1][3] = t.y
       data[2][3] = t.z
       # last row
       data[3][0] = 0.0
       data[3][1] = 0.0
       data[3][2] = 0.0
       data[3][3] = 1.0
       return Matrix4(data)
   @staticmethod
   def from_pose(pose: 'Pose') -> 'Matrix4':
       """
       Convenience constructor that takes your Pose (position + orientation)
       and returns the corresponding Matrix4.
       """
       return Matrix4.from_quaternion_translation(pose.orientation, pose.position)
   @staticmethod
   def from_quaternion(q: 'Quaternion') -> 'Matrix4':
         """
         Construct a 4x4 homogeneous transform from a quaternion.
         """
         return Matrix4.from_quaternion_translation(q, Vector3(0.0, 0.0, 0.0))
   def to_quaternion_translation(self) -> Tuple[Quaternion, Vector3]:
       """
       Extract the rotation (as a Quaternion) and translation (as Vector3)
       from this homogeneous matrix.
       """
       # rotation = top-left 3x3
       rot_3x3 = np.array([row[:3] for row in self.data[:3]])  # shape (3,3)
       # translation = top-right column
       t = Vector3(self.data[0][3], self.data[1][3], self.data[2][3])
       # Convert 3x3 rotation to quaternion
       q_arr = R.from_matrix(rot_3x3).as_quat()  # [x, y, z, w]
       q = Quaternion(q_arr[0], q_arr[1], q_arr[2], q_arr[3])
       return (q, t)
   def to_pose(self) -> 'Pose':
       """
       Convert this Matrix4 into a Pose (position + orientation).
       """
       q, t = self.to_quaternion_translation()
       return Pose(t, q)
   def inverse(self) -> 'Matrix4':
       """
       Invert this 4x4 homogeneous transform.
       For a 4x4 of the form [R | t; 0 1], the inverse is [R^T | -R^T t; 0 1].
       """
       # We can do this manually or via numpy.linalg.inv
       mat = np.array(self.data, dtype=np.float64)
       inv_mat = np.linalg.inv(mat)
       return Matrix4(inv_mat.tolist())
   

   def __mul__(self, other):
       """
       Overload the * operator for:
         - Matrix4 * Matrix4 -> composition of transforms
         - Matrix4 * Vector3 -> transform a 3D point in homogeneous coords
       """
       if isinstance(other, Matrix4):
           # 4x4 x 4x4
           a = np.array(self.data, dtype=np.float64)
           b = np.array(other.data, dtype=np.float64)
           c = np.matmul(a, b)
           return Matrix4(c.tolist())
       elif isinstance(other, Vector3):
           # 4x4 x 3D vector (assume w=1)
           a = np.array(self.data, dtype=np.float64)
           v = np.array([other.x, other.y, other.z, 1.0], dtype=np.float64)
           res = a @ v
           # result is [x', y', z', w']
           # we usually do res[0:3] / res[3] if w' != 1.0
           if abs(res[3]) > 1e-8:
               return Vector3(res[0]/res[3], res[1]/res[3], res[2]/res[3])
           else:
               return Vector3(res[0], res[1], res[2])
       else:
           raise TypeError("Unsupported multiplication. Must be Matrix4 or Vector3.")
   def transform_vector(self, v: 'Vector3') -> 'Vector3':
       """
       Explicit function to transform a Vector3 by this matrix in homogeneous coords.
       Same as using the * operator if you prefer that syntax.
       """
       return self * v
   
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
    
    def to_Cartesian(self) -> PoseCartesian:
        return PoseCartesian(self.position, self.orientation.to_euler())
    
    def __str__(self):
        return f"Position: {self.position}, Orientation: {self.orientation}"