# -----------------------------------------------------------------------------------
# Planarizes selected vertices to their best-fit plane.
# Version: 1.5
#
# Changes in v1.5:
# - Restores original selection mode and selection after processing
# - If started in edge/polygon mode, converts back from points to original mode
#
# Changes in v1.4:
# - Converts edge/polygon selection to point selection mode automatically
# - Only works with current selection mode (not all modes simultaneously)
# - Selected edges or polygons are converted to point selection before processing
# - The object's selection mode is switched to points with correct selection
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

def get_original_selection(obj, mode):
    """Store original selection based on mode"""
    if mode == c4d.Medges:
        edge_sel = obj.GetEdgeS()
        selected_edges = []
        # Store all selected edge indices
        for poly_idx in range(obj.GetPolygonCount()):
            for edge_idx in range(4):
                if edge_sel.IsSelected(poly_idx * 4 + edge_idx):
                    selected_edges.append(poly_idx * 4 + edge_idx)
        return selected_edges
    
    elif mode == c4d.Mpolygons:
        poly_sel = obj.GetPolygonS()
        selected_polys = []
        for i in range(obj.GetPolygonCount()):
            if poly_sel.IsSelected(i):
                selected_polys.append(i)
        return selected_polys
    
    return None

def restore_original_selection(obj, doc, mode, original_selection):
    """Restore original selection and mode"""
    if mode == c4d.Medges and original_selection is not None:
        # Clear all selections
        obj.GetPointS().DeselectAll()
        obj.GetEdgeS().DeselectAll()
        obj.GetPolygonS().DeselectAll()
        
        # Restore edge selection
        edge_sel = obj.GetEdgeS()
        for edge_idx in original_selection:
            edge_sel.Select(edge_idx)
        
        # Switch back to edge mode
        doc.SetMode(c4d.Medges)
    
    elif mode == c4d.Mpolygons and original_selection is not None:
        # Clear all selections
        obj.GetPointS().DeselectAll()
        obj.GetEdgeS().DeselectAll()
        obj.GetPolygonS().DeselectAll()
        
        # Restore polygon selection
        poly_sel = obj.GetPolygonS()
        for poly_idx in original_selection:
            poly_sel.Select(poly_idx)
        
        # Switch back to polygon mode
        doc.SetMode(c4d.Mpolygons)
    
    # If mode was points, do nothing - selection is already correct

def get_selected_points_and_convert(obj, doc):
    """
    Returns list of selected point indices based on CURRENT selection mode only.
    Converts edge/polygon selection to point selection mode in Cinema 4D.
    """
    # Get current mode
    mode = doc.GetMode()
    
    point_sel = obj.GetPointS()
    edge_sel = obj.GetEdgeS()
    poly_sel = obj.GetPolygonS()
    
    points_set = set()
    needs_conversion = False
    
    # Work only with current mode
    if mode == c4d.Mpoints:
        # Point mode - get selected points
        for i in range(obj.GetPointCount()):
            if point_sel.IsSelected(i):
                points_set.add(i)
    
    elif mode == c4d.Medges:
        # Edge mode - convert edges to points
        needs_conversion = True
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
    
    elif mode == c4d.Mpolygons:
        # Polygon mode - convert polygons to points
        needs_conversion = True
        for i in range(obj.GetPolygonCount()):
            if poly_sel.IsSelected(i):
                poly = obj.GetPolygon(i)
                points_set.add(poly.a)
                points_set.add(poly.b)
                points_set.add(poly.c)
                if poly.c != poly.d:
                    points_set.add(poly.d)
    
    points_list = list(points_set)
    
    # Convert selection to points if we were in edge or polygon mode
    if needs_conversion and len(points_list) > 0:
        # Clear all selections
        point_sel.DeselectAll()
        edge_sel.DeselectAll()
        poly_sel.DeselectAll()
        
        # Select the gathered points
        for point_idx in points_list:
            point_sel.Select(point_idx)
        
        # Switch to point mode
        doc.SetMode(c4d.Mpoints)
    
    return points_list

# -----------------------------------------------------------------------------------
# Align Vertices to Plane Function
# -----------------------------------------------------------------------------------
def alignVtxToPlane():
    doc = c4d.documents.GetActiveDocument()
    obj = doc.GetActiveObject()
    
    if obj is None or not isinstance(obj, c4d.PolygonObject):
        c4d.StatusSetText('Please select a polygon object.')
        return
    
    # Remember original mode and selection
    original_mode = doc.GetMode()
    original_selection = get_original_selection(obj, original_mode)
    
    # Get selected points from CURRENT selection mode and convert to point selection
    points = get_selected_points_and_convert(obj, doc)
    
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
    
    # Restore original selection mode and selection
    restore_original_selection(obj, doc, original_mode, original_selection)
    
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
