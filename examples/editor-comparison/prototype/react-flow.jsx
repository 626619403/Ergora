import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ReactFlow, Background, Controls, applyNodeChanges } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

export function reactFlowGraph(container, onSelect, onConnect) {
  const root = createRoot(container);
  function Graph({ units, selected }) {
    const [nodes, setNodes] = useState([]);
    useEffect(() => setNodes(previous => units.map((unit, index) => ({
      id: unit.id,
      data: { label: unit.id },
      selected: unit.id === selected,
      position: previous.find(node => node.id === unit.id)?.position || {
        x: 70 + (index % 2) * 220, y: 50 + Math.floor(index / 2) * 140,
      },
    }))), [units, selected]);
    const edges = units.flatMap(unit => unit.depends_on.map(id => ({
      id: JSON.stringify([id, unit.id]), source: id, target: unit.id,
    })));
    return <ReactFlow nodes={nodes} edges={edges}
      onNodesChange={changes => setNodes(previous => applyNodeChanges(changes, previous))}
      onNodeClick={(_, node) => onSelect(node.id)}
      onConnect={edge => onConnect(edge.source, edge.target)} fitView
      deleteKeyCode={null} nodesFocusable edgesFocusable
      ariaLabelConfig={{ 'node.a11yDescription.default': '可选择或用方向键移动节点；依赖也可在表单中编辑。' }}>
      <Background /><Controls showInteractive={false} />
    </ReactFlow>;
  }
  return {
    update(units, selected) { root.render(<Graph units={units} selected={selected} />); },
    destroy() { root.unmount(); },
  };
}
