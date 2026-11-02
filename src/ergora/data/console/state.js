// UI selection and server snapshots; business state remains on the server.
export const app = {
  tab: "overview",
  project: sessionStorage.getItem("ergora-project"),
  bootstrap: null,
  data: null,
  layers: {},
  agentRoles: [],
};
export const bindingFor = (project, layer) =>
  project.bindings[layer] ||
  (layer === "kernel" ? { tool: "manual" } : project.bindings.implementer);
export const stages = ["inventory", "plan", "work", "integrate", "verify", "review"];
