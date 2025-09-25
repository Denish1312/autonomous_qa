"""
HTML and Markdown templates for test reports.
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report.title }}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {
            --primary-color: #2563eb;
            --success-color: #22c55e;
            --error-color: #ef4444;
            --warning-color: #f59e0b;
            --info-color: #3b82f6;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #1f2937;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .summary-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
        }
        
        .status-passed { background: var(--success-color); color: white; }
        .status-failed { background: var(--error-color); color: white; }
        .status-skipped { background: var(--warning-color); color: white; }
        .status-error { background: var(--error-color); color: white; }
        .status-healed { background: var(--info-color); color: white; }
        
        .test-suite {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .test-case {
            border-left: 4px solid #e5e7eb;
            padding: 10px 20px;
            margin: 10px 0;
        }
        
        .test-case.passed { border-color: var(--success-color); }
        .test-case.failed { border-color: var(--error-color); }
        .test-case.skipped { border-color: var(--warning-color); }
        .test-case.error { border-color: var(--error-color); }
        .test-case.healed { border-color: var(--info-color); }
        
        .test-step {
            margin: 10px 0;
            padding: 10px;
            background: #f9fafb;
            border-radius: 4px;
        }
        
        .artifact-link {
            display: inline-block;
            padding: 4px 8px;
            background: #e5e7eb;
            border-radius: 4px;
            text-decoration: none;
            color: #374151;
            margin: 4px;
        }
        
        .trend-chart {
            margin: 40px 0;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report.title }}</h1>
            <p>{{ report.description }}</p>
            <p>Generated: {{ report.generated_at }}</p>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <p class="large-number">{{ report.summary.total_tests }}</p>
            </div>
            <div class="summary-card">
                <h3>Pass Rate</h3>
                <p class="large-number">{{ report.summary.pass_rate }}%</p>
            </div>
            <div class="summary-card">
                <h3>Healing Rate</h3>
                <p class="large-number">{{ report.summary.healing_rate }}%</p>
            </div>
            <div class="summary-card">
                <h3>Duration</h3>
                <p class="large-number">{{ report.summary.total_duration }}</p>
            </div>
        </div>
        
        <div id="trendChart" class="trend-chart">
            <!-- Plotly chart will be rendered here -->
        </div>
        
        {% for suite in report.test_suites %}
        <div class="test-suite">
            <h2>{{ suite.name }}</h2>
            <p>{{ suite.description }}</p>
            
            {% for test in suite.test_cases %}
            <div class="test-case {{ test.status }}">
                <h3>
                    {{ test.title }}
                    <span class="status-badge status-{{ test.status }}">{{ test.status }}</span>
                </h3>
                
                {% if test.error_message %}
                <div class="error-message">{{ test.error_message }}</div>
                {% endif %}
                
                {% for step in test.steps %}
                <div class="test-step">
                    <p>{{ step.description }}</p>
                    {% if step.error_message %}
                    <div class="error-message">{{ step.error_message }}</div>
                    {% endif %}
                    
                    {% for artifact in step.artifacts %}
                    <a href="{{ artifact.path }}" class="artifact-link" target="_blank">
                        {{ artifact.type }}: {{ artifact.description }}
                    </a>
                    {% endfor %}
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>
    
    <script>
        // Render trend chart using Plotly
        const trends = {{ report.trends | tojson }};
        const dates = trends.map(t => t.date);
        const passRates = trends.map(t => (t.passed_tests / t.total_tests) * 100);
        const healingRates = trends.map(t => t.healing_success_rate);
        
        const trace1 = {
            x: dates,
            y: passRates,
            name: 'Pass Rate',
            type: 'scatter'
        };
        
        const trace2 = {
            x: dates,
            y: healingRates,
            name: 'Healing Rate',
            type: 'scatter'
        };
        
        const layout = {
            title: 'Test Execution Trends',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Rate (%)' }
        };
        
        Plotly.newPlot('trendChart', [trace1, trace2], layout);
    </script>
</body>
</html>
"""

MARKDOWN_TEMPLATE = """
# {{ report.title }}

{{ report.description }}

Generated: {{ report.generated_at }}

## Summary

- Total Tests: {{ report.summary.total_tests }}
- Pass Rate: {{ report.summary.pass_rate }}%
- Healing Rate: {{ report.summary.healing_rate }}%
- Total Duration: {{ report.summary.total_duration }}

## Test Suites

{% for suite in report.test_suites %}
### {{ suite.name }}

{{ suite.description }}

{% for test in suite.test_cases %}
#### {{ test.title }} ({{ test.status }})

{% if test.error_message %}
Error: {{ test.error_message }}
{% endif %}

Steps:
{% for step in test.steps %}
- {{ step.description }}
  {% if step.error_message %}
  Error: {{ step.error_message }}
  {% endif %}
  {% if step.artifacts %}
  Artifacts:
  {% for artifact in step.artifacts %}
  - [{{ artifact.type }}: {{ artifact.description }}]({{ artifact.path }})
  {% endfor %}
  {% endif %}
{% endfor %}

{% endfor %}
{% endfor %}

## Environment

{% for key, value in report.environment.items() %}
- {{ key }}: {{ value }}
{% endfor %}

## Metadata

{% for key, value in report.metadata.items() %}
- {{ key }}: {{ value }}
{% endfor %}
"""
