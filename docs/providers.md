# Providers

## Primary: ipwho.is

- Endpoint: `GET https://ipwho.is/{ip}`
- Auth: none (free tier, HTTPS).
- IPv4 + IPv6.
- Fields used: `ip`, `type`, `country`, `country_code`, `region`,
  `region_code`, `city`, `postal`, `latitude`, `longitude`,
  `timezone.id`, `connection.{asn,org,isp,domain}`.
- Rate limits: respected; HTTP 429 surfaces as
  `[!] API rate limit reached.` Batch mode continues with the next IP.

## Adding Provider B

1. Create `src/ipghost/providers/second.py` with
   `class SecondProvider(GeoIPProvider)` and a `normalize()` that returns
   `IPInfo`.
2. Validate every field (types, lat/lon ranges, nulls) — never trust JSON.
3. Add mocked tests in `tests/test_provider.py`.
4. Document the endpoint, auth, and limits here. Do not put keys in source.

The CLI, formatters, maps, batch engine, and JSON contract stay untouched.
