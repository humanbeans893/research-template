# /zotero-connect

Connect to the Zotero desktop app running on Windows from WSL2.

## When to use

- At the start of a session when Zotero MCP tools are needed
- When `mcp__zotero__*` tools return "Connection refused" or "timed out"

## Steps

1. Ask the user to confirm Zotero is running on Windows.

2. Start the port forwarder (idempotent — safe to run if already active):
   ```bash
   python3 .claude/scripts/zotero-forward.py &>/tmp/zotero-forward.log &
   sleep 1 && cat /tmp/zotero-forward.log
   ```

3. Verify connectivity:
   ```bash
   curl -s --connect-timeout 3 http://localhost:23119/connector/ping
   ```
   Expected: any response from Zotero (even 404 is OK).

4. Test MCP with `mcp__zotero__zotero_get_collections`.

## Troubleshooting

- **"Address already in use"**: Forwarder is already running — skip to step 3.
- **Connection timeout at step 3**: Windows Firewall may be blocking. User needs to run in admin PowerShell:
  ```powershell
  New-NetFirewallRule -DisplayName "Zotero WSL2" -Direction Inbound -LocalPort 23119 -Protocol TCP -Action Allow -RemoteAddress 172.30.0.0/16
  ```
- **Gateway IP changed**: The script auto-detects via `ip route show default`. If WSL2 was restarted, the IP may change — just re-run the forwarder.
- **ブラウザコネクターが壊れた場合**: `netsh portproxy` の `listenaddress` が `0.0.0.0` だとブラウザ→Zoteroの通信を横取りする。WSL2ゲートウェイIPのみにすること:
  ```powershell
  netsh interface portproxy delete v4tov4 listenport=23119 listenaddress=0.0.0.0
  netsh interface portproxy add v4tov4 listenport=23119 listenaddress=172.30.224.1 connectport=23119 connectaddress=127.0.0.1
  ```

## Collection reference

- **EddyAndCuurent**: key `BVS7T5VA`
