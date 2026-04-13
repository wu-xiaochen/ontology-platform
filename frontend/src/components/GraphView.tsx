import React, { useCallback, useRef } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';

interface Node {
  id: string;
  name: string;
  type: string;
  color?: string;
  val?: number;
}

interface Link {
  source: string;
  target: string;
  label: string;
}

interface GraphData {
  nodes: Node[];
  links: Link[];
}

interface GraphViewProps {
  data: GraphData;
  onNodeClick?: (node: Node) => void;
}

const GraphView: React.FC<GraphViewProps> = ({ data, onNodeClick }) => {
  const fgRef = useRef<any>();

  const getColor = (type: string) => {
    switch (type) {
      case 'Entity': return '#007aff';
      case 'Process': return '#ff3b30';
      case 'Rule': return '#34c759';
      default: return '#00f2ff';
    }
  };

  const processedData = {
    nodes: data.nodes.map(n => ({ ...n, color: getColor(n.type), val: 1 })),
    links: data.links
  };

  return (
    <div className="glass w-full h-full relative overflow-hidden">
      <ForceGraph3D
        ref={fgRef}
        graphData={processedData}
        backgroundColor="#0a0a0c"
        nodeLabel="name"
        nodeColor="color"
        nodeRelSize={6}
        linkWidth={1}
        linkColor={() => 'rgba(255, 255, 255, 0.2)'}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
        onNodeClick={onNodeClick}
        enablePointerInteraction={true}
        nodeThreeObject={(node: any) => {
          const sprite = new THREE.Sprite(
            new THREE.SpriteMaterial({ 
              color: node.color,
              transparent: true,
              opacity: 0.8
            })
          );
          sprite.scale.set(12, 12, 1);
          return sprite;
        }}
      />
      <div className="absolute top-4 left-4 z-10">
        <h3 className="text-xs font-semibold opacity-50 uppercase tracking-widest">
          3D Knowledge Domain
        </h3>
      </div>
    </div>
  );
};

export default GraphView;
