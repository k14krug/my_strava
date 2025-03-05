#!/bin/bash
# filepath: /home/kkrug/projects/strava/strava_auth.sh

set -e  # Exit on error

# Default activity ID to test
DEFAULT_ACTIVITY_ID="13781691455"
ACTIVITY_ID=${DEFAULT_ACTIVITY_ID}

# ANSI color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to check if required commands are available
check_requirements() {
  for cmd in curl jq; do
    if ! command -v $cmd &> /dev/null; then
      print_error "$cmd is required but not installed. Please install it and try again."
      exit 1
    fi
  done
}

# Load existing environment variables
load_env_vars() {
  if [ -f .env ]; then
    print_info "Loading variables from .env file..."
    export $(grep -v '^#' .env | xargs)
  fi
}

# Save tokens to .env file
save_to_env() {
  local env_file=".env"
  local key=$1
  local value=$2
  
  # Create file if it doesn't exist
  touch $env_file
  
  # Check if key exists
  if grep -q "^${key}=" $env_file; then
    # Replace existing key
    sed -i "s|^${key}=.*|${key}=${value}|" $env_file
  else
    # Add new key
    echo "${key}=${value}" >> $env_file
  fi
  
  print_success "Saved $key to $env_file"
}

# Generate authorization URL
generate_auth_url() {
  if [ -z "$STRAVA_CLIENT_ID" ]; then
    print_error "STRAVA_CLIENT_ID is not set"
    exit 1
  fi

  print_info "Visit this URL in your browser to authorize the application:"
  echo -e "${YELLOW}https://www.strava.com/oauth/authorize?client_id=${STRAVA_CLIENT_ID}&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=read_all,activity:read_all,profile:read_all${NC}"
  echo ""
  print_info "After authorization, you'll be redirected to a URL like:"
  echo -e "${YELLOW}http://localhost/?state=&code=AUTHORIZATION_CODE${NC}"
  echo ""

  # Prompt for the authorization code
  read -p "Enter the authorization code from the URL: " auth_code
  
  if [ -z "$auth_code" ]; then
    print_error "No authorization code provided"
    exit 1
  fi
  
  echo ""
  exchange_auth_code "$auth_code"
}

# Exchange authorization code for tokens
exchange_auth_code() {
  local auth_code=$1
  
  print_info "Exchanging authorization code for tokens..."
  local token_response=$(curl -s -X POST https://www.strava.com/oauth/token \
    -d client_id=$STRAVA_CLIENT_ID \
    -d client_secret=$STRAVA_CLIENT_SECRET \
    -d code=$auth_code \
    -d grant_type=authorization_code)
  
  echo "$token_response" | jq .
  
  # Extract tokens
  local access_token=$(echo "$token_response" | jq -r '.access_token')
  local refresh_token=$(echo "$token_response" | jq -r '.refresh_token')
  local expires_at=$(echo "$token_response" | jq -r '.expires_at')
  
  if [ "$access_token" == "null" ] || [ -z "$access_token" ]; then
    print_error "Failed to get access token"
    return 1
  fi
  
  # Save tokens to environment variables
  export STRAVA_ACCESS_TOKEN=$access_token
  export STRAVA_REFRESH_TOKEN=$refresh_token
  export STRAVA_TOKEN_EXPIRES_AT=$expires_at
  
  # Save tokens to .env file
  save_to_env "STRAVA_ACCESS_TOKEN" "$access_token"
  save_to_env "STRAVA_REFRESH_TOKEN" "$refresh_token" 
  save_to_env "STRAVA_TOKEN_EXPIRES_AT" "$expires_at"
  
  print_success "Token exchange successful"
  return 0
}

# Refresh access token using refresh token
refresh_access_token() {
  print_info "Refreshing access token..."
  
  if [ -z "$STRAVA_CLIENT_ID" ] || [ -z "$STRAVA_CLIENT_SECRET" ] || [ -z "$STRAVA_REFRESH_TOKEN" ]; then
    print_error "Missing required credentials. Please check your environment variables."
    exit 1
  fi
  
  local token_response=$(curl -s -X POST "https://www.strava.com/oauth/token" \
    -d "client_id=$STRAVA_CLIENT_ID" \
    -d "client_secret=$STRAVA_CLIENT_SECRET" \
    -d "grant_type=refresh_token" \
    -d "refresh_token=$STRAVA_REFRESH_TOKEN")
  
  # Extract tokens
  local access_token=$(echo "$token_response" | jq -r '.access_token')
  local refresh_token=$(echo "$token_response" | jq -r '.refresh_token')
  local expires_at=$(echo "$token_response" | jq -r '.expires_at')
  local expires_in=$(echo "$token_response" | jq -r '.expires_in')
  
  if [ "$access_token" == "null" ] || [ -z "$access_token" ]; then
    print_error "Failed to refresh token: $(echo "$token_response" | jq -r '.message // "Unknown error"')"
    return 1
  fi
  
  # Save tokens to environment variables
  export STRAVA_ACCESS_TOKEN=$access_token
  export STRAVA_REFRESH_TOKEN=$refresh_token
  export STRAVA_TOKEN_EXPIRES_AT=$expires_at
  
  # Save tokens to .env file
  save_to_env "STRAVA_ACCESS_TOKEN" "$access_token"
  save_to_env "STRAVA_REFRESH_TOKEN" "$refresh_token" 
  save_to_env "STRAVA_TOKEN_EXPIRES_AT" "$expires_at"
  
  print_success "New access token acquired (expires in $expires_in seconds)"
  return 0
}

# Test athlete endpoint
test_athlete() {
  print_info "Testing athlete API..."
  local response=$(curl -s -H "Authorization: Bearer ${STRAVA_ACCESS_TOKEN}" \
    "https://www.strava.com/api/v3/athlete")
  
  if echo "$response" | jq -e 'has("message")' > /dev/null; then
    print_error "Athlete API error: $(echo "$response" | jq -r '.message')"
    return 1
  fi
  
  local athlete_id=$(echo "$response" | jq -r '.id')
  local athlete_name=$(echo "$response" | jq -r '.firstname + " " + .lastname')
  
  print_success "Successfully retrieved athlete data for $athlete_name (ID: $athlete_id)"
  echo "$response" | jq '{id, username, firstname, lastname, city, state, country}'
  return 0
}

# Test activities endpoint
test_activities() {
  print_info "Testing activities API..."
  local response=$(curl -s -H "Authorization: Bearer ${STRAVA_ACCESS_TOKEN}" \
    "https://www.strava.com/api/v3/athlete/activities?per_page=1")
  
  if echo "$response" | jq -e 'if type=="object" then has("message") else false end' > /dev/null; then
    print_error "Activities API error: $(echo "$response" | jq -r '.message')"
    return 1
  fi
  
  local activity_count=$(echo "$response" | jq 'length')
  
  print_success "Retrieved $activity_count recent activity"
  echo "$response" | jq -r '.[] | {id, name, start_date, distance, moving_time}'
  
  # Use the specified activity ID or the first activity ID if none was specified
  if [ "$ACTIVITY_ID" == "$DEFAULT_ACTIVITY_ID" ]; then
    ACTIVITY_ID=$(echo "$response" | jq -r '.[0].id')
    print_info "Using first activity (ID: $ACTIVITY_ID) for further testing"
  fi
  
  # Retrieve and display details for the specified activity ID
  local activity_response=$(curl -s -H "Authorization: Bearer ${STRAVA_ACCESS_TOKEN}" \
    "https://www.strava.com/api/v3/activities/${ACTIVITY_ID}")
  
  if echo "$activity_response" | jq -e 'has("message")' > /dev/null; then
    print_error "Activity API error: $(echo "$activity_response" | jq -r '.message')"
    return 1
  fi
  
  print_success "Details for activity ID $ACTIVITY_ID:"
  echo "$activity_response" | jq '{id, name, start_date, distance, moving_time}'
  
  return 0
}

# Test activity streams endpoint
test_streams() {
  print_info "Testing streams API for activity $ACTIVITY_ID..."
  local response=$(curl -s -H "Authorization: Bearer ${STRAVA_ACCESS_TOKEN}" \
    "https://www.strava.com/api/v3/activities/${ACTIVITY_ID}/streams?keys=time,distance,latlng,altitude,velocity_smooth,heartrate,cadence,watts,temp,moving,grade_smooth&key_by_type=true")
  
  if echo "$response" | jq -e 'has("message")' > /dev/null; then
    print_error "Streams API error: $(echo "$response" | jq -r '.message')"
    return 1
  fi
  
  local available_streams=$(echo "$response" | jq 'keys | join(", ")')
  print_success "Successfully retrieved streams: $available_streams"
  
  # Show summary of stream data points
  echo "$response" | jq 'map_values(.data | length)'
  return 0
}

# Test segments for activity
test_segments() {
  print_info "Testing segments for activity $ACTIVITY_ID..."
  local response=$(curl -s -H "Authorization: Bearer ${STRAVA_ACCESS_TOKEN}" \
    "https://www.strava.com/api/v3/activities/${ACTIVITY_ID}")
  
  if echo "$response" | jq -e 'has("message")' > /dev/null; then
    print_error "Activity API error: $(echo "$response" | jq -r '.message')"
    return 1
  fi
  
  # Check if activity has segment efforts
  local segment_efforts=$(echo "$response" | jq '.segment_efforts // []')
  local segment_count=$(echo "$segment_efforts" | jq 'length')
  
  if [ "$segment_count" -eq 0 ]; then
    print_warning "No segments found for activity $ACTIVITY_ID"
    return 0
  fi
  
  print_success "Found $segment_count segment efforts in activity"
  echo "$segment_efforts" | jq -r '.[] | {name: .name, id: .segment.id, distance: .segment.distance, elapsed_time: .elapsed_time}'
  
  # Get details for first segment
  local first_segment_id=$(echo "$segment_efforts" | jq -r '.[0].segment.id')
  
  if [ -n "$first_segment_id" ]; then
    print_info "Getting details for segment $first_segment_id..."
    local segment_response=$(curl -s -H "Authorization: Bearer ${STRAVA_ACCESS_TOKEN}" \
      "https://www.strava.com/api/v3/segments/${first_segment_id}")
    
    if echo "$segment_response" | jq -e 'has("message")' > /dev/null; then
      print_error "Segment API error: $(echo "$segment_response" | jq -r '.message')"
    else
      print_success "Successfully retrieved segment details"
      echo "$segment_response" | jq '. | {name, distance, average_grade, maximum_grade, elevation_high, elevation_low, total_elevation_gain}'
    fi
  fi
  
  return 0
}

# Main menu function
show_menu() {
  echo -e "\n${BLUE}=== Strava API Authorization & Testing Tool ===${NC}"
  echo "1. Generate new authorization URL"
  echo "2. Refresh access token using existing refresh token"
  echo "3. Test athlete API"
  echo "4. Test activities API"
  echo "5. Test streams API"
  echo "6. Test segments API"
  echo "7. Run all tests"
  echo "8. Change activity ID for testing (current: $ACTIVITY_ID)"
  echo "9. Exit"
  echo -n "Enter your choice [1-9]: "
  
  read choice
  echo ""
  
  case $choice in
    1) generate_auth_url ;;
    2) refresh_access_token ;;
    3) test_athlete ;;
    4) test_activities ;;
    5) test_streams ;;
    6) test_segments ;;
    7)
      refresh_access_token &&
      test_athlete &&
      test_activities &&
      test_streams &&
      test_segments
      ;;
    8)
      read -p "Enter activity ID: " new_id
      if [ -n "$new_id" ]; then
        ACTIVITY_ID=$new_id
        print_info "Activity ID set to $ACTIVITY_ID"
      fi
      ;;
    9) exit 0 ;;
    *)
      print_error "Invalid option"
      ;;
  esac
  
  # Press any key to continue
  read -n 1 -s -r -p "Press any key to continue..."
  echo ""
}

# Main function
main() {
  check_requirements
  load_env_vars
  
  # Check for command line arguments
  if [ "$#" -gt 0 ]; then
    case $1 in
      --new-auth)
        generate_auth_url
        ;;
      --refresh)
        refresh_access_token
        ;;
      --test-all)
        refresh_access_token &&
        test_athlete &&
        test_activities &&
        test_streams &&
        test_segments
        ;;
      --activity)
        if [ -n "$2" ]; then
          ACTIVITY_ID=$2
        fi
        refresh_access_token &&
        test_streams &&
        test_segments
        ;;
      --help)
        echo "Usage: $0 [OPTION]"
        echo "Options:"
        echo "  --new-auth             Generate new authorization URL"
        echo "  --refresh              Refresh access token using existing refresh token"
        echo "  --test-all             Run all API tests"
        echo "  --activity ACTIVITY_ID Test specific activity ID"
        echo "  --help                 Show this help message"
        echo "Without options, the script shows an interactive menu."
        exit 0
        ;;
      *)
        print_error "Unknown option: $1"
        print_info "Use --help for usage information"
        exit 1
        ;;
    esac
    exit 0
  fi
  
  # No arguments, show interactive menu
  while true; do
    show_menu
  done
}

# Run main function
main "$@"