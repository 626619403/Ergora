"""Runs in the optional pinned SDK environment; no Ergora imports or scheduler."""

from contextlib import redirect_stdout
from dataclasses import asdict
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys
import uuid


def installed_versions():
    versions = {name: version(name) for name in ("deepseek-harness-sdk", "deepseek-harness-runtime-bin")}
    if any(value != "0.2.2rc2" for value in versions.values()):
        raise ValueError("This adapter requires deepseek-harness-sdk/runtime-bin==0.2.2rc2")
    return versions


def main():
    versions = installed_versions()
    if sys.argv[1] == "--check":
        print(json.dumps({"distributions": versions, "python": sys.version}))
        return
    path = Path(sys.argv[1])
    request = json.loads(path.read_text(encoding="utf-8"))
    binding = request["binding"]
    credential = binding["api_key_env"]
    # Remove ambient DSH configuration and unrelated credentials before importing
    # or spawning the SDK. Retaining HOME does not imply host isolation.
    environment = {key: value for key, value in os.environ.items() if key in (
        "PATH", "HOME", "LANG", "LC_ALL", "PYTHONUTF8", "PYTHONIOENCODING", "TMPDIR",
        "SSL_CERT_FILE", "SSL_CERT_DIR", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
        "http_proxy", "https_proxy", "all_proxy", "no_proxy", credential)}
    os.environ.clear()
    os.environ.update(environment)
    with redirect_stdout(sys.stderr):
        from deepseek_harness import DeepSeekHarness

    home = path.parent / "native-home"
    home.mkdir(mode=0o700)
    patch = [{"id": name, "disabled": True} for name in (
        "persistent-bash", "persistent-pwsh", "tool-fs", "tool-working-directory", "mcp-resources", "llm-deepseek")]
    patch.append({"insert": [{"id": "llm-ergora", "name": "@deepseek-ai/dsh-llm-pi-ai", "config": {"providers": {
        "ergora": {"apiKeyEnv": credential, "api": "openai-completions", "baseURL": binding["base_url"],
                   "models": [{"id": binding["model"], "contextWindow": binding.get("context_window", 131072),
                               "maxTokens": binding.get("max_tokens", 4096)}],
                   "retryPolicy": {"mode": "normal", "maxRetries": 0}}}}}]})
    if request["task_mcp"] is not None:
        patch.append({"insert": [{"id": "mcp-ergora-task", "name": "@deepseek-ai/dsh-mcp-client", "config": {
            "serverName": "ergora_task", "transport": "stdio", **request["task_mcp"], "cwd": request["cwd"],
            "startupTimeoutMs": 15000, "toolCallTimeoutMs": 15000, "closeTimeoutMs": 5000,
            "failOnStartupError": True, "reconnect": {"enabled": False}}}]})
    patch_path = path.parent / "native-patch.yml"
    patch_path.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
    prompt = request["prompt"]
    if request["schema"] is not None:
        prompt += "\n\nReturn exactly one JSON object matching this schema, without fences or explanation:\n" + json.dumps(request["schema"])
    (path.parent / "native-prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    native_id = "ergora-" + uuid.uuid4().hex
    (path.parent / "native-identity.json").write_text(json.dumps({"session_id": native_id, "distributions": versions,
        "python": sys.version, "profile": "sdk-minimal", "home": str(home)}), encoding="utf-8")

    def record(notification):
        with (path.parent / "native-events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(notification), ensure_ascii=False) + "\n")

    # The existing outer Ergora process owner bounds the whole call, including
    # notifications and MCP descendants; the SDK request timeout does not.
    with redirect_stdout(sys.stderr):
        with DeepSeekHarness(profile="sdk-minimal", dsh_home=str(home), patches=(str(patch_path),),
            cwd=request["cwd"], runtime_cwd=request["cwd"], provider="ergora", model=binding["model"],
            initialize_timeout_seconds=15, request_timeout_seconds=15, shutdown_timeout_seconds=5) as harness:
            result = harness.run(prompt, session_id=native_id, on_notification=record)
            native = {"session_id": result.session_id, "finish_reason": result.finish_reason,
                      "final_response": result.final_response, "events": result.events}
            (path.parent / "native-result.json").write_text(json.dumps(native, ensure_ascii=False), encoding="utf-8")
    print(result.final_response)


if __name__ == "__main__":
    main()
