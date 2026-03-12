# Extensions

Artel supports native Python extensions for tools, hooks, and UI widgets.

## Install an extension

Install from a registry name, a Git URL, or a local path:

```bash
artel ext install artel-ext-foo
artel ext install git+https://github.com/user/artel-ext-foo.git
artel ext install ../artel-ext-foo
```

If you pass a plain package name, Artel first tries to resolve it through the configured registries.

## List installed extensions

```bash
artel ext list
```

## Remove an extension

```bash
artel ext remove artel-ext-foo
```

## Update extensions

Update one extension:

```bash
artel ext update artel-ext-foo
```

Update everything currently installed:

```bash
artel ext update
```

## Search registries

Search across all configured registries:

```bash
artel ext search browser
```

## Registry management

List current registries:

```bash
artel ext registry list
```

Add a custom registry:

```bash
artel ext registry add mycompany https://example.com/extensions.toml
```

Remove a custom registry:

```bash
artel ext registry remove mycompany
```

The built-in `official` registry is enabled by default and cannot be removed.

## Configuration

The extension section in your config can control install location and allow and deny lists:

```toml
[extensions]
dir = "~/.config/artel/extensions"
enabled = []
disabled = []
```

You can also define registries directly in the config file:

```toml
[[extensions.registries]]
name = "official"
url = "https://example.com/extensions.toml"
```
