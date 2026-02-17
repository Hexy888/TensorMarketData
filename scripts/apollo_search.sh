#!/bin/bash
# Apollo Lead Search - Working Version

API_KEY="kw_KuGhJAIw3DNrCyHdQSQ"

# Find people at specific company
search_by_company() {
    curl -s -X POST "https://api.apollo.io/api/v1/mixed_people/api_search" \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      --data-raw "{\"q_organization_name\": \"$1\", \"per_page\": $2}"
}

# Find people by title at any company  
search_by_title() {
    curl -s -X POST "https://api.apollo.io/api/v1/mixed_people/api_search" \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      --data-raw "{\"title\": [\"$1\"], \"per_page\": $2}"
}

# Search with multiple filters
search_ai_leads() {
    curl -s -X POST "https://api.apollo.io/api/v1/mixed_people/api_search" \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      --data-raw '{
        "q_organization_name": "'"$1"'",
        "title": ["CEO", "CTO", "VP Engineering", "VP Sales", "Head of Growth", "Founder"],
        "per_page": '"$2"'
      }'
}

# Example usage
case "$1" in
  company)
    search_by_company "$2" "${3:-10}"
    ;;
  title)
    search_by_title "$2" "${3:-10}"
    ;;
  ai)
    search_ai_leads "$2" "${3:-10}"
    ;;
  *)
    echo "Usage: $0 {company <name> <count>|title <title> <count>|ai <company> <count>}"
    echo ""
    echo "Examples:"
    echo "  $0 company OpenAI 5"
    echo "  $0 title CEO 10"  
    echo "  $0 ai Anthropic 10"
    ;;
esac
