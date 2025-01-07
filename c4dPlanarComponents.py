import c4d
import numpy as np

# -----------------------------------------------------------------------------------
# Linear Algebra Operations
# -----------------------------------------------------------------------------------

# Returns vertex coordinates as a numpy array
def Vtx3DtoNpArray(obj, points):
    A = np.empty((0, 3), float)
    for point in points:
        p = obj.GetPoint(point)
        A = np.append(A, np.array([[p.x, p.y, p.z]]), axis=0)
    return A

# Normalizes vector a
def normalized(a, axis=-1, order=2):
    l2 = np.atleast_1d(np.linalg.norm(a, order, axis))
    l2[l2 == 0] = 1
    return a / np.expand_dims(l2, axis)

# Returns the normal of the plane fitted to points M
def fitPlaneEigen(M):
    covariant = np.cov(M.T)
    eigenValues, eigenVectors = np.linalg.eig(covariant)
    idx = eigenValues.argsort()
    eigenVectors = eigenVectors[:, idx]
    return eigenVectors[:, 0]

# Returns the average point of points M
def average(M):
    return np.mean(M, axis=0)

# -----------------------------------------------------------------------------------
# Align Vertices to Plane Function
# -----------------------------------------------------------------------------------

def alignVtxToPlane():
    doc = c4d.documents.GetActiveDocument()
    obj = doc.GetActiveObject()
    
    if obj is None or not isinstance(obj, c4d.PolygonObject):
        c4d.gui.MessageDialog('Please select a polygon object.')
        return
    
    sel = obj.GetPointS()
    if sel.GetCount() < 3:
        c4d.gui.MessageDialog('Please select at least 3 vertices.')
        return
    
    points = [i for i in range(obj.GetPointCount()) if sel.IsSelected(i)]
    vtxCoor = Vtx3DtoNpArray(obj, points)
    planeNorm = fitPlaneEigen(vtxCoor)
    avgPoint = average(vtxCoor)

    # Start undo recording
    doc.StartUndo()
    
    for i, point_idx in enumerate(points):
        # Record undo for each point
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
        
        # Project each point onto the plane
        p = vtxCoor[i] - np.inner((vtxCoor[i] - avgPoint), planeNorm) * planeNorm
        obj.SetPoint(point_idx, c4d.Vector(p[0], p[1], p[2]))

    # End undo recording and update document
    doc.EndUndo()
    obj.Message(c4d.MSG_UPDATE)
    c4d.EventAdd()

# Execute function
alignVtxToPlane()
