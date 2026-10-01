# Tool restriction qualification — 2026-09-30

The installed CLI is copied Codex0.159.2. Platform source by itself leaves native web search mode unchanged and exposes per-bot VM shell tools. Prompt-only restrictions are insufficient for Arm A.

Official [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) documents web_search disabled, shell feature control, and agents.enabled. Official [MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) documents enabled_tools allowlists. CLI config/read and actual localhost outgoing transport were tested independently of paid/provider inference.

The first tool inspection missed additional_tools in request input; that interpretation is superseded. Metadata-only synthetic functions.exec enumerated nested tool registry: MCP get_desktop_state retained, synthetic vm_exec/read_file/search_web removed. apply_patch remained present. agents.enabled=false removed collaboration family; read-only policy rejected a fixture canary write before creation. These are local configuration tests, not clinical/model outcomes or integrated platform acceptance. No medical images, real model answers or upstream inference involved.

Next gate: apply supported controls in the benchmark-owned existing-platform runner; verify resolved per-turn policy and graphical adapter scope. Current study only, no filesystem/network shortcuts, no independent agent expansion, replayable screenshots/actions. No Arm A inference before this gate passes.
