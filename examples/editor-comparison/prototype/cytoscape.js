import cytoscape from '@ergora/cytoscape';

export function cytoscapeGraph(container, onSelect, onConnect) {
  const graph = cytoscape({
    container, elements: [],
    style: [
      { selector: 'node', style: {
        label: 'data(label)', 'background-color': '#527e59', color: '#183923',
        'text-valign': 'bottom', 'text-margin-y': 8, width: 28, height: 28,
      } },
      { selector: '.selected', style: {
        'background-color': '#c07832', 'border-width': 3, 'border-color': '#213d2b',
      } },
      { selector: 'edge', style: {
        width: 2, 'line-color': '#9ab59c', 'target-arrow-color': '#9ab59c',
        'target-arrow-shape': 'triangle', 'curve-style': 'bezier',
      } },
    ],
  });
  let source = null;
  graph.on('tap', 'node', event => {
    const id = event.target.id();
    if (event.originalEvent?.shiftKey) { source = id; return; }
    if (source !== null) {
      const previous = source;
      source = null;
      onConnect(previous, id);
    } else onSelect(id);
  });
  return {
    update(units, selected) {
      source = null;
      const positions = new Map(graph.nodes().map(node => [node.id(), node.position()]));
      graph.elements().remove();
      graph.add(units.map((unit, index) => ({
        data: { id: unit.id, label: unit.id },
        position: positions.get(unit.id) || { x: 90 + (index % 2) * 230, y: 70 + Math.floor(index / 2) * 140 },
      })));
      graph.add(units.flatMap(unit => unit.depends_on.map(id => ({
        data: { id: JSON.stringify([id, unit.id]), source: id, target: unit.id },
      }))));
      graph.nodes().filter(node => node.id() === selected).addClass('selected');
      graph.fit(undefined, 45);
    },
    destroy() { graph.destroy(); },
  };
}
