# Server: /api/assessments errors and worker OOM

## Get the actual exception

When you see `[ERROR] Error handling request /api/assessments` without a traceback, use:

```bash
ssh root@159.65.160.106 "journalctl -u mingus-test --since '10 minutes ago' --no-pager | grep -A 15 'Error in submit_assessment\|Traceback\|Exception'"
```

Or dump more log lines so Python tracebacks are visible:

```bash
ssh root@159.65.160.106 "journalctl -u mingus-test --since '10 minutes ago' --no-pager -n 200"
```

## Worker killed (OOM)

If you see:

```text
Worker (pid:XXXX) was sent SIGKILL! Perhaps out of memory?
```

- The droplet is running out of RAM and the kernel is killing the gunicorn worker.
- **Immediate mitigations:**
  1. Use a single worker (you already have `-w 1` in ExecStart). Do not increase workers on a small box.
  2. Add swap so the system has more “memory” under pressure:
     ```bash
     sudo fallocate -l 1G /swapfile
     sudo chmod 600 /swapfile
     sudo mkswap /swapfile
     sudo swapon /swapfile
     echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
     ```
  3. Restart the app after code/config changes:  
     `sudo systemctl restart mingus-test`
  4. If the app imports heavy ML or large data at startup, consider lazy loading or moving that work off the web worker.

- **Long term:** Upgrade the droplet to a plan with more RAM if traffic or assessment usage grows.

## Code fixes already applied

- **risk_level:** Vehicle assessment and `submit_assessment` now set/use `risk_level` (and `health_level` fallback) so the INSERT into `lead_magnet_results` does not fail.
- **sync_assessments_to_profile:** Safe handling of `None`/missing `recommendations` and `subscores` (no crash on `json.loads`).
- **user_behavior_analytics:** `interaction_type` is normalized to an allowed value so the CHECK constraint does not fail; retry on “database is locked” for SQLite.
- **submit_assessment:** Full exception is logged with `logger.exception(...)` so the next failure will show a traceback in journalctl.

After deploying these changes and restarting `mingus-test`, re-run the assessment flow and, if it still errors, use the journalctl commands above to capture the traceback.
