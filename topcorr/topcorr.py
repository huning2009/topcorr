import networkx as nx
import collections
import numpy as np

def _calculate_new_faces(faces, new, old_set):
    """
    Calculates the new triangular faces for the network when we 
    add in new

    Parameters
    -----------
    faces : list
        a list of the faces present in the graph
    new : int
        the node id that is being added to the face
    old_set : set
        the old face that the node is being added to

    Returns
    -------
    None
    """
    faces.remove(frozenset(old_set))

    faces.add(frozenset([new, old_set[1], old_set[0]]))
    faces.add(frozenset([new, old_set[0], old_set[2]]))
    faces.add(frozenset([new, old_set[1], old_set[2]]))

def _add_triangular_face(G, new, old_set, C, faces):
    """
    Adds a new triangle to the networkx graph G

    Parameters
    -----------
    G : networkx graph
        the networkx graph to add the new face to
    new : int
        the node id that is being added to the face
    C : array_like
        correlation matrix
    old_set : set
        the old face that the node is being added to
    faces : list
        a list of the faces present in the graph

    Returns
    -------
    None
    """
    if isinstance(new, collections.Sized):
        raise ValueError("New should be a scaler")

    if len(old_set) > 3:
        raise ValueError("Old set is not the right size!")
    for j in old_set:
        G.add_edge(new, j, weight=C[new, j])

def tmfg(corr, absolute=False):
    """
    Constructs a TMFG from the supplied correlation matrix

    Parameters
    -----------
    corr : array_like
        p x p matrix - correlation matrix
    absolute : bool
        whether to use the absolute correlation values for chooisng weights or normal ones

    Returns
    -------
    networkx graph
        The Triangular Maximally Filtered Graph
    """
    p = corr.shape[0]

    if absolute:
        weight_corr = np.abs(corr)
    else:
        weight_corr = corr

    # Find the 4 most central vertices
    degree_centrality = weight_corr.sum(axis=0)
    ind = np.argsort(degree_centrality)[::-1]
    starters = ind[0:4]
    starters_set = set(starters)
    not_in = set(range(p))
    not_in = not_in.difference(starters_set)

    G = nx.Graph()
    G.add_nodes_from(range(p))

    # Add the tetrahedron in
    faces = set()
    _add_triangular_face(G, ind[0], set([ind[1], ind[3]]), corr, faces)
    _add_triangular_face(G, ind[1], set([ind[2], ind[3]]), corr, faces)
    _add_triangular_face(G, ind[0], set([ind[2], ind[3]]), corr, faces)
    _add_triangular_face(G, ind[2], set([ind[1], ind[3]]), corr, faces)

    faces.add(frozenset([ind[0], ind[1], ind[3]]))
    faces.add(frozenset( [ind[1], ind[2], ind[3]] ))
    faces.add(frozenset([ind[0], ind[2], ind[3]]))
    faces.add(frozenset([ind[0], ind[1], ind[2]]))

    while len(not_in) > 0:
        #to_check = permutations(starters_set, 3)

        max_corr = -1
        max_i = -1
        nodes_correlated_with = None
        not_in_arr = np.array(list(not_in))

        # Find the node most correlated with the faces in the TMFG currently
        for ind in faces:
            ind = list(ind)
            ind_arr = np.array(ind)
            most_related = weight_corr[ind_arr, :][:, not_in_arr].sum(axis=0)
            ind_2 = np.argsort(most_related)[::-1]
            curr_corr = most_related[ind_2[0]]

            if curr_corr > max_corr:
                max_corr = curr_corr
                max_i = not_in_arr[[ind_2[0]]]
                nodes_correlated_with = ind

        starters_set = starters_set.union(set(max_i))
        not_in = not_in.difference(starters_set)
        _add_triangular_face(G, max_i[0], nodes_correlated_with, corr, faces)
        _calculate_new_faces(faces, max_i[0], nodes_correlated_with)
    
    return G

def pmfg(corr):
    """
    Constructs a PMFG from the correlation matrix specified

    Parameters
    -----------
    corr : array_like
        p x p matrix - correlation matrix

    Returns
    -------
    networkx graph
        The Planar Maximally Filtered Graph
    """
    vals = np.argsort(corr.flatten(), axis=None)[::-1]
    pmfg = nx.Graph()
    p = corr.shape[0]
    pmfg.add_nodes_from(range(p))
    for v in vals:
        idx_i, idx_j = np.unravel_index(v, (p, p))
        
        if idx_i == idx_j:
            continue

        pmfg.add_edge(idx_i, idx_j, weight=corr[idx_i, idx_j])
        if not nx.check_planarity(pmfg)[0]:
            pmfg.remove_edge(idx_i, idx_j)

        if len(pmfg.edges()) == 3 *  (p - 2):
            break

    return pmfg

def _in_same_component(components, i, j):
    """
    Checks to see if nodes i and j are in the same component in the MST

    Parameters
    -----------
    components : list 
        list containing the current components of the MST
    i : int
        integer of node i
    j : int
        integer of node j
    
    Returns
    -------
    bool
        True if i and j are in the same component, False otherwise
    """
    for c in components:
        if i in c and j in c:
            return True

    return False

def _merge_components(components, i, j):
    """
    Merges the components that contain nodes i and j

    Parameters
    -----------
    components : list 
        list containing the current components of the MST
    i : int
        integer of node i
    j : int
        integer of node j
    
    Returns
    -------
    list
        list containing the new components of the MST
    """
    c1 = None
    c2 = None
    c1_i = None
    c2_i = None
    for idx, c in enumerate(components):
        if i in c:
            c1 = c
            c1_i = idx
        
        if j in c:
            c2 = c
            c2_i = idx

    c1 |= c2

    del components[c2_i]
    return components
    
def mst(corr):
    """
    Constructs a minimum spanning tree from the specified correlation matrix

    Parameters
    -----------
    corr : array_like
        p x p matrix - correlation matrix

    Returns
    -------
    networkx graph
        The Minimum Spanning Tree
    """
    p = corr.shape[0]
    vals = np.argsort(corr.flatten(), axis=None)[::-1]
    components = [set([x]) for x in range(p)]
    mst_G = nx.Graph()
    for v in vals:
        idx_i, idx_j = np.unravel_index(v, (p, p))
        if idx_i == idx_j:
            continue

        if _in_same_component(components, idx_i, idx_j):
            continue
        else:
            mst_G.add_edge(idx_i, idx_j, weight=corr[idx_i, idx_j])
            components = _merge_components(components, idx_i, idx_j)
        if len(mst_G.edges()) == p - 1:
            break

    return mst_G

def threshold(corr, threshold, binary=False, absolute=True):
    """
    Thresholds the correlation matrix at the set level

    Parameters
    -----------
    corr : array_like
        p x p matrix - correlation matrix to threshold
    threshold : float
        threshold at which to keep values
    binary : bool, optional
        whether the nonzero values are set to 1 or left as floats (default False)
    absolute : bool, optional
        whether to threshold the plain or absolute values (default True)
    
    Returns
    -------
    array_like
        thresholded matrix
    """
    corr = corr.copy()
    if absolute:
        corr[np.abs(corr) < threshold] = 0
    else:
        corr[corr < threshold] = 0

    if binary:
        corr[np.abs(corr) > 0] = 1

    return corr

def calculate_partial_correlation(corr, i, j, k):
    """
    Calculates the partial correlation between i and jm
    given k

    Parameters
    -----------
    corr : array_like
        correlation matrix
    i : int
        first variable
    j : int
        second variable
    k : int
        variable to remove the effect of
    """
    dem = (1 - corr[i, k]**2) * (1 - corr[k, j]**2)
    return (corr[i, j] - corr[i, k] * corr[k, j]) / np.sqrt(dem)

def dependency_network(corr):
    """
    Calculates a dependency network - see "Dominating Clasp of the Financial
    Sector Revealed by Partial Correlation Analysis of the Stock Market"
    for more details

    Parameters
    -----------
    corr : array_like
        correlation matrix

    Returns
    -------
    array_like
        dependency network adjacency matrix
    """ 
    p = corr.shape[0]
    ind = np.arange(p)
    D = np.zeros((p, p, p))
    for i in range(p):
        for j in range(p):
            for k in range(p):
                if i == j or i == k or j == k:
                    continue
                D[i, j, k] = (corr[i, j] - calculate_partial_correlation(corr, i, j, k))
    
    for i in range(p):
        for j in range(p):
            D[i, j, j] = 1

    # Next we filter D down
    dependency_network = np.zeros((p, p))
    for i in range(p):
        for k in range(p):
            if i == k:
                continue
            dependency_network[k, i] = D[i, i!=ind, k].sum() / (p-1)

    return dependency_network

def knn(corr, k):
    """
    Calculates a k-Nearest Neighbours graph from the given correlation
    matrix - each node is allowed k edges

    Parameters
    -----------
    corr : array_like
        correlation matrix

    Returns
    -------
    Networkx Graph
        k-NN network adjacency matrix
    """ 
    p = corr.shape[0]
    G = nx.Graph()
    #ind = np.arange(p)
    for i in range(p):
        edges = corr[:, i]
        sort = np.argsort(edges)[::-1]
        num = 0
        for j in sort:
            if num == k:
                break
            if j == i:
                continue
            G.add_edge(i, j, weight=corr[i, j])
            num += 1
    return G

def partial_correlation(corr):
    """
    Calculates a partial correlation network from the given correlation matrix
    
    Parameters
    -----------
    corr : array_like
        correlation matrix

    Returns
    -------
    array_like
        partial correlation matrix
    """ 
    p = corr.shape[0]
    prec = np.linalg.inv(corr)
    partial_correlation = np.zeros((p, p))
    
    for i in range(p):
        for j in range(p):
            partial_correlation[i, j] = - prec[i, j] / (np.sqrt(prec[i, i] * prec[j, j]))

    np.fill_diagonal(partial_correlation, 1)

    return partial_correlation

    
