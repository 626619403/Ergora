import { start, nativeForm } from './app.js';
import { reactFlowGraph } from './react-flow.jsx';
start({ name: 'flow', title: 'React Flow + 原生表单', graph: reactFlowGraph, form: nativeForm });
