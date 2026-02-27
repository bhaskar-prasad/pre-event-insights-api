#!/usr/bin/env python3
"""
Test script to verify the domain path normalization fix.
"""

import re

def normalize_domain_path(path: str) -> str:
    """
    Normalize API path by replacing IDs with {id} placeholder.

    Args:
        path: API path

    Returns:
        Normalized path
    """
    # Replace numeric IDs, UUIDs, and alphanumeric IDs (with underscores/dashes) with {id}
    # Matches: 123, 550e8400-e29b-41d4-a716-446655440000, campaign_001, user-123, etc.
    normalized = re.sub(
        r"(?:/|^)(\d+|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}|[a-z0-9]*[_-][a-z0-9]*)(?=/|$)",
        "/{id}",
        path,
    )
    return normalized


# Test cases
test_cases = [
    ("/campaigns", "/campaigns"),  # No change - literal route
    ("/campaigns/123", "/campaigns/{id}"),  # Numeric ID
    ("/campaigns/123/attendees", "/campaigns/{id}/attendees"),  # Numeric ID with subroute
    ("/campaigns/campaign_001", "/campaigns/{id}"),  # Alphanumeric with underscore
    ("/campaigns/campaign_001/attendees", "/campaigns/{id}/attendees"),  # The failing case
    ("/campaigns/user-456", "/campaigns/{id}"),  # Alphanumeric with dash
    ("/campaigns/550e8400-e29b-41d4-a716-446655440000/attendees", "/campaigns/{id}/attendees"),  # UUID
    ("/campaigns/attendees", "/campaigns/attendees"),  # Should NOT change - route name
]

print("🧪 Testing domain path normalization:\n")
all_passed = True

for input_path, expected in test_cases:
    result = normalize_domain_path(input_path)
    status = "✅" if result == expected else "❌"
    if result != expected:
        all_passed = False
    print(f"{status} Input: {input_path}")
    print(f"   Expected: {expected}")
    print(f"   Got:      {result}\n")

if all_passed:
    print("✨ All tests passed!")
else:
    print("⚠️  Some tests failed!")
