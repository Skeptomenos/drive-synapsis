# Rust & Tauri Standards

> **Read this when:** Writing or reviewing Rust code in `src-tauri/`.
> **Also read:** `global.md` for language-agnostic rules.

---

## 1. Code Style & Formatting

### 1.1 Tooling
- **Formatter:** `rustfmt` — Run `cargo fmt` before committing
- **Linter:** `clippy` — Run `cargo clippy` and fix all warnings
- **Edition:** Rust 2021

### 1.2 Naming Conventions
- **Functions/Variables:** `snake_case`
- **Types/Traits:** `PascalCase`
- **Constants:** `SCREAMING_SNAKE_CASE`
- **Modules:** `snake_case` (file names match module names)

### 1.3 Error Handling
```rust
// GOOD: Use Result with context
fn do_something() -> Result<String, AppError> {
    std::fs::read_to_string("config.json")
        .map_err(|e| AppError::ConfigLoadFailed(e.to_string()))
}

// BAD: Unwrap in production code
let val = option.unwrap(); // Never do this
```

- Use `thiserror` for custom error types
- Use `anyhow` for application-level error propagation
- Reserve `.unwrap()` for tests only

---

## 2. Tauri-Specific Patterns

### 2.1 Plugin Configuration
```rust
// In lib.rs — use the builder pattern
tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .invoke_handler(tauri::generate_handler![...])
    .run(tauri::generate_context!())
    .expect("error running tauri application");
```

### 2.2 Async Commands
```rust
// Async commands are preferred for I/O
#[tauri::command]
async fn fetch_data() -> Result<String, String> {
    // Async I/O here
    Ok("data".to_string())
}

// Sync commands for pure computation only
#[tauri::command]
fn calculate(x: i32) -> i32 {
    x * 2
}
```

### 2.3 Blocking Operations
```rust
// Never block the main thread
// Use spawn_blocking for CPU-intensive work
tokio::task::spawn_blocking(|| {
    // Heavy computation here
}).await
```

---

## 3. Security

### 3.1 Capabilities (CSP)
- Define minimal capabilities in `src-tauri/capabilities/default.json`
- Only allow necessary permissions (shell, filesystem)
- Do not enable `*:all` — use scoped permissions

### 3.2 No Secrets in Code
```rust
// BAD: Hardcoded secret
const API_KEY: &str = "sk-12345...";

// GOOD: Read from env at runtime
let api_key = std::env::var("API_KEY")
    .expect("API_KEY not set");
```

### 3.3 Input Validation
- Validate all data received from frontend via `#[tauri::command]`
- Use `serde` with strict typing — no `serde_json::Value` unless necessary

---

## 4. Testing

### 4.1 Unit Tests
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_logic() {
        let result = calculate(2);
        assert_eq!(result, 4);
    }
}
```

### 4.2 Integration Tests
- Use `#[tokio::test]` for async tests

---

## 5. Dependencies

### 5.1 Recommended Crates
| Crate | Purpose |
|-------|---------|
| `serde` / `serde_json` | Serialization |
| `thiserror` | Custom error types |
| `anyhow` | Error propagation |
| `tokio` | Async runtime (via Tauri) |
| `tauri-plugin-shell` | System shell access |

### 5.2 Forbidden Patterns
| Pattern | Reason |
|---------|--------|
| `unsafe` blocks | Security risk — avoid unless absolutely necessary |
| `.unwrap()` in prod | Use `?` or `.expect()` with context |
| Global mutable state | Use Tauri's `State` manager instead |
| Blocking in async | Deadlock risk — use `spawn_blocking` |

---

## 6. File Organization

```
src-tauri/
├── src/
│   ├── main.rs       # Entry point (minimal)
│   ├── lib.rs        # Tauri setup, plugins, commands
│   └── commands/     # Tauri command modules
├── capabilities/
│   └── default.json  # Permission definitions
├── Cargo.toml        # Dependencies
└── tauri.conf.json   # Tauri configuration
```
