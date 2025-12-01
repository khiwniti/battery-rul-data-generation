# Battery RUL Prediction API - Complete Reference

**Base URL**: `https://your-backend.railway.app`
**API Version**: v1.0.0
**API Prefix**: `/api/v1`

---

## Table of Contents

1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [Locations](#locations)
4. [Batteries](#batteries)
5. [Alerts](#alerts)
6. [WebSocket](#websocket)
7. [Error Codes](#error-codes)

---

## Authentication

All API endpoints (except `/health` and `/auth/login`) require JWT authentication via Bearer token.

### Headers

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

### POST /api/v1/auth/login

Login with username and password.

**Request Body:**
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "user_id": "admin",
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": true
  }
}
```

**Errors:**
- `401`: Invalid credentials or inactive user

---

### POST /api/v1/auth/refresh

Refresh expired access token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401`: Invalid refresh token

---

### POST /api/v1/auth/logout

Logout (client-side token deletion).

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

---

### GET /api/v1/auth/me

Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "user_id": "admin",
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "System Administrator",
  "role": "admin",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

---

### POST /api/v1/auth/change-password

Change current user's password.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "current_password": "old_password",
  "new_password": "new_password123"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

**Errors:**
- `401`: Incorrect current password

---

## User Management (Admin Only)

### GET /api/v1/auth/users

List all users.

**Headers:** `Authorization: Bearer <admin_token>`

**Query Parameters:**
- `skip` (int, default: 0) - Pagination offset
- `limit` (int, default: 100, max: 1000) - Results per page

**Response (200 OK):**
```json
{
  "users": [
    {
      "user_id": "admin",
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "System Administrator",
      "role": "admin",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

**Errors:**
- `403`: Admin access required

---

### POST /api/v1/auth/users

Create new user.

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "user_id": "engineer1",
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure123",
  "full_name": "John Doe",
  "role": "engineer"
}
```

**Response (201 Created):**
```json
{
  "user_id": "engineer1",
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "engineer",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Errors:**
- `400`: User already exists or invalid role
- `403`: Admin access required

---

### PATCH /api/v1/auth/users/{user_id}

Update user.

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body (all fields optional):**
```json
{
  "email": "new_email@example.com",
  "full_name": "New Name",
  "role": "admin",
  "is_active": false
}
```

**Response (200 OK):** UserResponse

**Errors:**
- `404`: User not found
- `400`: Invalid role
- `403`: Admin access required

---

### DELETE /api/v1/auth/users/{user_id}

Delete user.

**Headers:** `Authorization: Bearer <admin_token>`

**Response (200 OK):**
```json
{
  "message": "User engineer1 deleted successfully"
}
```

**Errors:**
- `404`: User not found
- `400`: Cannot delete self
- `403`: Admin access required

---

## Locations

### GET /api/v1/locations

List all data center locations with battery statistics.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `include_stats` (bool, default: true) - Include battery counts

**Response (200 OK):**
```json
{
  "locations": [
    {
      "location_id": "DC-CNX-01",
      "name": "Chiang Mai Data Center",
      "region": "northern",
      "city": "Chiang Mai",
      "country": "Thailand",
      "latitude": 18.7883,
      "longitude": 98.9853,
      "temp_offset_c": -2.0,
      "humidity_offset_pct": -5.0,
      "power_outage_frequency_per_year": 2,
      "total_batteries": 216,
      "active_batteries": 216,
      "critical_batteries": 3,
      "average_soh": 92.5,
      "active_alerts": 5
    }
  ],
  "total": 9
}
```

---

### GET /api/v1/locations/{location_id}

Get location details.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):** LocationWithStats (same as list item)

**Errors:**
- `404`: Location not found

---

### GET /api/v1/locations/{location_id}/batteries

Get all batteries at location.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 1000)

**Response (200 OK):**
```json
{
  "batteries": [...],
  "total": 216
}
```

---

## Batteries

### GET /api/v1/batteries

List batteries with latest telemetry.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `location_id` (string, optional) - Filter by location
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 1000)

**Response (200 OK):**
```json
{
  "batteries": [
    {
      "battery_id": "BAT-DC-CNX-01-UPS-01-STR-01-001",
      "serial_number": "CSB-HX12-120-2023-001234",
      "position": 1,
      "manufacturer": "CSB",
      "model": "HX12-120",
      "nominal_voltage_v": 12.0,
      "nominal_capacity_ah": 120.0,
      "installed_date": "2023-01-15",
      "warranty_months": 60,
      "string_id": "uuid-...",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "latest_telemetry": {
        "timestamp": "2025-11-30T08:00:00Z",
        "voltage": 13.2,
        "current": -2.5,
        "temperature": 28.5,
        "internal_resistance": 0.0045,
        "soc_pct": 95.0,
        "soh_pct": 92.0
      },
      "status": "healthy",
      "active_alerts": 0
    }
  ],
  "total": 216
}
```

---

### GET /api/v1/batteries/{battery_id}

Get battery details.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "battery_id": "BAT-DC-CNX-01-UPS-01-STR-01-001",
  "...": "...",
  "latest_telemetry": {...},
  "status": "healthy",
  "active_alerts": 0,
  "age_days": 680,
  "is_in_warranty": true,
  "string_info": {
    "string_id": "STR-DC-CNX-01-UPS-01-01",
    "position": 1
  },
  "location_info": {
    "location_id": "DC-CNX-01",
    "name": "Chiang Mai Data Center"
  }
}
```

**Errors:**
- `404`: Battery not found

---

### GET /api/v1/batteries/{battery_id}/telemetry

Get battery telemetry time-series data.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `start` (datetime, optional, default: 24h ago) - Start timestamp
- `end` (datetime, optional, default: now) - End timestamp
- `limit` (int, default: 1000, max: 10000) - Maximum results

**Response (200 OK):**
```json
{
  "battery_id": "BAT-DC-CNX-01-UPS-01-STR-01-001",
  "start": "2025-11-29T08:00:00Z",
  "end": "2025-11-30T08:00:00Z",
  "data": [
    {
      "timestamp": "2025-11-30T08:00:00Z",
      "voltage": 13.2,
      "current": -2.5,
      "temperature": 28.5,
      "internal_resistance": 0.0045,
      "soc_pct": 95.0,
      "soh_pct": 92.0
    }
  ],
  "count": 1440
}
```

---

## Alerts

### GET /api/v1/alerts

List alerts with filters.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `location_id` (string, optional)
- `severity` (string, optional) - `info`, `warning`, `critical`
- `alert_type` (string, optional) - e.g., `voltage_high`, `temperature_high`
- `active_only` (bool, default: true)
- `acknowledged` (bool, optional)
- `start_date` (datetime, optional)
- `end_date` (datetime, optional)
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 1000)

**Response (200 OK):**
```json
{
  "alerts": [
    {
      "id": "uuid-...",
      "alert_id": "ALT-BAT-...-2025-11-30-...",
      "battery_id": "BAT-DC-CNX-01-UPS-01-STR-01-001",
      "alert_type": "temperature_high",
      "severity": "warning",
      "message": "Battery temperature 45.2°C exceeds threshold 45.0°C",
      "threshold_value": 45.0,
      "actual_value": 45.2,
      "triggered_at": "2025-11-30T08:00:00Z",
      "resolved_at": null,
      "is_acknowledged": false,
      "acknowledged_at": null,
      "acknowledged_by": null,
      "acknowledgment_note": null,
      "created_at": "2025-11-30T08:00:00Z",
      "updated_at": "2025-11-30T08:00:00Z",
      "is_active": true,
      "is_pending": true
    }
  ],
  "total": 50,
  "active_count": 25,
  "pending_count": 15
}
```

---

### GET /api/v1/alerts/stats

Get alert statistics.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `location_id` (string, optional)
- `days` (int, default: 7, range: 1-365)

**Response (200 OK):**
```json
{
  "total_alerts": 150,
  "active_alerts": 25,
  "critical_alerts": 5,
  "warning_alerts": 18,
  "info_alerts": 2,
  "acknowledged_alerts": 125,
  "alerts_by_type": {
    "temperature_high": 45,
    "voltage_high": 30,
    "soh_degraded": 25,
    "rul_warning": 20,
    "resistance_drift": 15,
    "rul_critical": 10,
    "voltage_low": 5
  },
  "alerts_by_location": {
    "DC-CNX-01": 25,
    "DC-BKK-01": 40,
    "DC-HDY-01": 30
  }
}
```

---

### GET /api/v1/alerts/{alert_id}

Get alert details with battery context.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "...": "...",
  "battery_serial": "CSB-HX12-120-2023-001234",
  "battery_position": 1,
  "location_id": "DC-CNX-01",
  "location_name": "Chiang Mai Data Center"
}
```

**Errors:**
- `404`: Alert not found

---

### POST /api/v1/alerts/{alert_id}/acknowledge

Acknowledge an alert (Engineer+ only).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "note": "Battery temperature normalized after HVAC repair"
}
```

**Response (200 OK):** AlertResponse

**Errors:**
- `404`: Alert not found
- `400`: Alert already acknowledged
- `403`: Engineer/Admin access required

---

### POST /api/v1/alerts/{alert_id}/resolve

Manually resolve an alert (Engineer+ only).

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):** AlertResponse

**Errors:**
- `404`: Alert not found
- `400`: Alert already resolved
- `403`: Engineer/Admin access required

---

## WebSocket

Real-time battery telemetry and alerts via Socket.IO.

**Connection URL**: `wss://your-backend.railway.app/socket.io`

### Connection

```javascript
import io from 'socket.io-client';

const socket = io('https://your-backend.railway.app', {
  auth: {
    token: 'YOUR_JWT_TOKEN'
  },
  transports: ['websocket', 'polling']
});

socket.on('connected', (data) => {
  console.log('Connected:', data);
});
```

### Client Events (Emit)

**subscribe_location**
```javascript
socket.emit('subscribe_location', {
  location_id: 'DC-CNX-01'
});
```

**unsubscribe_location**
```javascript
socket.emit('unsubscribe_location', {
  location_id: 'DC-CNX-01'
});
```

**subscribe_battery**
```javascript
socket.emit('subscribe_battery', {
  battery_id: 'BAT-DC-CNX-01-UPS-01-STR-01-001'
});
```

**unsubscribe_battery**
```javascript
socket.emit('unsubscribe_battery', {
  battery_id: 'BAT-DC-CNX-01-UPS-01-STR-01-001'
});
```

**ping**
```javascript
socket.emit('ping', {});
```

### Server Events (Listen)

**connected**
```javascript
socket.on('connected', (data) => {
  // { message: 'Connected to Battery RUL Monitoring', timestamp: '...' }
});
```

**subscribed**
```javascript
socket.on('subscribed', (data) => {
  // { type: 'location', location_id: 'DC-CNX-01', timestamp: '...' }
});
```

**telemetry_update**
```javascript
socket.on('telemetry_update', (data) => {
  console.log('Telemetry:', data);
  // {
  //   battery_id: 'BAT-...',
  //   data: { voltage: 13.2, temperature: 28.5, ... },
  //   timestamp: '...'
  // }
});
```

**alert**
```javascript
socket.on('alert', (data) => {
  console.log('Alert:', data);
  // {
  //   battery_id: 'BAT-...',
  //   location_id: 'DC-CNX-01',
  //   severity: 'critical',
  //   message: '...',
  //   ...
  // }
});
```

**battery_status_update**
```javascript
socket.on('battery_status_update', (data) => {
  // {
  //   battery_id: 'BAT-...',
  //   data: { status: 'warning', soh_pct: 85.0, ... },
  //   timestamp: '...'
  // }
});
```

**pong**
```javascript
socket.on('pong', (data) => {
  // { timestamp: '...' }
});
```

**error**
```javascript
socket.on('error', (data) => {
  console.error('WebSocket error:', data);
});
```

---

## Error Codes

### HTTP Status Codes

- `200` - OK (successful request)
- `201` - Created (resource created)
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource not found)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

### Common Errors

**401 Unauthorized:**
- "Could not validate credentials"
- "Incorrect username or password"
- "User account is inactive"
- "Invalid refresh token"

**403 Forbidden:**
- "Admin access required"
- "Engineer access required"

**404 Not Found:**
- "Location {location_id} not found"
- "Battery {battery_id} not found"
- "Alert {alert_id} not found"
- "User {user_id} not found"

**400 Bad Request:**
- "User with this user_id or username already exists"
- "Invalid role: {role}. Must be one of: admin, engineer, viewer"
- "Cannot delete your own account"
- "Alert has already been acknowledged"
- "Alert has already been resolved"

---

## Rate Limiting

No rate limiting currently implemented. Recommended for production:
- `/auth/login`: 5 requests/minute per IP
- Other endpoints: 100 requests/minute per user

---

## Pagination

All list endpoints support pagination:
- `skip` (offset): Default 0
- `limit` (page size): Default 100, max 1000

Example:
```
GET /api/v1/batteries?skip=0&limit=50
```

---

## Timestamps

All timestamps in ISO 8601 format with UTC timezone:
```
2025-11-30T08:00:00Z
```

---

## Health Check

### GET /health

Public endpoint (no auth required).

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "backend-api",
  "version": "1.0.0",
  "environment": "production"
}
```

### GET /health/ready

Public endpoint (no auth required). Validates database connectivity.

**Response (200 OK):**
```json
{
  "status": "ready",
  "service": "backend-api",
  "database": "connected",
  "ml_pipeline": "http://ml-pipeline.railway.internal:8001",
  "digital_twin": "http://digital-twin.railway.internal:8002"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "not_ready",
  "service": "backend-api",
  "error": "Database connection failed"
}
```

---

**Last Updated**: 2025-11-30
**API Version**: 1.0.0
