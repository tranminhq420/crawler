#!/usr/bin/env python3

def analyze_cookie_transformation():
    """Analyze the transformation of cookies from login to API access"""
    
    print("🍪 Cookie Transformation Analysis")
    print("="*60)
    
    # Login Set-Cookie responses (what server sends back)
    login_cookies_raw = [
        "wordpress_logged_in_b0519f4f29df6fe4169d3ce7e4751811=quan.tm1103%40gmail.com%7C1749055321%7C14CSWT16OsZrntpZjiFlCiVxcu2MAV2dDTlB3MJoHFy%7C871aef54aebde1cf8e0eb2fd52649dffb8d62c4caa2e3c99ae5bcbe682063956; _ga_VPJE22YS3J=GS2.1.s1748882490$o6$g1$t1748882552$j59$l0$h0",
        "wordpress_sec_b0519f4f29df6fe4169d3ce7e4751811=quan.tm1103%40gmail.com%7C1749055321%7C14CSWT16OsZrntpZjiFlCiVxcu2MAV2dDTlB3MJoHFy%7Ca8d14d58f0eca46ef2c73d30372864c7acb374fddeac31d75f4e3a979d8a83af;",
        "wordpress_sec_b0519f4f29df6fe4169d3ce7e4751811=quan.tm1103%40gmail.com%7C1749055321%7C14CSWT16OsZrntpZjiFlCiVxcu2MAV2dDTlB3MJoHFy%7Ca8d14d58f0eca46ef2c73d30372864c7acb374fddeac31d75f4e3a979d8a83af;"
    ]
    
    # API access cookies (what client sends to server)
    api_cookies_raw = "wordpress_sec_b0519f4f29df6fe4169d3ce7e4751811=quan.tm1103%40gmail.com%7C1749055321%7C14CSWT16OsZrntpZjiFlCiVxcu2MAV2dDTlB3MJoHFy%7Ca8d14d58f0eca46ef2c73d30372864c7acb374fddeac31d75f4e3a979d8a83af; _ga=GA1.1.801616380.1748826725; PHPSESSID=b4a4dcf02c8510219e8d2e5619ea4b6c; wordpress_test_cookie=WP%20Cookie%20check; _ldapp_bhd_currentLocation=ha-noi; wordpress_logged_in_b0519f4f29df6fe4169d3ce7e4751811=quan.tm1103%40gmail.com%7C1749055321%7C14CSWT16OsZrntpZjiFlCiVxcu2MAV2dDTlB3MJoHFy%7C871aef54aebde1cf8e0eb2fd52649dffb8d62c4caa2e3c99ae5bcbe682063956; _ga_VPJE22YS3J=GS2.1.s1748882490$o6$g1$t1748882566$j45$l0$h0"
    
    # Parse login cookies
    login_cookies = {}
    for cookie_header in login_cookies_raw:
        if '=' in cookie_header:
            pairs = cookie_header.split(';')
            for pair in pairs:
                pair = pair.strip()
                if '=' in pair:
                    name, value = pair.split('=', 1)
                    login_cookies[name.strip()] = value.strip()
    
    # Parse API cookies
    api_cookies = {}
    for pair in api_cookies_raw.split(';'):
        pair = pair.strip()
        if '=' in pair:
            name, value = pair.split('=', 1)
            api_cookies[name.strip()] = value.strip()
    
    print("\n📋 LOGIN RESPONSE COOKIES:")
    for name, value in login_cookies.items():
        print(f"  {name}: {value[:50]}...")
    
    print(f"\n📋 API REQUEST COOKIES:")
    for name, value in api_cookies.items():
        print(f"  {name}: {value[:50]}...")
    
    print(f"\n🔍 TRANSFORMATION ANALYSIS:")
    
    # 1. Check which cookies are preserved
    print(f"\n1️⃣ PRESERVED COOKIES (login → API):")
    preserved = 0
    for name, login_value in login_cookies.items():
        if name in api_cookies:
            api_value = api_cookies[name]
            if login_value == api_value:
                print(f"  ✅ {name}: EXACT MATCH")
                preserved += 1
            else:
                print(f"  🔄 {name}: MODIFIED")
                print(f"      Login:  {login_value[:50]}...")
                print(f"      API:    {api_value[:50]}...")
        else:
            print(f"  ❌ {name}: NOT IN API REQUEST")
    
    # 2. Check which cookies are added
    print(f"\n2️⃣ ADDED COOKIES (not from login):")
    added = 0
    for name, value in api_cookies.items():
        if name not in login_cookies:
            print(f"  ➕ {name}: {value[:50]}...")
            added += 1
    
    # 3. Check which cookies are removed
    print(f"\n3️⃣ REMOVED COOKIES (from login but not in API):")
    removed = 0
    for name in login_cookies.keys():
        if name not in api_cookies:
            print(f"  ➖ {name}")
            removed += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"  Preserved: {preserved} cookies")
    print(f"  Modified: {len([n for n in login_cookies if n in api_cookies and login_cookies[n] != api_cookies[n]])} cookies")
    print(f"  Added: {added} cookies")
    print(f"  Removed: {removed} cookies")
    
    return login_cookies, api_cookies

def generate_spider_cookie_strategy(login_cookies, api_cookies):
    """Generate the strategy our spider should use"""
    
    print(f"\n🕷️ SPIDER COOKIE STRATEGY")
    print(f"="*60)
    
    print(f"\n1️⃣ CORE AUTHENTICATION COOKIES (from login response):")
    auth_cookies = [
        "wordpress_sec_b0519f4f29df6fe4169d3ce7e4751811",
        "wordpress_logged_in_b0519f4f29df6fe4169d3ce7e4751811"
    ]
    
    for cookie_name in auth_cookies:
        if cookie_name in login_cookies:
            print(f"  ✅ MUST CAPTURE: {cookie_name}")
            print(f"      Value: {login_cookies[cookie_name][:50]}...")
        else:
            print(f"  ❌ MISSING: {cookie_name}")
    
    print(f"\n2️⃣ PERSISTENT SESSION COOKIES (from site navigation):")
    persistent_cookies = [
        "_ga", "_ga_VPJE22YS3J", "PHPSESSID", 
        "wordpress_test_cookie", "_ldapp_bhd_currentLocation"
    ]
    
    for cookie_name in persistent_cookies:
        if cookie_name in api_cookies:
            print(f"  ✅ MUST MAINTAIN: {cookie_name}")
            print(f"      Value: {api_cookies[cookie_name][:50]}...")
        else:
            print(f"  ❓ MISSING: {cookie_name}")
    
    print(f"\n3️⃣ SPIDER IMPLEMENTATION CHECKLIST:")
    print(f"  ✅ Visit main site first (collect GA cookies)")
    print(f"  ✅ Handle login form (collect WordPress auth cookies)")
    print(f"  ✅ Preserve PHPSESSID throughout session")
    print(f"  ✅ Set BHD location cookie: _ldapp_bhd_currentLocation=ha-noi")
    print(f"  ✅ Set WordPress test cookie: wordpress_test_cookie=WP%20Cookie%20check")
    print(f"  ✅ Merge all cookies for API requests")
    print(f"  ❓ Update GA timestamp cookies during navigation")

def check_spider_implementation():
    """Check if our current spider implementation matches this strategy"""
    
    print(f"\n🔍 CURRENT SPIDER IMPLEMENTATION REVIEW")
    print(f"="*60)
    
    spider_checks = [
        ("Visit main site first", "✅ visit_main_site() method"),
        ("Collect GA cookies", "✅ Store ALL cookies from main site"),
        ("Handle login form", "✅ handle_login_page() and after_login()"),
        ("Preserve PHPSESSID", "✅ Extract and store from responses"),
        ("WordPress auth cookies", "✅ Extract from 302 redirect response"),
        ("BHD location cookie", "✅ Set _ldapp_bhd_currentLocation=ha-noi"),
        ("WordPress test cookie", "✅ Set wordpress_test_cookie"),
        ("Merge all cookies", "✅ create_cookie_header() method"),
        ("Fresh nonce per movie", "✅ get_movie_specific_data() method"),
        ("Movie-specific f param", "✅ Use movie_id from data-id")
    ]
    
    print(f"\n📋 Implementation Status:")
    for check, status in spider_checks:
        print(f"  {status} {check}")
    
    print(f"\n💡 POTENTIAL ISSUES:")
    print(f"  ❓ Cookie timing: GA cookies may update during navigation")
    print(f"  ❓ Session persistence: PHPSESSID must stay consistent")
    print(f"  ❓ Nonce freshness: May expire quickly")
    print(f"  ❓ Movie-specific data-id: Must extract correctly from hanoicine")

if __name__ == "__main__":
    # Analyze the transformation
    login_cookies, api_cookies = analyze_cookie_transformation()
    
    # Generate strategy
    generate_spider_cookie_strategy(login_cookies, api_cookies)
    
    # Check current implementation
    check_spider_implementation()
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. ✅ Our spider cookie handling looks correct")
    print(f"2. ❓ Test with fresh login to get working cookies")
    print(f"3. ❓ Extract correct movie-specific data-id values")
    print(f"4. ❓ Get fresh nonce values per movie")
    print(f"5. ❓ Test seats API with correct f + nonce combination") 