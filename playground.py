import numpy as np
from scipy.sparse import coo_matrix, dok_matrix
import scipy.linalg as scilinalg
from scipy.sparse.linalg import spilu, svds

import meshlib
from discrete_mesh import DiscreteMesh
from render import get_markers, BrowserVisualizer

source = meshlib.Mesh.from_file_obj("models/lowpoly_cat/cat_reference.obj")
target = meshlib.Mesh.from_file_obj("models/lowpoly_dog/dog_reference.obj")
markers = get_markers()  # cat, dog

source_vert = np.concatenate((source.vertices, DiscreteMesh.calc_triangle_norm(source)))
target_vert = np.concatenate((target.vertices, DiscreteMesh.calc_triangle_norm(target)))

v1, v2, v3 = source.vertices[source.faces].transpose((1, 0, 2))
a = v2 - v1
b = v3 - v1
tmp = np.cross(a, b)
c = tmp / np.sqrt(np.linalg.norm(tmp))
v4 = v1 + c
Vs = np.transpose((a, b, c), axes=(1, 0, 2))
invVs = np.linalg.inv(Vs)

# As = dok_matrix(
#     (
#         len(source.faces) + sum(len(np.where(source.faces == f)[0]) - 1 for f in source.faces),
#         # + len(source.vertices)
#         len(source_vert_flat)
#     ),
#     dtype=np.float
# )
# Bs = np.zeros(len(source_vert_flat))


# def set_vertex_index(row: int, index: int, mat: np.ndarray):
#     assert mat.ndim == 2 and mat.shape[1] == 3
#     vert_index = index * 3
#     for i in range(3):
#         for j in range(3):
#             As[row + i, vert_index + j * 3 + i] = mat[i, j]

new_v4_indices = np.arange(len(source.vertices), len(source.vertices) + len(v4))
interm_faces = np.concatenate((source.faces, new_v4_indices.reshape((-1, 1))), axis=1)
interm_vertices = np.concatenate((source.vertices, v4), axis=0)

print("TEST")

"""
V = [v2-v1, v3-v1, v4-v1]

wij = iv1 x2 - iv1 x1 + iv2 x3 - iv2 x1 + iv3 x4 - iv3 x1

wij = (-iv1 -iv2 - iv3) x1  +  iv1 x2  +  iv2 x3 + iv3 x4
"""

vertices_length_flat = len(interm_vertices) * 3

# Smoothness
AEs = dok_matrix(
    (sum(len(np.where(interm_faces == f)[0]) - 1 for f in interm_faces) * 9, vertices_length_flat),
    dtype=np.float
)

# Identity
AEi = dok_matrix(
    (len(interm_faces) * 9, vertices_length_flat),
    dtype=np.float
)

b = np.array([1, 0, 0, 0, 1, 0, 0, 0, 1] * len(interm_faces))

# row = 0
for index, (f, invV) in enumerate(zip(interm_faces, invVs)):  # type: int, (np.ndarray, np.ndarray)

    # Index
    i0 = f[0]
    i1 = f[1]
    i2 = f[2]
    i3 = f[3]

    kleinA = np.zeros(shape=(9, 12))
    for i in range(3):
        for j in range(3):
            kleinA[i * 3 + j, i] = - (invV[0, j] + invV[1, j] + invV[2, j])
            kleinA[i * 3 + j, i + 3] = invV[0, j]
            kleinA[i * 3 + j, i + 6] = invV[1, j]
            kleinA[i * 3 + j, i + 9] = invV[2, j]

    AEi[index * 9: index * 9 + 9, i0:i0 + 3] = kleinA[:, 0:3]
    AEi[index * 9: index * 9 + 9, i1:i1 + 3] = kleinA[:, 3:6]
    AEi[index * 9: index * 9 + 9, i2:i2 + 3] = kleinA[:, 6:9]
    AEi[index * 9: index * 9 + 9, i3:i3 + 3] = kleinA[:, 9:12]

for mark_src_i, mark_dest_i in markers:
    i = mark_src_i * 3
    valueB = np.matmul(AEi[:, i:i + 3], target.vertices[mark_dest_i].reshape((-1, 1)))
    b -= valueB
    AEi[:, i:i + 3] = 0

AEi = AEi.tocsc()

AEiT = AEi.transpose()
wow = AEiT.__matmul__(AEi)

AtB = AEiT * b

u, s, vt = svds(wow)
sinv = np.identity(len(s)) / s
psInv = np.matmul(np.matmul(vt.transpose(), sinv), u.transpose())
xschlange = np.matmul(psInv, AtB)

final_mesh = meshlib.Mesh(
    vertices=np.transpose((xschlange[0::4], xschlange[1::4], xschlange[2::4])),
    faces=source.faces
)

vis = BrowserVisualizer()
vis.addMesh(final_mesh)
vis.show()

# psInv = spilu(vt * sinv * u.transpose())
# source_vert_flat = source_vert.flatten()
# target_vert_flat = target_vert.flatten()


# adjecent = np.where(source.faces == f)[0]
# for adj in adjecent:
#     if adj != index:
#         set_vertex_index(row, index, invV.transpose())
#         set_vertex_index(row, adj, -invVs[adj].transpose())
#         row += 1
#
# np.transpose(invV)
