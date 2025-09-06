/**
 * Widget Build Script
 * Combines all widgets into UMD bundles for easy embedding
 */

const fs = require('fs');
const path = require('path');

// Widget files to bundle
const widgets = [
    'orchid-of-day.js',
    'weather-compare.js', 
    'map-viewer.js'
];

// UMD wrapper template
const umdWrapper = (name, code) => `
(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD
        define([], factory);
    } else if (typeof module === 'object' && module.exports) {
        // Node
        module.exports = factory();
    } else {
        // Browser globals
        root.OrchidWidgets = factory();
    }
}(typeof self !== 'undefined' ? self : this, function () {
    'use strict';
    
    ${code}
    
    return {
        OrchidOfDayWidget: typeof OrchidOfDayWidget !== 'undefined' ? OrchidOfDayWidget : null,
        WeatherCompareWidget: typeof WeatherCompareWidget !== 'undefined' ? WeatherCompareWidget : null,
        MapViewerWidget: typeof MapViewerWidget !== 'undefined' ? MapViewerWidget : null
    };
}));
`;

// Ensure output directory exists
const outputDir = path.join(__dirname, 'dist');
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

try {
    console.log('Building orchid widgets...');
    
    // Combine all widget files
    let combinedCode = '';
    
    for (const widget of widgets) {
        const widgetPath = path.join(__dirname, 'src', widget);
        if (fs.existsSync(widgetPath)) {
            const content = fs.readFileSync(widgetPath, 'utf8');
            combinedCode += content + '\n\n';
            console.log(`✓ Added ${widget}`);
        } else {
            console.warn(`⚠ Widget file not found: ${widget}`);
        }
    }
    
    // Wrap in UMD format
    const umdBundle = umdWrapper('OrchidWidgets', combinedCode);
    
    // Write UMD bundle
    const umdPath = path.join(outputDir, 'orchid-widgets.umd.js');
    fs.writeFileSync(umdPath, umdBundle);
    console.log(`✓ Created UMD bundle: ${umdPath}`);
    
    // Write minified version (simple minification)
    const minified = umdBundle
        .replace(/\s+/g, ' ')
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/\/\/.*$/gm, '');
    
    const minPath = path.join(outputDir, 'orchid-widgets.umd.min.js');
    fs.writeFileSync(minPath, minified);
    console.log(`✓ Created minified bundle: ${minPath}`);
    
    // Create widget demo HTML
    const demoHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orchid Widgets Demo</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f3f4f6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #1f2937;
            margin-bottom: 40px;
        }
        .widget-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }
        .widget-container {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .widget-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            color: #1f2937;
        }
        .code-block {
            background: #1f2937;
            color: #f9fafb;
            padding: 16px;
            border-radius: 8px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 14px;
            overflow-x: auto;
            margin-top: 16px;
        }
        .theme-toggle {
            text-align: center;
            margin-bottom: 20px;
        }
        .theme-toggle button {
            padding: 8px 16px;
            margin: 0 4px;
            border: 1px solid #d1d5db;
            background: white;
            border-radius: 6px;
            cursor: pointer;
        }
        .theme-toggle button.active {
            background: #3b82f6;
            color: white;
            border-color: #3b82f6;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌺 Orchid Continuum Widgets Demo</h1>
        
        <div class="theme-toggle">
            <button id="light-theme" class="active">Light Theme</button>
            <button id="dark-theme">Dark Theme</button>
        </div>
        
        <div class="widget-grid">
            <div class="widget-container">
                <div class="widget-title">Orchid of the Day</div>
                <orchid-of-day 
                    data-theme="light" 
                    data-size="medium"
                    api-base="https://api.orchidcontinuum.org">
                </orchid-of-day>
                <div class="code-block">
&lt;script src="orchid-widgets.umd.js"&gt;&lt;/script&gt;
&lt;orchid-of-day 
    data-theme="light" 
    data-size="medium"&gt;
&lt;/orchid-of-day&gt;
                </div>
            </div>
            
            <div class="widget-container">
                <div class="widget-title">Weather & Habitat Compare</div>
                <weather-compare 
                    data-theme="light"
                    api-base="https://api.orchidcontinuum.org">
                </weather-compare>
                <div class="code-block">
&lt;script src="orchid-widgets.umd.js"&gt;&lt;/script&gt;
&lt;weather-compare 
    data-theme="light"
    orchid-id="123"&gt;
&lt;/weather-compare&gt;
                </div>
            </div>
            
            <div class="widget-container">
                <div class="widget-title">Map Viewer</div>
                <map-viewer 
                    data-theme="light"
                    data-zoom="2"
                    api-base="https://api.orchidcontinuum.org">
                </map-viewer>
                <div class="code-block">
&lt;script src="orchid-widgets.umd.js"&gt;&lt;/script&gt;
&lt;map-viewer 
    data-theme="light"
    data-zoom="3"&gt;
&lt;/map-viewer&gt;
                </div>
            </div>
        </div>
    </div>
    
    <script src="orchid-widgets.umd.js"></script>
    <script>
        // Theme switching
        const lightBtn = document.getElementById('light-theme');
        const darkBtn = document.getElementById('dark-theme');
        const widgets = document.querySelectorAll('orchid-of-day, weather-compare, map-viewer');
        
        lightBtn.addEventListener('click', () => {
            lightBtn.classList.add('active');
            darkBtn.classList.remove('active');
            widgets.forEach(widget => widget.setAttribute('data-theme', 'light'));
            document.body.style.background = '#f3f4f6';
        });
        
        darkBtn.addEventListener('click', () => {
            darkBtn.classList.add('active');
            lightBtn.classList.remove('active');
            widgets.forEach(widget => widget.setAttribute('data-theme', 'dark'));
            document.body.style.background = '#1f2937';
        });
    </script>
</body>
</html>
    `;
    
    const demoPath = path.join(outputDir, 'demo.html');
    fs.writeFileSync(demoPath, demoHtml);
    console.log(`✓ Created demo page: ${demoPath}`);
    
    // Generate package.json for widget distribution
    const packageJson = {
        name: 'orchid-continuum-widgets',
        version: '1.0.0',
        description: 'Embeddable widgets for The Orchid Continuum platform',
        main: 'orchid-widgets.umd.js',
        files: ['dist/'],
        keywords: ['orchids', 'widgets', 'web-components', 'botany'],
        repository: {
            type: 'git',
            url: 'https://github.com/orchid-continuum/widgets'
        },
        license: 'MIT',
        author: 'The Orchid Continuum Team'
    };
    
    const packagePath = path.join(outputDir, 'package.json');
    fs.writeFileSync(packagePath, JSON.stringify(packageJson, null, 2));
    console.log(`✓ Created package.json: ${packagePath}`);
    
    console.log('\n✅ Widget build completed successfully!');
    console.log('\nFiles created:');
    console.log(`  - ${path.relative(process.cwd(), umdPath)}`);
    console.log(`  - ${path.relative(process.cwd(), minPath)}`);
    console.log(`  - ${path.relative(process.cwd(), demoPath)}`);
    console.log(`  - ${path.relative(process.cwd(), packagePath)}`);
    
} catch (error) {
    console.error('❌ Build failed:', error);
    process.exit(1);
}