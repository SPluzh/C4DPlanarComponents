# -----------------------------------------------------------------------------------
# Planarizes selected vertices to their best-fit plane.
# Version: 1.3
# 
# Changes in v1.3:
# - Added support for polygon and edge selection (converts to vertices automatically)
# - Works with vertices, edges, polygons selection modes
#
# Changes in v1.2:
# - Only moves vertices that are OFF the plane (selective displacement)
# - Detects vertices already on plane and uses them to define it (preserves majority)
# - Shows non-blocking notification in status bar with moved vertex count and plane orientation
# - Distance threshold (1e-3) determines which vertices need alignment
#
# Changes in v1.1:
# - Added snap_normal_to_axis: snaps plane normal to X/Y/Z if within 0.1° threshold
# - Improved performance: Vtx3DtoNpArray uses list comprehension instead of np.append
# - Better undo handling
# -----------------------------------------------------------------------------------

import c4d
import numpy as np

# -----------------------------------------------------------------------------------
# Linear Algebra Operations
# -----------------------------------------------------------------------------------

def Vtx3DtoNpArray(obj, points):
    """Returns vertex coordinates as a numpy array of shape [n, 3]"""
    return np.array([[obj.GetPoint(p).x, obj.GetPoint(p).y, obj.GetPoint(p).z] for p in points])

def normalized(v):
    """Returns the normalized version of a vector"""
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def fitPlaneEigen(M):
    """Returns the normal of the best-fit plane for a set of points"""
    cov = np.cov(M.T)
    eigvals, eigvecs = np.linalg.eig(cov)
    idx = np.argmin(eigvals)
    return eigvecs[:, idx]

def average(M):
    """Returns the average point (centroid) of a set of points"""
    return np.mean(M, axis=0)

def snap_normal_to_axis(normal, threshold_deg=0.1):
    """
    If the normal is within threshold_deg of a world axis (X/Y/Z),
    snaps it to that axis.
    """
    threshold_rad = np.deg2rad(threshold_deg)
    world_axes = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0])
    ]
    
    n = normalized(normal)
    for axis in world_axes:
        dot = np.dot(n, axis)
        angle = np.arccos(np.clip(abs(dot), -1.0, 1.0))
        if angle < threshold_rad:
            return axis * np.sign(dot)
    return n

def get_selected_points(obj):
    """Returns list of selected point indices from points, edges, or polygons"""
    point_sel = obj.GetPointS()
    edge_sel = obj.GetEdgeS()
    poly_sel = obj.GetPolygonS()
    
    points_set = set()
    
    # Get points from point selection
    if point_sel.GetCount() > 0:
        for i in range(obj.GetPointCount()):
            if point_sel.IsSelected(i):
                points_set.add(i)
    
    # Get points from edge selection
    if edge_sel.GetCount() > 0:
        for i in range(obj.GetPolygonCount()):
            poly = obj.GetPolygon(i)
            edges = [
                (poly.a, poly.b),
                (poly.b, poly.c),
                (poly.c, poly.d if poly.c != poly.d else poly.a),
                (poly.d, poly.a) if poly.c != poly.d else None
            ]
            for edge_idx, edge in enumerate(edges):
                if edge and edge_sel.IsSelected(i * 4 + edge_idx):
                    points_set.add(edge[0])
                    points_set.add(edge[1])
    
    # Get points from polygon selection
    if poly_sel.GetCount() > 0:
        for i in range(obj.GetPolygonCount()):
            if poly_sel.IsSelected(i):
                poly = obj.GetPolygon(i)
                points_set.add(poly.a)
                points_set.add(poly.b)
                points_set.add(poly.c)
                if poly.c != poly.d:
                    points_set.add(poly.d)
    
    return list(points_set)

# -----------------------------------------------------------------------------------
# Align Vertices to Plane Function
# -----------------------------------------------------------------------------------

def alignVtxToPlane():
    doc = c4d.documents.GetActiveDocument()
    obj = doc.GetActiveObject()
    
    if obj is None or not isinstance(obj, c4d.PolygonObject):
        c4d.StatusSetText('Please select a polygon object.')
        return
    
    # Get selected points from any selection mode
    points = get_selected_points(obj)
    
    if len(points) < 3:
        c4d.StatusSetText('Please select at least 3 vertices, 1 edge, or 1 polygon.')
        return
    
    # Compute initial best-fit plane
    vtxCoor = Vtx3DtoNpArray(obj, points)
    avg = average(vtxCoor)
    normal = fitPlaneEigen(vtxCoor)
    normal = snap_normal_to_axis(normal)
    
    # Find vertices already on the plane
    distance_threshold = 1e-3
    distances = [abs(np.dot(vtxCoor[i] - avg, normal)) for i in range(len(points))]
    on_plane_indices = [i for i, d in enumerate(distances) if d <= distance_threshold]
    
    # If most vertices are already on a plane, use them to define the plane
    if len(on_plane_indices) >= 3:
        plane_points = vtxCoor[on_plane_indices]
        avg = average(plane_points)
        normal = fitPlaneEigen(plane_points)
        normal = snap_normal_to_axis(normal)

    # Start undo recording
    doc.StartUndo()
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
    
    # Move only vertices that are off the plane
    moved_count = 0
    for i, point_idx in enumerate(points):
        vec = vtxCoor[i] - avg
        distance_to_plane = abs(np.dot(vec, normal))
        
        if distance_to_plane > distance_threshold:
            proj = np.dot(vec, normal) * normal
            new_pos = vtxCoor[i] - proj
            obj.SetPoint(point_idx, c4d.Vector(new_pos[0], new_pos[1], new_pos[2]))
            moved_count += 1

    # End undo recording and update document
    doc.EndUndo()
    obj.Message(c4d.MSG_UPDATE)
    c4d.EventAdd()
    
    # Show non-blocking notification in status bar
    axis_names = {
        (1.0, 0.0, 0.0): "X", (-1.0, 0.0, 0.0): "X",
        (0.0, 1.0, 0.0): "Y", (0.0, -1.0, 0.0): "Y",
        (0.0, 0.0, 1.0): "Z", (0.0, 0.0, -1.0): "Z"
    }
    normal_tuple = tuple(normal)
    axis_info = axis_names.get(normal_tuple, "custom")
    
    message = 'Aligned {count} vertices to plane (normal: {axis})'.format(
        count=moved_count,
        axis=axis_info
    )
    c4d.StatusSetText(message)

# Execute function
alignVtxToPlane()
