export async function api(path, body, method = "POST", decode) {
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
  if (response.ok) return decode ? decode(response) : response.json();
  const result = await response.json();
  throw new Error(
    result.error ||
      (typeof result.detail === "string"
        ? result.detail
        : JSON.stringify(result.detail)) ||
      `HTTP ${response.status}`,
  );
}
