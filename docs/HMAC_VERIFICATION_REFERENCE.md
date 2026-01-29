# HMAC Signature Verification Reference

Complete reference guide for Microsoft Teams webhook HMAC signature verification, including implementation details, code examples, and testing procedures.

> **Note:** The legacy AWS Lambda handlers under `aws_agent_core/lambda_handlers` were removed.
> Teams webhook handling should be implemented via the `teams_adapter` service or an external
> webhook receiver that forwards messages to `/invocations`.

## Table of Contents

1. [Overview](#overview)
2. [HMAC Signature Algorithm](#hmac-signature-algorithm)
3. [Lambda Implementation](#lambda-implementation)
4. [Postman Testing](#postman-testing)
5. [Python Testing Scripts](#python-testing-scripts)
6. [Troubleshooting](#troubleshooting)

---

## Overview

Microsoft Teams signs outgoing webhook requests using **HMAC SHA256** to ensure request authenticity. The signature is computed from the request body using a shared secret (security token) configured when creating the webhook.

### Security Flow

```
Teams Webhook Creation
    ↓
Security Token Generated (shared secret)
    ↓
Teams sends request with HMAC signature
    ↓
Lambda verifies signature using same secret
    ↓
Request processed if signature valid
```

---

## HMAC Signature Algorithm

### Algorithm Details

Microsoft Teams uses the following algorithm:

1. **Input**: Request body (raw JSON string) + Security token (webhook secret)
2. **Algorithm**: HMAC SHA256
3. **Encoding**: Base64
4. **Header**: `Authorization: Bearer <signature>` or `X-Teams-Signature: <signature>`

### Mathematical Formula

```
signature = base64(HMAC-SHA256(security_token, request_body))
```

### Step-by-Step Process

1. **Teams Side**:
   ```
   request_body = '{"text":"What are sales?","from":{...}}'
   secret = "webhook-security-token"
   
   hmac_hash = HMAC-SHA256(secret, request_body)
   signature = base64_encode(hmac_hash)
   
   Header: Authorization: Bearer <signature>
   ```

2. **Lambda Side**:
   ```
   received_signature = extract_from_header("Authorization")
   expected_signature = base64(HMAC-SHA256(secret, request_body))
   
   if received_signature == expected_signature:
       process_request()
   else:
       return 401 Unauthorized
   ```

---

## Lambda Implementation

### Current Implementation

The Lambda handler includes HMAC verification:

**File (legacy)**: `aws_agent_core/lambda_handlers/teams_webhook_handler.py`

```python
def verify_teams_webhook_signature(
    body: str,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify Teams outgoing webhook HMAC signature.
    
    Args:
        body: Request body as string
        signature: HMAC signature from Teams
        secret: Shared secret configured in Teams
        
    Returns:
        True if signature is valid
    """
    try:
        # Teams uses HMAC SHA256
        expected_signature = base64.b64encode(
            hmac.new(
                secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")
        
        # Compare signatures (constant-time comparison)
        return hmac.compare_digest(signature, expected_signature)
    
    except Exception as e:
        logger.error(f"Error verifying signature: {str(e)}")
        return False
```

### Usage in Lambda Handler

```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # Extract body and headers
    parsed = parse_api_gateway_event(event)
    headers = parsed["headers"]
    body_str = parsed["raw_body"]
    
    # Get webhook secret
    webhook_secret = settings.teams.teams_app_password
    
    if webhook_secret:
        # Extract signature from header
        signature = headers.get("authorization", "").replace("Bearer ", "")
        if not signature:
            signature = headers.get("x-teams-signature", "")
        
        if signature:
            # Verify signature
            if not verify_teams_webhook_signature(body_str, signature, webhook_secret):
                logger.warning("Invalid Teams webhook signature")
                return create_error_response(401, "Invalid signature", "UNAUTHORIZED")
        else:
            logger.warning("Missing Teams webhook signature")
    
    # Process request...
```

### Key Implementation Details

1. **Constant-Time Comparison**
   - Uses `hmac.compare_digest()` instead of `==`
   - Prevents timing attacks
   - Critical for security

2. **Raw Body Required**
   - Must use raw request body (not parsed JSON)
   - Preserves exact formatting
   - No whitespace changes

3. **UTF-8 Encoding**
   - Both secret and body must be UTF-8 encoded
   - Python's `.encode("utf-8")` handles this

4. **Header Extraction**
   - Checks `Authorization: Bearer <sig>` first
   - Falls back to `X-Teams-Signature: <sig>`
   - Removes "Bearer " prefix if present

---

## Postman Testing

### Pre-request Script

Postman can generate HMAC signatures using a pre-request script:

```javascript
// Teams Webhook HMAC Signature Generation
const crypto = require('crypto');

// Get webhook secret from environment
const webhookSecret = pm.environment.get("TEAMS_WEBHOOK_SECRET");

// Get request body (must be raw string, not parsed JSON)
const requestBody = pm.request.body.raw;

// Generate HMAC SHA256 signature
const signature = crypto
    .createHmac('sha256', webhookSecret)
    .update(requestBody)
    .digest('base64');

// Store signature in environment variable
pm.environment.set("SIGNATURE", signature);

// Set Authorization header
pm.request.headers.add({
    key: 'Authorization',
    value: `Bearer ${signature}`
});

// Also set X-Teams-Signature header (alternative)
pm.request.headers.add({
    key: 'X-Teams-Signature',
    value: signature
});

console.log("Generated signature:", signature);
```

### Important Notes for Postman

1. **Body Must Be Raw**
   - Use `raw` body type, not `form-data` or `x-www-form-urlencoded`
   - Body must be exact JSON string (no formatting changes)

2. **Script Execution Order**
   - Pre-request script runs before request is sent
   - Signature is generated from the body that will be sent

3. **Environment Variables**
   - Store `TEAMS_WEBHOOK_SECRET` in environment
   - Never hardcode secrets in scripts

---

## Python Testing Scripts

### Script 1: Generate Signature

```python
#!/usr/bin/env python3
"""
Generate HMAC signature for Teams webhook testing.
"""

import hmac
import hashlib
import base64
import json
import sys

def generate_signature(secret: str, body: str) -> str:
    """
    Generate HMAC SHA256 signature for Teams webhook.
    
    Args:
        secret: Webhook security token
        body: Request body as string
        
    Returns:
        Base64-encoded signature
    """
    signature = base64.b64encode(
        hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256
        ).digest()
    ).decode("utf-8")
    
    return signature


def main():
    # Webhook secret (from Teams)
    if len(sys.argv) > 1:
        secret = sys.argv[1]
    else:
        secret = input("Enter webhook secret: ")
    
    # Request body (Teams webhook payload)
    body = json.dumps({
        "text": "What are the total sales?",
        "from": {
            "id": "29:1test-user-id",
            "name": "Test User"
        },
        "channel": {
            "id": "19:test-channel-id",
            "name": "General"
        },
        "tenant": {
            "id": "test-tenant-id"
        }
    })
    
    # Generate signature
    signature = generate_signature(secret, body)
    
    print("=" * 60)
    print("Teams Webhook HMAC Signature Generator")
    print("=" * 60)
    print()
    print(f"Request Body:")
    print(body)
    print()
    print(f"Signature: {signature}")
    print()
    print(f"Authorization Header: Bearer {signature}")
    print(f"X-Teams-Signature Header: {signature}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python generate_signature.py "your-webhook-secret"
# Or
python generate_signature.py
# (will prompt for secret)
```

### Script 2: Verify Signature

```python
#!/usr/bin/env python3
"""
Verify HMAC signature for Teams webhook.
"""

import hmac
import hashlib
import base64
import sys

def verify_signature(secret: str, body: str, received_signature: str) -> bool:
    """
    Verify HMAC signature.
    
    Args:
        secret: Webhook security token
        body: Request body as string
        received_signature: Signature from request header
        
    Returns:
        True if signature is valid
    """
    expected_signature = base64.b64encode(
        hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256
        ).digest()
    ).decode("utf-8")
    
    return hmac.compare_digest(received_signature, expected_signature)


def main():
    if len(sys.argv) < 4:
        print("Usage: verify_signature.py <secret> <body> <signature>")
        sys.exit(1)
    
    secret = sys.argv[1]
    body = sys.argv[2]
    received_signature = sys.argv[3]
    
    is_valid = verify_signature(secret, body, received_signature)
    
    print("=" * 60)
    print("Teams Webhook HMAC Signature Verification")
    print("=" * 60)
    print()
    print(f"Secret: {secret[:10]}...")
    print(f"Body: {body[:50]}...")
    print(f"Received Signature: {received_signature}")
    print()
    
    if is_valid:
        print("✅ Signature is VALID")
    else:
        print("❌ Signature is INVALID")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python verify_signature.py "secret" '{"text":"test"}' "signature-here"
```

### Script 3: Complete Test Suite

```python
#!/usr/bin/env python3
"""
Complete test suite for Teams webhook HMAC verification.
"""

import hmac
import hashlib
import base64
import json

def test_signature_generation():
    """Test signature generation."""
    secret = "test-secret-123"
    body = '{"text":"test message"}'
    
    signature = base64.b64encode(
        hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    ).decode()
    
    print(f"Test 1: Signature Generation")
    print(f"  Secret: {secret}")
    print(f"  Body: {body}")
    print(f"  Signature: {signature}")
    print()
    
    return signature


def test_signature_verification():
    """Test signature verification."""
    secret = "test-secret-123"
    body = '{"text":"test message"}'
    
    # Generate signature
    valid_signature = base64.b64encode(
        hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    ).decode()
    
    # Verify valid signature
    expected = base64.b64encode(
        hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    ).decode()
    
    is_valid = hmac.compare_digest(valid_signature, expected)
    
    print(f"Test 2: Signature Verification")
    print(f"  Valid signature: {is_valid}")
    print()
    
    # Test invalid signature
    invalid_signature = "invalid-signature-12345"
    is_invalid = hmac.compare_digest(invalid_signature, expected)
    
    print(f"Test 3: Invalid Signature")
    print(f"  Invalid signature rejected: {not is_invalid}")
    print()


def test_teams_payload():
    """Test with actual Teams webhook payload format."""
    secret = "test-secret-123"
    
    payload = {
        "text": "What are the total sales?",
        "from": {
            "id": "29:1test-user-id",
            "name": "Test User"
        },
        "channel": {
            "id": "19:test-channel-id",
            "name": "General"
        },
        "tenant": {
            "id": "test-tenant-id"
        }
    }
    
    body = json.dumps(payload)
    signature = base64.b64encode(
        hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    ).decode()
    
    print(f"Test 4: Teams Payload Format")
    print(f"  Body: {body}")
    print(f"  Signature: {signature}")
    print(f"  Authorization: Bearer {signature}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Teams Webhook HMAC Test Suite")
    print("=" * 60)
    print()
    
    test_signature_generation()
    test_signature_verification()
    test_teams_payload()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Signature Always Fails

**Symptoms:**
- All requests return 401 Unauthorized
- Signature verification always fails

**Solutions:**

1. **Check Secret Match**
   ```python
   # Verify secrets match
   lambda_secret = os.getenv("TEAMS_APP_PASSWORD")
   teams_secret = "secret-from-teams"
   
   assert lambda_secret == teams_secret, "Secrets don't match!"
   ```

2. **Verify Body Encoding**
   - Ensure body is UTF-8 encoded
   - No BOM (Byte Order Mark)
   - No extra whitespace

3. **Check Body Format**
   - Use exact JSON string (not parsed/re-serialized)
   - Preserve original formatting
   - No trailing newlines

#### Issue 2: Signature Works in Postman but Not in Teams

**Symptoms:**
- Postman requests succeed
- Teams requests fail

**Solutions:**

1. **Check Header Name**
   - Teams may use different header
   - Verify Lambda checks both headers

2. **Verify Body Preservation**
   - API Gateway may modify body
   - Check if body is base64 encoded
   - Use `event.body` directly (not parsed)

3. **Check API Gateway Configuration**
   - Ensure body passthrough is enabled
   - Check integration settings

#### Issue 3: Signature Verification Timing Out

**Symptoms:**
- Signature verification takes too long
- Lambda times out

**Solutions:**

1. **Optimize Code**
   - HMAC verification should be fast (< 1ms)
   - Check for blocking operations

2. **Check Secret Retrieval**
   - If using Secrets Manager, cache secret
   - Don't retrieve on every request

---

## Security Best Practices

### 1. Secret Management

- ✅ **Never log secrets** in code or logs
- ✅ **Use AWS Secrets Manager** for production
- ✅ **Rotate secrets** periodically
- ✅ **Use environment variables** for development only

### 2. Signature Verification

- ✅ **Always verify signatures** in production
- ✅ **Use constant-time comparison** (`hmac.compare_digest`)
- ✅ **Log verification failures** for monitoring
- ✅ **Reject invalid signatures** immediately

### 3. Request Validation

- ✅ **Validate request format** before verification
- ✅ **Check required fields** exist
- ✅ **Sanitize input** before processing
- ✅ **Rate limit** requests if needed

### 4. Error Handling

- ✅ **Don't reveal** why verification failed
- ✅ **Log errors** for debugging
- ✅ **Return generic** error messages
- ✅ **Monitor** verification failure rates

---

## Code Examples Summary

### Python (Lambda)

```python
import hmac
import hashlib
import base64

def verify_signature(secret: str, body: str, signature: str) -> bool:
    expected = base64.b64encode(
        hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")
    return hmac.compare_digest(signature, expected)
```

### JavaScript (Postman)

```javascript
const crypto = require('crypto');
const secret = pm.environment.get("TEAMS_WEBHOOK_SECRET");
const body = pm.request.body.raw;
const signature = crypto.createHmac('sha256', secret).update(body).digest('base64');
pm.request.headers.add({key: 'Authorization', value: `Bearer ${signature}`});
```

### Bash (cURL Testing)

```bash
#!/bin/bash
SECRET="your-webhook-secret"
BODY='{"text":"test"}'

SIGNATURE=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)

curl -X POST https://your-api-gateway-url/api/teams/webhook \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SIGNATURE" \
  -d "$BODY"
```

---

## Quick Reference

### Signature Generation Formula

```
HMAC-SHA256(secret, body) → base64 → signature
```

### Header Format

```
Authorization: Bearer <signature>
X-Teams-Signature: <signature>  (alternative)
```

### Verification Steps

1. Extract signature from header
2. Get webhook secret
3. Compute expected signature
4. Compare signatures (constant-time)
5. Process if valid, reject if invalid

---

**Last Updated**: 2024  
**Maintained By**: Multi-Agent Orchestrator Team
