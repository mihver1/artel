# Extensions

Worker supports native Python extensions for tools, hooks, and UI widgets.

## Install an extension

Install from a registry name, a Git URL, or a local path:

```bash
worker ext install worker-ext-foo
worker ext install git+https://github.com/user/worker-ext-foo.git
worker ext install ../worker-ext-foo
```

If you pass a plain package name, Worker first tries to resolve it through the configured registries.

## List installed extensions

```bash
worker ext list
```

## Remove an extension

```bash
worker ext remove worker-ext-foo
```

## Update extensions

Update one extension:

```bash
worker ext update worker-ext-foo
```

Update everything currently installed:

```bash
worker ext update
```

## Search registries

Search across all configured registries:

```bash
worker ext search browser
```

## Registry management

List current registries:

```bash
worker ext registry list
```

Add a custom registry:

```bash
worker ext registry add mycompany https://example.com/extensions.toml
```

Remove a custom registry:

```bash
worker ext registry remove mycompany
```

The built-in `official` registry is enabled by default and cannot be removed.

## Configuration

The extension section in your config can control install location and allow and deny lists:

```toml
[extensions]
dir = "~/.config/worker/extensions"
enabled = []
disabled = []
```

You can also define registries directly in the config file:

```toml
[[extensions.registries]]
name = "official"
url = "https://raw.githubusercontent.com/mihver1/worker-agent/main/registry/extensions.toml"
```
