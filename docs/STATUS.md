# Interpreting probe outcomes

The `probe.quality.evaluate` helper distinguishes:
- `not_configured`: no target URLs provided.
- `failed`: URLs were provided but errors occurred without products.
- `no_structured_products`: requests completed without extracted Product JSON-LD.
- `products_found`: extracted at least one product without errors.
- `products_found_with_errors`: partial success.

Missing values remain missing. Completeness is `null` for zero products rather than a misleading zero-quality percentage.

This helper is a foundation for dashboard integration; it does not establish live site coverage.
