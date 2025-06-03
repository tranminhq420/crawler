import requests
import re

def show_request_cookies():
    print("=== Showing Cookies in check_user_logged_in Request ===")
    
    session = requests.Session()
    
    # Step 1: Get login page and login
    print("\n1. Getting login page and logging in...")
    login_page = session.get("https://www.bhdstar.vn/tai-khoan/?login")
    nonce_match = re.search(r'name="woocommerce-login-nonce" value="([^"]+)"', login_page.text)
    nonce = nonce_match.group(1) if nonce_match else "unknown"
    
    login_payload = {
        "username": "quan.tm1103@gmail.com",
        "password": "123quan123",
        "woocommerce-login-nonce": nonce,
        "_wp_http_referer": "/",
        "login": "Đăng nhập"
    }
    
    login_headers = {
        "host": "www.bhdstar.vn",
        "connection": "keep-alive",
        "cache-control": "max-age=0",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "origin": "https://www.bhdstar.vn",
        "content-type": "application/x-www-form-urlencoded",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "referer": "https://www.bhdstar.vn/tai-khoan/?login",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9"
    }
    
    login_response = session.post(
        "https://www.bhdstar.vn/tai-khoan/?login",
        data=login_payload,
        headers=login_headers,
        allow_redirects=True
    )
    
    print(f"Login status: {login_response.status_code}")
    
    # Step 2: Show all cookies after login
    print("\n2. All cookies after login:")
    all_cookies = {}
    for cookie in session.cookies:
        all_cookies[cookie.name] = cookie.value
        print(f"  {cookie.name} = {cookie.value}")
    
    # Step 3: Create the check_user_logged_in request and intercept it
    print("\n3. Making check_user_logged_in request...")
    
    check_params = {
        "action": "ldapp_order_check_user_logged_in",
        "cinemaID": "0000000010",
        "sessionID": "107175"
    }
    
    check_headers = {
        "host": "www.bhdstar.vn",
        "connection": "keep-alive",
        "sec-ch-ua-platform": '"Windows"',
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://www.bhdstar.vn/dat-ve/?f=my-love-will-make-you-disappear",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9"
    }
    
    # Create the request manually to see what cookies would be sent
    prepared_request = session.prepare_request(
        requests.Request(
            method='GET',
            url="https://www.bhdstar.vn/wp-admin/admin-ajax.php",
            params=check_params,
            headers=check_headers
        )
    )
    
    print("\n4. Cookies that will be sent in the request:")
    print(f"Cookie header: {prepared_request.headers.get('Cookie', 'No Cookie header')}")
    
    # Parse the cookie header to show individual cookies
    cookie_header = prepared_request.headers.get('Cookie', '')
    if cookie_header:
        print("\n5. Individual cookies in the request:")
        cookies_in_request = {}
        cookie_pairs = cookie_header.split('; ')
        for cookie_pair in cookie_pairs:
            if '=' in cookie_pair:
                name, value = cookie_pair.split('=', 1)
                cookies_in_request[name] = value
                print(f"  {name} = {value}")
        
        print(f"\n6. Total cookies in request: {len(cookies_in_request)}")
        
        # Check specifically for the cookies we care about
        print("\n7. Key cookies check:")
        if 'PHPSESSID' in cookies_in_request:
            print(f"  ✅ PHPSESSID: {cookies_in_request['PHPSESSID']}")
        else:
            print("  ❌ PHPSESSID: Not found!")
            
        wordpress_logged_in_key = 'wordpress_logged_in_b0519f4f29df6fe4169d3ce7e4751811'
        if wordpress_logged_in_key in cookies_in_request:
            print(f"  ✅ WordPress logged_in: {cookies_in_request[wordpress_logged_in_key][:50]}...")
        else:
            print("  ❌ WordPress logged_in: Not found!")
            
        wordpress_sec_key = 'wordpress_sec_b0519f4f29df6fe4169d3ce7e4751811'
        if wordpress_sec_key in cookies_in_request:
            print(f"  ✅ WordPress sec: {cookies_in_request[wordpress_sec_key][:50]}...")
        else:
            print("  ❌ WordPress sec: Not found!")
    
    # Step 4: Actually send the request and show response
    print("\n8. Sending request and showing response:")
    check_response = session.get(
        "https://www.bhdstar.vn/wp-admin/admin-ajax.php",
        params=check_params,
        headers=check_headers
    )
    
    print(f"Response status: {check_response.status_code}")
    print(f"Response: {check_response.text}")
    
    # Step 5: Compare with the user's working cookie string
    print("\n9. Comparison with user's working cookie string:")
    user_working_cookies = {
        'wordpress_sec_b0519f4f29df6fe4169d3ce7e4751811': 'quan.tm1103%40gmail.com%7C1749010215%7ClCDu0GK2hz2NHOg9A1tStVUubzvNUrEzWl1TY1q3aCS%7Cb81356590f1ff34cfcf3db0f2574e07fe57b4531c31ce4992282c3ea8116a558',
        'PHPSESSID': 'b4a4dcf02c8510219e8d2e5619ea4b6c',
        'wordpress_logged_in_b0519f4f29df6fe4169d3ce7e4751811': 'quan.tm1103%40gmail.com%7C1749010215%7ClCDu0GK2hz2NHOg9A1tStVUubzvNUrEzWl1TY1q3aCS%7C559d032e564ba8e0cdb80480ea74bda03b25b4d1361869b64ed8736e80233ed5'
    }
    
    print("User's working cookies:")
    for name, value in user_working_cookies.items():
        print(f"  {name} = {value}")
        
    print("\nOur current cookies:")
    for name in user_working_cookies.keys():
        if name in cookies_in_request:
            our_value = cookies_in_request[name]
            user_value = user_working_cookies[name]
            if our_value == user_value:
                print(f"  ✅ {name} = MATCHES")
            else:
                print(f"  ❌ {name} = DIFFERENT")
                print(f"      Our value: {our_value[:50]}...")
                print(f"      User's value: {user_value[:50]}...")
        else:
            print(f"  ❌ {name} = MISSING")

if __name__ == "__main__":
    show_request_cookies() 