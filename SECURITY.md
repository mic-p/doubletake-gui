# Security notes

This is an **unofficial local GUI** for the [omarroth/doubletake](https://github.com/omarroth/doubletake) AirPlay client. It does not implement AirPlay security or authenticate receivers itself.

- Mirroring PINs/passwords typed into the GUI are passed through the child process environment variable `DOUBLETAKE_CODE`, as recommended by the upstream project. They are not stored in the GUI's settings or added to Doubletake's command-line arguments. Process environments are **not** a secure vault: suitably privileged local users and processes may be able to inspect them.
- Interactive responses are masked in the entry field and the GUI logs only that a response was sent. Output emitted by upstream Doubletake is displayed unmodified, and may include debug material. **Review logs before sharing them.**
- `doubletake-ctl connect` and `doubletake-ctl pin` accept credentials in argv. The GUI masks them in its log, but an external process monitor such as `ps` may see the argument temporarily. This is an upstream CLI interface limitation.
- Additional command-line flags are parsed into an argument list and passed to `QProcess`; the GUI **does not execute them through a shell**.
- Auto-detection never silently overwrites a non-empty executable path. The user controls the executable; choose paths you trust.
- The GUI never needs root permissions at runtime. Root is used only in the optional manual installation step under `/opt/apple`.
- No telemetry, background updater, remote code download, or automatic access to third-party accounts is included.

Please report GUI-specific issues to the GUI project's issue tracker. For protocol, authentication and encoder vulnerabilities in the core AirPlay implementation, see the [main Doubletake repository](https://github.com/omarroth/doubletake).
