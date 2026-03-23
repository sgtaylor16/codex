import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";



/**
 * Performs topological sort on a directed graph
 * @param {Object} graph - Adjacency list representation of the graph
 * @returns {string[]} - Array of nodes in topologically sorted order
 */
function topologicalSort(graph) {
    if (typeof graph !== 'object' || graph === null) {
        throw new Error("Graph must be a non-null object (adjacency list).");
    }

    // Step 1: Compute in-degree for each node
    const inDegree = {};
    const nodes = new Set();

    for (const node in graph) {
        nodes.add(node);
        if (!Array.isArray(graph[node])) {
            throw new Error(`Graph adjacency list for '${node}' must be an array.`);
        }
        graph[node].forEach(neighbor => {
            nodes.add(neighbor);
            inDegree[neighbor] = (inDegree[neighbor] || 0) + 1;
        });
    }

    // Initialize in-degree for nodes with no incoming edges
    nodes.forEach(node => {
        if (!(node in inDegree)) {
            inDegree[node] = 0;
        }
    });

    // Step 2: Collect nodes with in-degree 0
    const queue = [];
    for (const node of nodes) {
        if (inDegree[node] === 0) {
            queue.push(node);
        }
    }

    // Step 3: Process nodes
    const sortedOrder = [];
    while (queue.length > 0) {
        const current = queue.shift();
        sortedOrder.push(current);

        (graph[current] || []).forEach(neighbor => {
            inDegree[neighbor]--;
            if (inDegree[neighbor] === 0) {
                queue.push(neighbor);
            }
        });
    }

    // Step 4: Check for cycles
    if (sortedOrder.length !== nodes.size) {
        throw new Error("Graph has at least one cycle; topological sort not possible.");
    }

    return sortedOrder;
}


export { topologicalSort };

