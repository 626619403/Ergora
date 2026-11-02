export async function api(path, body, method = "POST") {
  const options =
    body === undefined
      ? {}
      : {
          method,
          headers: {
            "Content-Type": "application/json",
            "X-Ergora-Request": "1",
          },
          body: JSON.stringify(body),
        };
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok)
    throw new Error(
      result.error ||
        (typeof result.detail === "string"
          ? result.detail
          : JSON.stringify(result.detail)) ||
        `HTTP ${response.status}`,
    );
  return result;
}
