# Generic JSON API Sensor for Home Assistant

A custom Home Assistant integration that fetches JSON data from any API endpoint and exposes it as a sensor with configurable attributes.

## Features

- 🌐 Fetch JSON data from any REST API endpoint
- 🔐 Support for authentication (Bearer tokens, custom headers)
- 🎨 Transform JSON data with Jinja2 templates
- ⚙️ Configurable scan intervals
- 📊 Automatic handling of arrays and objects
- 🔄 Works with any JSON API (Readeck, custom APIs, etc.)

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/json_api_sensor` folder to your Home Assistant's `custom_components` directory
2. If the `custom_components` directory doesn't exist, create it in your Home Assistant configuration directory
3. Restart Home Assistant

Your directory structure should look like this:
```
config/
└── custom_components/
    └── json_api_sensor/
        ├── __init__.py
        ├── manifest.json
        └── sensor.py
```

## Configuration

Add the sensor to your `configuration.yaml` file:

### Basic Configuration

```yaml
sensor:
  - platform: json_api_sensor
    name: "My API Sensor"
    url: "https://api.example.com/data"
    scan_interval: 300  # seconds (5 minutes)
```

### With Authorization

```yaml
sensor:
  - platform: json_api_sensor
    name: "My API Sensor"
    url: "https://api.example.com/data"
    authorization: "Bearer YOUR_TOKEN_HERE"
    scan_interval: 300
```

### With Custom Headers

```yaml
sensor:
  - platform: json_api_sensor
    name: "My API Sensor"
    url: "https://api.example.com/data"
    headers:
      Authorization: "Bearer YOUR_TOKEN_HERE"
      Content-Type: "application/json"
      X-Custom-Header: "value"
    scan_interval: 300
```

### With Attributes Template

Transform the JSON response to extract only what you need:

```yaml
sensor:
  - platform: json_api_sensor
    name: "Readeck Bookmarks"
    url: "https://your-readeck-instance.com/api/bookmarks"
    authorization: "Bearer YOUR_TOKEN"
    scan_interval: 300
    attributes_template: >
      {% set ns = namespace(items=[]) %}
      {% for item in value_json %}
        {% set ns.items = ns.items + [{'url': item.url, 'title': item.title}] %}
      {% endfor %}
      {{ {'bookmarks': ns.items} | tojson }}
```

## Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `platform` | Yes | - | Must be `json_api_sensor` |
| `name` | No | `JSON API Sensor` | Friendly name for the sensor |
| `url` | Yes | - | The API endpoint URL |
| `authorization` | No | - | Authorization header value (e.g., `Bearer token123`) |
| `headers` | No | `{}` | Dictionary of custom headers |
| `scan_interval` | No | `300` | Update interval in seconds |
| `attributes_template` | No | - | Jinja2 template to transform the JSON response |

## Usage Examples


### Example 1: Readeck Bookmarks

Fetch bookmarks from Readeck and display only URL and title:

```yaml
sensor:
  - platform: json_api_sensor
    name: "Readeck Bookmarks"
    url: "https://bookmarks.example.com/api/bookmarks"
    authorization: "Bearer YOUR_READECK_TOKEN"
    scan_interval: 300
    attributes_template: >
      {% set ns = namespace(items=[]) %}
      {% for item in value_json %}
        {% set ns.items = ns.items + [{'url': item.url, 'title': item.title}] %}
      {% endfor %}
      {{ {'bookmarks': ns.items} | tojson }}
```

Access in templates:
```yaml
{% set bookmarks = state_attr('sensor.readeck_bookmarks', 'bookmarks') %}
{% for item in bookmarks[:5] %}
  [{{ item.title }}]({{ item.url }})
{% endfor %}
```

### Example 2: Weather API

```yaml
sensor:
  - platform: json_api_sensor
    name: "Weather Data"
    url: "https://api.weather.com/current"
    headers:
      API-Key: "YOUR_API_KEY"
    scan_interval: 600
```

### Example 3: Custom IoT Device

```yaml
sensor:
  - platform: json_api_sensor
    name: "Device Status"
    url: "http://192.168.1.100/api/status"
    scan_interval: 30
    attributes_template: >
      {{ {'temperature': value_json.temp, 'humidity': value_json.hum, 'online': value_json.status == 'ok'} | tojson }}
```

## Attributes Template Guide

The `attributes_template` option accepts Jinja2 templates with access to the `value_json` variable containing the API response.

### Template must return valid JSON

Your template should output a valid JSON string using the `tojson` filter:

```yaml
attributes_template: >
  {{ {'key': 'value'} | tojson }}
```

### Filtering Array Data

Extract specific fields from an array:

```yaml
attributes_template: >
  {% set ns = namespace(items=[]) %}
  {% for item in value_json %}
    {% set ns.items = ns.items + [{'id': item.id, 'name': item.name}] %}
  {% endfor %}
  {{ {'items': ns.items} | tojson }}
```

### Transforming Object Data

Restructure nested data:

```yaml
attributes_template: >
  {{ {
    'summary': value_json.data.summary,
    'count': value_json.data.items | length,
    'first_item': value_json.data.items[0].name
  } | tojson }}
```

## Default Behavior (Without Template)

When no `attributes_template` is provided:

- **Array response**: State = array length, attributes stored under `items` key
- **Object response**: State = `OK` (or `count`/`total` if present), all keys stored as attributes
- **Other types**: State = string representation, stored under `raw` key

## Secrets

Secrets can be used for your links and authorisation codes


Sensor
``` yaml
sensor:
  - platform: json_api_sensor
    name: "Readeck Bookmarks"
    url: !secret readeck_url
    authorization: !secret readeck_token
    scan_interval: 300
```
Secrets.yaml
``` yaml
readeck_url: "https://bookmarks.example.com/api/bookmarks"
readeck_token: "Bearer YOUR_TOKEN_HERE"
```

## Troubleshooting

### Sensor shows as unavailable

- Check Home Assistant logs: `Settings` → `System` → `Logs`
- Verify the API URL is accessible
- Check authentication credentials
- Ensure the API returns valid JSON

### Template errors

- Verify your template outputs valid JSON
- Test templates in Home Assistant Developer Tools → Template
- Check logs for specific error messages
- Use `{{ value_json | tojson }}` to see raw API response

### Rate limiting

- Increase `scan_interval` to reduce API calls
- Check if your API has rate limits
- Monitor Home Assistant logs for HTTP errors

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## License

This project is licensed under the MIT License.

## Credits

Created for Home Assistant users who need a simple way to integrate any JSON API into their smart home.
