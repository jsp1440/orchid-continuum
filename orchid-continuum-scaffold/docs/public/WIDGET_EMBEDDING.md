# Orchid Continuum Widget Embedding Guide

This guide shows how to embed Orchid Continuum widgets into your website or application.

## Quick Start

### 1. Include the Widget Bundle

Add the UMD bundle to your HTML page:

```html
<script src="https://cdn.orchidcontinuum.org/orchid-widgets.umd.js"></script>
```

### 2. Add Widget Elements

Use the custom elements in your HTML:

```html
<!-- Orchid of the Day -->
<orchid-of-day data-theme="light" data-size="medium"></orchid-of-day>

<!-- Weather & Habitat Compare -->
<weather-compare data-theme="light" orchid-id="123"></weather-compare>

<!-- Map Viewer -->
<map-viewer data-theme="light" data-zoom="3"></map-viewer>
```

## Widget Reference

### Orchid of the Day

Displays a featured orchid with image and description.

**Attributes:**
- `data-theme`: "light" or "dark" (default: "light")
- `data-size`: "small", "medium", or "large" (default: "medium")
- `api-base`: API endpoint URL (optional)

**Example:**
```html
<orchid-of-day 
    data-theme="dark" 
    data-size="large"
    api-base="https://api.orchidcontinuum.org">
</orchid-of-day>
```

### Weather & Habitat Compare

Compare local weather conditions with orchid's native habitat.

**Attributes:**
- `data-theme`: "light" or "dark" (default: "light")
- `orchid-id`: Specific orchid ID for comparison (optional)
- `api-base`: API endpoint URL (optional)

**Example:**
```html
<weather-compare 
    data-theme="light"
    orchid-id="phalaenopsis-123">
</weather-compare>
```

### Map Viewer

Interactive map showing orchid locations with filtering.

**Attributes:**
- `data-theme`: "light" or "dark" (default: "light")
- `data-zoom`: Initial zoom level 1-18 (default: 2)
- `api-base`: API endpoint URL (optional)

**Example:**
```html
<map-viewer 
    data-theme="dark"
    data-zoom="5">
</map-viewer>
```

## Styling and Theming

### Theme Switching

Widgets automatically adapt to light and dark themes:

```javascript
// Switch all widgets to dark theme
document.querySelectorAll('orchid-of-day, weather-compare, map-viewer')
    .forEach(widget => widget.setAttribute('data-theme', 'dark'));
```

### Custom CSS

Widgets use Shadow DOM and don't leak styles, but you can customize the container:

```css
orchid-of-day {
    max-width: 400px;
    margin: 20px auto;
    display: block;
}

weather-compare {
    border-radius: 12px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
```

## Responsive Design

All widgets are mobile-responsive and adapt to their container width:

```css
.widget-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 20px;
    padding: 20px;
}
```

## Integration Examples

### WordPress

Add to your theme's `functions.php`:

```php
function enqueue_orchid_widgets() {
    wp_enqueue_script(
        'orchid-widgets',
        'https://cdn.orchidcontinuum.org/orchid-widgets.umd.js',
        array(),
        '1.0.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'enqueue_orchid_widgets');
```

Then use in posts or pages:
```html
[orchid_of_day theme="light" size="medium"]
```

### React

```jsx
import { useEffect } from 'react';

function OrchidWidget({ theme = 'light', size = 'medium' }) {
    useEffect(() => {
        // Ensure widget script is loaded
        if (!window.OrchidWidgets) {
            const script = document.createElement('script');
            script.src = 'https://cdn.orchidcontinuum.org/orchid-widgets.umd.js';
            document.head.appendChild(script);
        }
    }, []);

    return (
        <orchid-of-day 
            data-theme={theme} 
            data-size={size}>
        </orchid-of-day>
    );
}
```

### Vue.js

```vue
<template>
    <orchid-of-day 
        :data-theme="theme" 
        :data-size="size">
    </orchid-of-day>
</template>

<script>
export default {
    props: {
        theme: { type: String, default: 'light' },
        size: { type: String, default: 'medium' }
    },
    mounted() {
        if (!window.OrchidWidgets) {
            const script = document.createElement('script');
            script.src = 'https://cdn.orchidcontinuum.org/orchid-widgets.umd.js';
            document.head.appendChild(script);
        }
    }
}
</script>
```

## API Configuration

### Custom API Endpoint

If you're running your own instance:

```html
<orchid-of-day api-base="https://your-api.example.com"></orchid-of-day>
```

### Authentication

For protected content, the widgets respect CORS and authentication headers:

```javascript
// Set global API configuration
window.OrchidWidgetConfig = {
    apiBase: 'https://api.orchidcontinuum.org',
    authToken: 'your-auth-token'
};
```

## Performance

### Lazy Loading

Load widgets only when needed:

```javascript
// Intersection Observer for lazy loading
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const widget = entry.target;
            widget.setAttribute('data-load', 'true');
            observer.unobserve(widget);
        }
    });
});

document.querySelectorAll('orchid-of-day').forEach(widget => {
    observer.observe(widget);
});
```

### Caching

Widgets automatically cache API responses for 5 minutes to reduce server load.

## Troubleshooting

### Widget Not Loading

1. Check browser console for errors
2. Verify script URL is accessible
3. Ensure CORS is properly configured

### API Errors

```javascript
// Listen for widget errors
document.addEventListener('orchid-widget-error', (event) => {
    console.error('Widget error:', event.detail);
});
```

### Network Issues

Widgets include offline fallbacks and retry mechanisms for network failures.

## Support

For integration support or custom widget development:
- Documentation: https://docs.orchidcontinuum.org
- Issues: https://github.com/orchid-continuum/widgets/issues
- Email: widgets@orchidcontinuum.org