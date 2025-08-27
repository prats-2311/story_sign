# StorySign External Integration Usage Guide

## Quick Start

The StorySign platform now supports comprehensive external integrations. Here's how to get started:

### 1. Database Setup

First, create the integration tables:

```bash
cd StorySign_Platform/backend
python create_integration_tables_standalone.py
```

This will create all necessary tables for OAuth, SAML, LTI, webhooks, and embeddable widgets.

### 2. API Testing

Verify the integration system works:

```bash
python test_integration_api.py
```

All tests should pass ✅

## Integration Methods

### OAuth2 Authentication

**Setup OAuth Provider:**

```bash
curl -X POST http://localhost:8000/api/v1/integrations/oauth/providers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "name": "google",
    "client_id": "your-google-client-id",
    "client_secret": "your-google-client-secret",
    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo"
  }'
```

**User Login Flow:**

1. Redirect user to: `GET /api/v1/integrations/oauth/google/authorize?redirect_uri=...`
2. Handle callback: `POST /api/v1/integrations/oauth/google/callback`
3. Receive JWT tokens for authenticated user

### SAML SSO Integration

**Get SAML Metadata:**

```bash
curl http://localhost:8000/api/v1/integrations/saml/metadata
```

**Configure Identity Provider:**

- Use the metadata XML to configure your IdP
- Set assertion consumer service URL to `/api/v1/integrations/saml/sso`
- Users will be automatically created/logged in from SAML assertions

### LTI Integration

**LMS Configuration:**

- Consumer Key: `storysign-consumer`
- Consumer Secret: `your-lti-secret`
- Launch URL: `http://localhost:8000/api/v1/integrations/lti/launch`

**Launch Process:**

- LMS sends signed LTI launch request
- StorySign validates signature and creates/logs in user
- User is redirected to StorySign with active session

### Webhooks

**Create Webhook:**

```bash
curl -X POST http://localhost:8000/api/v1/integrations/webhooks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "LMS Integration",
    "url": "https://your-lms.com/storysign-webhook",
    "events": ["session.completed", "progress.updated"],
    "secret": "your-webhook-secret"
  }'
```

**Webhook Events:**

- `user.registered` - New user account created
- `session.completed` - Practice session finished
- `progress.updated` - User progress changed
- `story.completed` - User completed a story
- And more...

**Webhook Payload Example:**

```json
{
  "event_type": "session.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "user_id": "user-123",
  "data": {
    "session_id": "session-456",
    "story_id": "story-789",
    "score": 92,
    "duration": 15,
    "sentences_completed": 8
  }
}
```

### Embeddable Widgets

**Practice Widget:**

```html
<div id="storysign-practice"></div>
<script src="http://localhost:8000/api/v1/integrations/embed/script/practice?domain=yoursite.com"></script>
<script>
  StorySignWidget.init({
    containerId: "storysign-practice",
    userId: "user-123",
    width: 800,
    height: 600,
    theme: "blue",
  });
</script>
```

**Progress Widget:**

```html
<iframe
  src="http://localhost:8000/api/v1/integrations/embed/widget/progress?domain=yoursite.com&user_id=user-123"
  width="400"
  height="300"
  frameborder="0"
>
</iframe>
```

**Leaderboard Widget:**

```html
<div id="storysign-leaderboard"></div>
<script src="http://localhost:8000/api/v1/integrations/embed/script/leaderboard?domain=yoursite.com"></script>
<script>
  StorySignWidget.init({
    containerId: "storysign-leaderboard",
    groupId: "class-2024",
    width: 500,
    height: 400,
  });
</script>
```

### Data Synchronization

**Export User Progress:**

```bash
# JSON format
curl "http://localhost:8000/api/v1/integrations/sync/progress/user-123?format=json" \
  -H "Authorization: Bearer YOUR_TOKEN"

# CSV format
curl "http://localhost:8000/api/v1/integrations/sync/progress/user-123?format=csv" \
  -H "Authorization: Bearer YOUR_TOKEN"

# XML format
curl "http://localhost:8000/api/v1/integrations/sync/progress/user-123?format=xml" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Import Users from External System:**

```bash
curl -X POST http://localhost:8000/api/v1/integrations/sync/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "source_system": "school_lms",
    "users": [
      {
        "external_id": "student_001",
        "email": "alice@school.edu",
        "first_name": "Alice",
        "last_name": "Johnson",
        "role": "learner"
      }
    ]
  }'
```

## Security Configuration

### API Keys

Create API keys for external system access:

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "name": "LMS Integration Key",
    "scopes": ["read:users", "read:progress", "write:webhooks"],
    "rate_limit": 1000,
    "expires_at": "2024-12-31T23:59:59Z"
  }'
```

### Rate Limiting

Default rate limits:

- **General API**: 100 requests/hour, burst 20
- **Authentication**: 5 requests/5min, burst 2
- **OAuth Callback**: 10 requests/5min, burst 5
- **Webhooks**: 1000 requests/hour, burst 100

### Domain Whitelisting

For embeddable widgets, configure allowed domains:

```bash
curl -X POST http://localhost:8000/api/v1/integrations/embed/configs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "widget_type": "practice",
    "domain": "school.edu",
    "features": ["video_practice", "gesture_feedback"],
    "theme": {"primary_color": "#007bff"}
  }'
```

## Integration Examples

### Canvas LMS Integration

1. **LTI Setup**: Configure StorySign as external tool in Canvas
2. **Grade Passback**: Use webhooks to send scores back to Canvas
3. **User Sync**: Import Canvas users via API

### Google Classroom Integration

1. **OAuth Setup**: Configure Google OAuth for SSO
2. **Assignment Integration**: Create assignments that launch StorySign
3. **Progress Sharing**: Export progress data to Google Sheets

### Moodle Integration

1. **SAML SSO**: Configure Moodle as SAML identity provider
2. **Embedded Activities**: Use widgets in Moodle courses
3. **Grade Sync**: Webhook integration for automatic grading

## Monitoring and Troubleshooting

### Webhook Delivery Logs

Check webhook delivery status:

```bash
curl "http://localhost:8000/api/v1/integrations/webhooks/webhook-id/deliveries" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Integration Events

View integration audit log:

```bash
curl "http://localhost:8000/api/v1/integrations/events?type=oauth&success=false" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Webhook

Test webhook delivery:

```bash
curl -X POST http://localhost:8000/api/v1/integrations/webhooks/test \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "webhook_id": "webhook-123",
    "test_event": {
      "event_type": "user.registered",
      "user_id": "test-user",
      "data": {"email": "test@example.com"}
    }
  }'
```

## Common Issues

### OAuth Callback Errors

- Verify redirect URI matches exactly
- Check client ID and secret
- Ensure HTTPS in production

### Webhook Delivery Failures

- Verify webhook URL is accessible
- Check signature verification
- Review webhook logs for errors

### Widget Embedding Issues

- Confirm domain is whitelisted
- Check CORS headers
- Verify iframe permissions

### SAML Authentication Problems

- Validate SAML metadata
- Check certificate configuration
- Verify assertion format

## Support

For integration support:

1. Check the API documentation at `/docs`
2. Review integration event logs
3. Test with provided sample configurations
4. Contact support with specific error messages

The StorySign integration system is designed to be flexible and secure, supporting a wide range of external systems and use cases.
