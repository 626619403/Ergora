import { start } from './app.js';
import { cytoscapeGraph } from './cytoscape.js';
import { schemaForm } from './schema-form.jsx';
start({ name: 'schema', title: 'Cytoscape + JSON Forms', graph: cytoscapeGraph, form: schemaForm });
