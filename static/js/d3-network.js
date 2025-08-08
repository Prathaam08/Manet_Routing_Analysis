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
    // Clear existing elements
    network.svg.selectAll("*").remove();
    
    // Extract nodes and links from simulation state
    const nodes = data.nodes.map(node => ({
        id: node.id,
        x: node.position[0] * network.width / data.areaSize[0],
        y: node.position[1] * network.height / data.areaSize[1],
        energy: node.energy
    }));
    
    const links = [];
    data.links.forEach(link => {
        const source = nodes.find(n => n.id === link.source);
        const target = nodes.find(n => n.id === link.target);
        if (source && target) {
            links.push({source, target});
        }
    });
    
    // Draw links
    network.svg.selectAll(".link")
        .data(links)
        .enter()
        .append("line")
        .attr("class", "link")
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y)
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .attr("stroke-width", 1.5);
    
    // Draw nodes
    const nodeGroups = network.svg.selectAll(".node")
        .data(nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.x},${d.y})`);
    
    nodeGroups.append("circle")
        .attr("r", 10)
        .attr("fill", d => {
            if (d.energy > 70) return "#4CAF50"; // Green
            if (d.energy > 30) return "#FFC107"; // Yellow
            return "#F44336"; // Red
        })
        .attr("stroke", "#333")
        .attr("stroke-width", 1);
    
    nodeGroups.append("text")
        .attr("dy", 4)
        .attr("text-anchor", "middle")
        .attr("font-size", "10px")
        .attr("fill", "white")
        .text(d => d.id);
    
    // Update network state
    network.nodes = nodes;
    network.links = links;
}