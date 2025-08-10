function initNetwork(containerId) {
    const container = document.getElementById(containerId);
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    const svg = d3.select(`#${containerId}`)
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    return {
        svg: svg,
        width: width,
        height: height,
        nodes: [],
        links: []
    };
}

function updateNetworkVisualization(network, data) {
    // clear
    network.svg.selectAll("*").remove();

    // map nodes: support either {x,y} or {position: [x,y]}
    const nodes = data.nodes.map(node => {
        let x = node.x, y = node.y;
        if (typeof x === 'undefined' && node.position && node.position.length >= 2) {
            x = node.position[0];
            y = node.position[1];
        }
        // normalize to canvas coordinates
        const nx = x * network.width / data.areaSize[0];
        const ny = y * network.height / data.areaSize[1];
        return { id: node.id, x: nx, y: ny, energy: node.energy };
    });

    // index by id for quick lookup
    const nodeById = {};
    nodes.forEach(n => nodeById[n.id] = n);

    const links = [];
    (data.links || []).forEach(link => {
        const s = nodeById[link.source];
        const t = nodeById[link.target];
        if (s && t) links.push({ source: s, target: t });
    });

    // draw links
    network.svg.selectAll(".link")
        .data(links)
        .join("line")
        .attr("class", "link")
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y)
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .attr("stroke-width", 1.5);

    // nodes
    const nodeG = network.svg.selectAll(".node")
        .data(nodes, d => d.id)
        .join("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.x},${d.y})`);

    nodeG.append("circle")
        .attr("r", 10)
        .attr("fill", d => d.energy > 70 ? "#4CAF50" : d.energy > 30 ? "#FFC107" : "#F44336")
        .attr("stroke", "#333")
        .attr("stroke-width", 1);

    nodeG.append("text")
        .attr("dy", 4)
        .attr("text-anchor", "middle")
        .attr("font-size", "10px")
        .attr("fill", "white")
        .text(d => d.id);

    network.nodes = nodes;
    network.links = links;
}
