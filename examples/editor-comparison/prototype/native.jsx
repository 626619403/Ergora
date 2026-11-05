import { start, nativeForm } from './app.js';
import { cytoscapeGraph } from './cytoscape.js';
start({ name: 'native', title: 'Cytoscape + 原生表单', graph: cytoscapeGraph, form: nativeForm });
