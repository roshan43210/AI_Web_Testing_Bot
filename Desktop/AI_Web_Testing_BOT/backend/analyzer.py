# analyzer.py
import requests
from bs4 import BeautifulSoup

def check_links(links):
    results = []

    for link in links:
        try:
            response = requests.get(link, timeout=5, allow_redirects=True)
            status = response.status_code
            
            # Get additional details for errors
            error_detail = None
            if status >= 400:
                error_detail = get_error_detail(status, response)
                
            # Analyze content for UI anomalies
            ui_anomalies = []
            if status == 200:
                ui_anomalies = detect_ui_anomalies(response.text, link)
        except requests.exceptions.ConnectionError:
            status = 0
            error_detail = "Connection failed - The URL is unreachable or invalid"
            ui_anomalies = []
        except requests.exceptions.Timeout:
            status = 0
            error_detail = "Connection timed out - The server took too long to respond"
            ui_anomalies = []
        except requests.exceptions.TooManyRedirects:
            status = 0
            error_detail = "Too many redirects - The URL has too many redirect chains"
            ui_anomalies = []
        except requests.exceptions.InvalidURL:
            status = 0
            error_detail = "Invalid URL format"
            ui_anomalies = []
        except Exception as e:
            status = 0
            error_detail = f"Error: {str(e)}"
            ui_anomalies = []
        else:
            error_detail = get_error_detail(status, response)

        # Calculate risk score and severity
        risk_score = calculate_risk_score(status, error_detail or "", ui_anomalies)
        severity = predict_severity(status, ui_anomalies)

        results.append({
            "url": link,
            "status": status,
            "error_detail": error_detail,
            "ui_anomalies": ui_anomalies,
            "risk_score": risk_score,
            "severity": severity
        })

    return results

def get_error_detail(status, response):
    """Get detailed explanation of HTTP status"""
    if status >= 200 and status < 300:
        return "OK - Link is working correctly"
    elif status == 301:
        return f"Permanent Redirect - Moved to: {response.headers.get('Location', 'Unknown')}"
    elif status == 302:
        return f"Temporary Redirect - Moved to: {response.headers.get('Location', 'Unknown')}"
    elif status == 304:
        return "Not Modified - Content hasn't changed (cached)"
    elif status == 400:
        return "Bad Request - The server didn't understand the request"
    elif status == 401:
        return "Unauthorized - Authentication required"
    elif status == 403:
        return "Forbidden - Access denied to this resource"
    elif status == 404:
        return "Not Found - The page doesn't exist"
    elif status == 405:
        return "Method Not Allowed - Request method not supported"
    elif status == 408:
        return "Request Timeout - Server timed out waiting for request"
    elif status == 429:
        return "Too Many Requests - Rate limited by server"
    elif status == 500:
        return "Internal Server Error - Server encountered an error"
    elif status == 502:
        return "Bad Gateway - Server received invalid response from upstream"
    elif status == 503:
        return "Service Unavailable - Server is temporarily unavailable"
    elif status == 504:
        return "Gateway Timeout - Upstream server timed out"
    elif status >= 300 and status < 400:
        return f"Redirect (HTTP {status}) - Visit the redirect URL"
    else:
        return f"HTTP {status} - Server returned this status code"

def detect_ui_anomalies(html_content, url):
    """Detect UI anomalies in the page"""
    anomalies = []
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for missing alt text on images
        images = soup.find_all('img')
        missing_alt = [img.get('src', 'unknown') for img in images if not img.get('alt')]
        if missing_alt:
            anomalies.append({
                "type": "missing_alt_text",
                "count": len(missing_alt),
                "details": f"{len(missing_alt)} images without alt text"
            })
        
        # Check for empty links
        empty_links = soup.find_all('a', href='')
        if empty_links:
            anomalies.append({
                "type": "empty_links",
                "count": len(empty_links),
                "details": f"{len(empty_links)} empty link(s) found"
            })
        
        # Check for missing form labels
        inputs = soup.find_all('input')
        unlabeled = [inp.get('id', 'unknown') for inp in inputs if not inp.get('aria-label') and not inp.get('label')]
        if unlabeled:
            anomalies.append({
                "type": "unlabeled_inputs",
                "count": len(unlabeled),
                "details": f"{len(unlabeled)} input(s) without labels"
            })
        
        # Check for broken JavaScript
        if 'javascript:void(0)' in html_content or 'javascript:;' in html_content:
            anomalies.append({
                "type": "inline_js",
                "count": html_content.count('javascript:void(0)'),
                "details": "Inline JavaScript handlers detected"
            })
        
        # Check for deprecated tags
        deprecated = soup.find_all(['center', 'font', 'strike'])
        if deprecated:
            anomalies.append({
                "type": "deprecated_tags",
                "count": len(deprecated),
                "details": f"{len(deprecated)} deprecated HTML tag(s) found"
            })
    except:
        pass
    
    return anomalies

def calculate_risk_score(status, error_detail, ui_anomalies):
    """Calculate risk score (0-100) based on link status and anomalies"""
    score = 0
    
    # Status-based scoring
    if status == 0:
        score += 50  # Connection error - high risk
    elif status == 404:
        score += 40  # Not found
    elif status == 403:
        score += 35  # Forbidden
    elif status == 500:
        score += 45  # Server error
    elif status >= 500:
        score += 40
    elif status >= 400:
        score += 25
    
    # Anomaly-based scoring
    if ui_anomalies:
        score += len(ui_anomalies) * 5
    
    return min(score, 100)

def predict_severity(status, ui_anomalies):
    """Predict bug severity: Critical, High, Medium, Low"""
    if status == 0 or status >= 500:
        return "Critical"
    elif status == 404 or status == 403:
        return "High"
    elif ui_anomalies:
        return "Medium"
    else:
        return "Low"

def generate_ai_summary(results, url):
    """Generate AI-powered summary report"""
    total = len(results)
    working = sum(1 for r in results if r.get('status', 0) >= 200 and r.get('status', 0) < 400)
    broken = total - working
    
    # Count by severity
    critical = sum(1 for r in results if r.get('severity') == 'Critical')
    high = sum(1 for r in results if r.get('severity') == 'High')
    medium = sum(1 for r in results if r.get('severity') == 'Medium')
    low = sum(1 for r in results if r.get('severity') == 'Low')
    
    # Collect all anomalies
    all_anomalies = []
    for r in results:
        for a in r.get('ui_anomalies', []):
            all_anomalies.append(a['type'])
    
    # Calculate average risk score
    avg_risk = sum(r.get('risk_score', 0) for r in results) / total if total > 0 else 0
    
    # Build AI summary
    summary_parts = []
    
    # Overall assessment
    health_percent = (working / total * 100) if total > 0 else 0
    if health_percent >= 90:
        health_status = "Excellent"
    elif health_percent >= 70:
        health_status = "Good"
    elif health_percent >= 50:
        health_status = "Fair"
    else:
        health_status = "Poor"
    
    summary_parts.append(f" 📊 Overall Assessment")
    summary_parts.append(f"Given Website {url} has a {health_status} health score of {health_percent:.1f}%.")
    summary_parts.append(f"")
    
    #Issue breakdown
    if broken > 0:
        summary_parts.append(f" 🚨 Issues Found")
        if critical > 0:
            summary_parts.append(f"- {critical} Critical issues requiring immediate attention")
        if high > 0:
            summary_parts.append(f"- {high} High priority issues that should be fixed soon")
        if medium > 0:
            summary_parts.append(f"- {medium} Medium issues affecting user experience")
        if low > 0:
            summary_parts.append(f"- {low} Low minor issues")
        summary_parts.append(f"")
    
    # Risk analysis
    summary_parts.append(f"⚠️ Risk Analysis")
    summary_parts.append(f"Average Risk Score: {avg_risk:.1f}/100")
    if avg_risk >= 70:
        summary_parts.append(f"This website has high security risk. Immediate action recommended.")
    elif avg_risk >= 40:
        summary_parts.append(f"This website has moderate risk. Review the issues above.")
    else:
        summary_parts.append(f"This website has low risk. Issues are mostly cosmetic.")
    summary_parts.append(f"")
    
    # UI anomalies
    if all_anomalies:
        anomaly_counts = {}
        for a in all_anomalies:
            anomaly_counts[a] = anomaly_counts.get(a, 0) + 1
        
        summary_parts.append(f" 🎨 UI/Accessibility Issues")
        for anom, count in sorted(anomaly_counts.items(), key=lambda x: x[1], reverse=True):
            readable = anom.replace('_', ' ').title()
            summary_parts.append(f"- {count}x {readable}")
        summary_parts.append(f"")
    
    # Recommendations
    summary_parts.append(f"💡 Recommendations")
    if critical > 0:
        summary_parts.append(f"1. Fix {critical} critical issue(s) immediately")
    if high > 0:
        summary_parts.append(f"2. Address {high} high-priority issue(s)")
    if all_anomalies:
        summary_parts.append(f"3. Improve accessibility by adding alt text and labels")
    if broken > 0:
        summary_parts.append(f"4. Review and fix {broken} broken link(s)")
    summary_parts.append(f"")
    
    summary_parts.append(f"---")
    summary_parts.append(f"*Generated by AI Web Testing Bot*")
    
    return "\n".join(summary_parts)
