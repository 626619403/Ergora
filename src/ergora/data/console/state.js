// UI selection and server snapshots; business state remains on the server.
export const app = {
  tab: "overview",
  project: sessionStorage.getItem("ergora-project"),
  bootstrap: null,
  data: null,
  layers: {},
  agentRoles: [],
};
export const bindingFor = (data, layer) =>
  data.configuration.layers[layer].binding;
export const stages = ["inventory", "plan", "work", "integrate", "verify", "review"];
