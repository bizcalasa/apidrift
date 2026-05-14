# apidrift

Detect breaking changes in REST APIs by diffing OpenAPI specs across versions and generating human-readable reports.

---

## Installation

```bash
pip install apidrift
```

---

## Usage

Compare two OpenAPI spec files and generate a report:

```bash
apidrift diff specs/v1.yaml specs/v2.yaml
```

Or use it programmatically in Python:

```python
from apidrift import diff

report = diff("specs/v1.yaml", "specs/v2.yaml")
print(report.summary())
```

Example output:

```
[BREAKING] DELETE /users/{id} — endpoint removed
[BREAKING] POST /orders — required field 'customer_id' added to request body
[WARNING]  GET /products — response field 'price' type changed from integer to string
[INFO]     GET /health — new endpoint added
```

Export the report to JSON or HTML:

```bash
apidrift diff specs/v1.yaml specs/v2.yaml --format html --output report.html
```

---

## Supported Formats

- OpenAPI 3.x (YAML and JSON)
- Swagger 2.0 (YAML and JSON)

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any significant changes.

---

## License

MIT © apidrift contributors