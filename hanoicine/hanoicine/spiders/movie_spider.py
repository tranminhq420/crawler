# Visit https://www.lddgo.net/en/string/pyc-compile-decompile for more information
# Version : Python 3.8

from urllib.parse import urlencode
import scrapy
import json
from hanoicine.items import TheaterItem, SessionItem, SeatDataItem
import re
from pathlib import Path
from datetime import datetime, timedelta

class BhdSpider(scrapy.Spider):
    name = 'bhd'
    allowed_domains = ['bhdstar.vn']
    handle_httpstatus_list = [302]
    
    def __init__(self, *args, **kwargs):
        super(BhdSpider, self).__init__(*args, **kwargs)
        self.login_cookies = {}
        self.user_session_id = None
        self.movie_data = []
        self.processed_sessions = set()  # Track processed sessions to avoid duplicates

    def start_requests(self):
        """Initialize spider with URLs from hanoicine spider"""
        urls_setting = self.settings.get('URLS', [])
        
        if isinstance(urls_setting, str):
            try:
                # Try parsing as JSON
                self.movie_data = json.loads(urls_setting.replace("'", '"'))
                self.logger.info(f'Parsed URLs from JSON string: {self.movie_data}')
            except (json.JSONDecodeError, ValueError):
                try:
                    # Try parsing as Python literal
                    import ast
                    self.movie_data = ast.literal_eval(urls_setting)
                    self.logger.info(f'Parsed URLs from Python literal: {self.movie_data}')
                except (ValueError, SyntaxError):
                    # Single URL fallback
                    self.movie_data = [{
                        'movie_url': urls_setting,
                        'movie_id': None,
                        'title': 'Unknown'
                    }]
                    self.logger.info(f'Using single URL: {self.movie_data}')
        else:
            self.movie_data = urls_setting

        # Convert old URL format to new format if needed
        if self.movie_data and isinstance(self.movie_data[0], str):
            self.logger.info('Converting old URL format to new format')
            self.movie_data = [{
                'movie_url': url,
                'movie_id': None,
                'title': 'Unknown'
            } for url in self.movie_data]

        self.logger.info(f'Received {len(self.movie_data)} movies to process')
        for i, movie in enumerate(self.movie_data):
            self.logger.info(f'Movie {i + 1}: {movie.get("title", "Unknown")} - URL: {movie.get("movie_url")} - ID: {movie.get("movie_id")}')

        if not self.movie_data:
            self.logger.warning('No movie data received from hanoicine spider')
            return

        self.logger.info('🚀 Starting fresh login process')
        main_url = 'https://www.bhdstar.vn/'
        yield scrapy.Request(
            url=main_url,
            callback=self.visit_main_site,
            meta={'cookiejar': 1, 'dont_cache': True},
            dont_filter=True
        )

    def visit_main_site(self, response):
        """Visit main site first to establish session and get PHPSESSID + other essential cookies"""
        self.logger.info('🌐 Visiting main site to establish PHP session and collect ALL cookies')
        self.logger.info(f'Main site response status: {response.status}')
        
        # Process Set-Cookie headers
        set_cookie_headers = response.headers.getlist('Set-Cookie')
        self.logger.info(f'Found {len(set_cookie_headers)} Set-Cookie headers on main site')
        
        for i, header in enumerate(set_cookie_headers):
            cookie_str = header.decode('utf-8')
            self.logger.info(f'Main site Set-Cookie #{i + 1}: {cookie_str[:100]}...')
            
            if '=' in cookie_str:
                cookie_parts = cookie_str.split(';')
                name_value_part = cookie_parts[0].strip()
                if '=' in name_value_part:
                    name, value = name_value_part.split('=', 1)
                    name = name.strip()
                    value = value.strip()
                    self.login_cookies[name] = value
                    self.logger.info(f'✅ Stored cookie: {name} = {value[:30]}...')
                    
                    if name == 'PHPSESSID':
                        self.user_session_id = value
                        self.logger.info(f'🎯 PHPSESSID established: {self.user_session_id}')

        # Process scrapy cookie jar
        if hasattr(response, 'cookies'):
            self.logger.info(f'Scrapy cookie jar has {len(response.cookies)} cookies')
            for cookie in response.cookies:
                self.logger.info(f'Scrapy jar cookie: {cookie.name} = {cookie.value[:30]}...')
                self.login_cookies[cookie.name] = cookie.value
                if cookie.name == 'PHPSESSID':
                    self.user_session_id = cookie.value
                    self.logger.info(f'🎯 PHPSESSID from jar: {self.user_session_id}')

        # Add critical BHD location cookie if not present
        if '_ldapp_bhd_currentLocation' not in self.login_cookies:
            self.login_cookies['_ldapp_bhd_currentLocation'] = 'ha-noi'
            self.logger.info('🏢 Added critical BHD location cookie: ha-noi')

        # Add WordPress test cookie if not present
        if 'wordpress_test_cookie' not in self.login_cookies:
            self.login_cookies['wordpress_test_cookie'] = 'WP%20Cookie%20check'
            self.logger.info('🍪 Added WordPress test cookie')

        self.logger.info(f'Session establishment complete. Total cookies: {len(self.login_cookies)}')
        self.logger.info('📋 Collected cookies:')
        for name, value in self.login_cookies.items():
            self.logger.info(f'  - {name}: {value[:30]}...')

        if self.user_session_id:
            self.logger.info(f'✅ PHPSESSID ready for login: {self.user_session_id}')
        else:
            self.logger.info('ℹ️ No PHPSESSID found yet - will try during login')

        # Proceed to login page
        login_url = 'https://www.bhdstar.vn/tai-khoan/?login'
        cookie_header = '; '.join([f'{name}={value}' for name, value in self.login_cookies.items()])
        
        headers = {}
        if cookie_header:
            headers['Cookie'] = cookie_header
            self.logger.info(f'Adding {len(self.login_cookies)} cookies to login request')

        yield scrapy.Request(
            url=login_url,
            callback=self.handle_login_page,
            headers=headers,
            meta={'cookiejar': 1, 'dont_cache': True},
            dont_filter=True
        )

    def handle_login_page(self, response):
        """Handle the login page and extract login form data while preserving ALL cookies"""
        self.logger.info('📋 Processing login page and preserving ALL session cookies')
        self.logger.info(f'Login page status: {response.status}')
        
        # Process additional cookies from login page
        additional_cookies = response.headers.getlist('Set-Cookie')
        if additional_cookies:
            self.logger.info(f'Login page set {len(additional_cookies)} additional cookies')
            for i, header in enumerate(additional_cookies):
                cookie_str = header.decode('utf-8')
                self.logger.info(f'Login page Set-Cookie #{i + 1}: {cookie_str[:100]}...')
                
                if '=' in cookie_str:
                    cookie_parts = cookie_str.split(';')
                    name_value_part = cookie_parts[0].strip()
                    if '=' in name_value_part:
                        name, value = name_value_part.split('=', 1)
                        name = name.strip()
                        value = value.strip()
                        self.login_cookies[name] = value
                        self.logger.info(f'✅ Added/updated cookie: {name} = {value[:30]}...')
                        
                        if name == 'PHPSESSID':
                            self.user_session_id = value
                            self.logger.info(f'🎯 Updated PHPSESSID: {self.user_session_id}')

        # Extract login form data
        login_nonce = response.css('input#woocommerce-login-nonce::attr(value)').get()
        wp_http_referer = response.css('input[name="_wp_http_referer"]::attr(value)').get()
        
        username = self.settings.get('BHD_USERNAME')
        password = self.settings.get('BHD_PASSWORD')
        
        if not username or not password:
            self.logger.error('Login credentials not found in settings!')
            return

        form_data = {
            'username': username,
            'password': password,
            'woocommerce-login-nonce': login_nonce,
            '_wp_http_referer': wp_http_referer or '/',
            'login': 'Đăng nhập'
        }

        headers = {
            'Host': 'www.bhdstar.vn',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Origin': 'https://www.bhdstar.vn',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://www.bhdstar.vn/',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        cookie_header = '; '.join([f'{name}={value}' for name, value in self.login_cookies.items()])
        if cookie_header:
            headers['Cookie'] = cookie_header
            self.logger.info(f'🍪 Including ALL {len(self.login_cookies)} session cookies in login form')
            self.logger.info('📋 Cookies being sent:')
            for name, value in self.login_cookies.items():
                self.logger.info(f'  - {name}: {value[:30]}...')
            
            if self.user_session_id:
                self.logger.info(f'🎯 Including PHPSESSID: {self.user_session_id}')

        self.logger.info(f'Attempting login with username: {username}')
        self.logger.info(f'Using nonce: {login_nonce}')

        yield scrapy.FormRequest(
            url='https://www.bhdstar.vn/tai-khoan/?login',
            formdata=form_data,
            headers=headers,
            callback=self.after_login,
            meta={'cookiejar': 1, 'dont_cache': True},
            dont_filter=True
        )

    def after_login(self, response):
        """Check if login was successful and merge ALL session cookies"""
        self.logger.info(f'🔐 Login response status: {response.status}')
        
        # Process login response cookies
        login_response_cookies = response.headers.getlist('Set-Cookie')
        if login_response_cookies:
            self.logger.info(f'Login response set {len(login_response_cookies)} cookies')
            for i, header in enumerate(login_response_cookies):
                cookie_str = header.decode('utf-8')
                self.logger.info(f'Login response Set-Cookie #{i + 1}: {cookie_str[:100]}...')
                
                if '=' in cookie_str:
                    cookie_parts = cookie_str.split(';')
                    name_value_part = cookie_parts[0].strip()
                    if '=' in name_value_part:
                        name, value = name_value_part.split('=', 1)
                        name = name.strip()
                        value = value.strip()
                        self.login_cookies[name] = value
                        self.logger.info(f'✅ Merged login cookie: {name} = {value[:30]}...')

        # Check login success
        if response.status == 302 or 'my-account' in response.url or 'tai-khoan' in response.url:
            self.logger.info('✅ Login appears successful - proceeding with movie processing')
        else:
            self.logger.warning('⚠️ Login may have failed - proceeding anyway')

        # Start processing movies
        yield from self.start_movie_processing()

    def start_movie_processing(self):
        """Start processing movies after successful login"""
        self.logger.info(f'🎬 Starting to process {len(self.movie_data)} movies')
        
        for movie_data in self.movie_data:
            movie_url = movie_data.get('movie_url')
            if movie_url:
                yield scrapy.Request(
                    url=movie_url,
                    callback=self.get_movie_specific_data,
                    headers={'Cookie': self.create_cookie_header()},
                    meta={
                        'movie_data': movie_data,
                        'cookiejar': 1,
                        'dont_cache': True
                    },
                    dont_filter=True
                )

    def create_cookie_header(self):
        """Create cookie header string from login_cookies"""
        return '; '.join([f'{name}={value}' for name, value in self.login_cookies.items()])

    def get_movie_specific_data(self, response):
        """Extract movie-specific nonce and f value from each movie page"""
        movie_data = response.meta.get('movie_data', {})
        movie_title = movie_data.get('title', 'Unknown')
        movie_id = movie_data.get('movie_id')
        
        self.logger.info(f'Extracting movie-specific data from {response.url}')
        self.logger.info(f'Movie: {movie_title} (ID: {movie_id})')

        # Extract nonce
        nonce_pattern = r'"nonce":"([a-f0-9]+)"'
        nonce_match = re.search(nonce_pattern, response.text)
        if not nonce_match:
            self.logger.error(f'Could not find nonce for {movie_title}')
            return
        
        nonce = nonce_match.group(1)
        self.logger.info(f'Movie-specific nonce for {movie_title}: {nonce}')

        # Get f value
        if movie_id:
            f_value = movie_id
            self.logger.info(f'Using movie-specific f value from data-id: {f_value}')
        else:
            f_pattern = r'"f":(\d+)'
            f_match = re.search(f_pattern, response.text)
            if not f_match:
                self.logger.error(f'Could not find f value for {movie_title}')
                return
            f_value = f_match.group(1)
            self.logger.info(f'Extracted f value from page for {movie_title}: {f_value}')

        yield scrapy.Request(
            url=response.url,
            callback=self.parse,
            meta={
                'fresh_nonce': nonce,
                'f_value': f_value,
                'movie_data': movie_data,
                'cookiejar': 1,
                'dont_cache': True
            },
            headers={'Cookie': self.create_cookie_header()},
            dont_filter=True
        )

    def parse(self, response):
        """Parse movie detail pages and extract schedule data"""
        movie_data = response.meta.get('movie_data', {})
        movie_title = movie_data.get('title', 'Unknown')
        movie_id = movie_data.get('movie_id')
        
        self.logger.info(f'Processing movie page: {response.url}')
        self.logger.info(f'Movie: {movie_title} (ID: {movie_id})')

        # Check if session expired
        if 'tai-khoan' in response.url and 'login' in response.url:
            self.logger.warning(f'Session expired for {response.url}, skipping')
            return

        # Extract film ID from URL
        film_id = None
        url_match = re.search(r'/phim/([^/]+)/?', response.url)
        if url_match:
            film_id = url_match.group(1)
            self.logger.info(f'🎬 Extracted film ID: {film_id}')
        else:
            self.logger.warning(f'⚠️ Could not extract film ID from URL: {response.url}')
            film_id = 'unknown'

        # Get nonce and f_value from meta
        nonce = response.meta.get('fresh_nonce')
        f_value = response.meta.get('f_value')

        if not f_value:
            self.logger.info('No f_value provided, extracting from page content')
            f_pattern = r'"f":(\d+)'
            f_match = re.search(f_pattern, response.text)
            if not f_match:
                self.logger.error('Could not find f value in page content')
                return
            f_value = f_match.group(1)
            self.logger.info(f'Extracted f_value from page: {f_value}')
        else:
            self.logger.info(f'Using movie-specific f_value: {f_value}')

        if not nonce:
            self.logger.error(f'Missing fresh nonce in meta for {response.url}')
            return

        self.logger.info(f'Using fresh nonce: {nonce}')
        self.logger.info(f'Using movie-specific f_value: {f_value}')

        # Generate schedule requests for 7 days
        base_url = 'https://www.bhdstar.vn/wp-admin/admin-ajax.php'
        
        for day_offset in range(7):
            target_date = datetime.now() + timedelta(days=day_offset + 1)
            order_date = target_date.strftime('%d/%m/%Y')
            
            self.logger.info(f'📅 Generating request for date: {order_date} (Day {day_offset + 1}) for movie: {movie_title}')

            params = {
                'action': 'ldapp_order_get_schedule',
                'city': 'ha-noi',
                'orderDate': order_date,
                'f': f_value,
                'nonce': nonce
            }

            url = f'{base_url}?{urlencode(params)}'
            
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': response.url,
                'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
                'Cookie': self.create_cookie_header()
            }

            self.logger.info(f'🍪 Schedule API: Including {len(self.login_cookies)} cookies')

            yield scrapy.Request(
                url=url,
                method='GET',
                headers=headers,
                callback=self.parse_schedule,
                meta={
                    'search_date': order_date,
                    'movie_url': response.url,
                    'film_id': film_id,
                    'movie_title': movie_title,
                    'fresh_nonce': nonce,
                    'f_value': f_value,
                    'cookiejar': 1,
                    'dont_cache': True
                }
            )

    def parse_schedule(self, response):
        """Parse schedule and generate ticketing requests"""
        self.logger.info(f'Schedule API response status: {response.status}')
        self.logger.info(f'Schedule API response URL: {response.url}')

        if response.status != 200:
            self.logger.error(f'Schedule API failed with status {response.status}')
            return

        try:
            data = json.loads(response.text)
            
            if not data.get('success', False):
                self.logger.warning(f'Schedule API returned success=false: {data}')
                return

            schedule_html = data.get('data', '')
            if not schedule_html:
                self.logger.info('No schedule data returned')
                return

            # Parse the HTML schedule data
            schedule_selector = scrapy.Selector(text=schedule_html)
            
            # Extract theaters and sessions
            for theater in schedule_selector.css('div.cinema-item'):
                theater_name = theater.css('h3.cinema-name::text').get()
                theater_address = theater.css('p.cinema-address::text').get()
                
                if theater_name:
                    # Generate theater ID
                    theater_id = re.sub(r'[^a-zA-Z0-9]', '-', theater_name.lower())
                    
                    # Yield theater item
                    theater_item = TheaterItem()
                    theater_item['name'] = theater_name.strip()
                    theater_item['address'] = theater_address.strip() if theater_address else ''
                    theater_item['theaterID'] = theater_id
                    yield theater_item

                    # Extract sessions for this theater
                    for session in theater.css('div.showtime-item'):
                        session_id = session.css('::attr(data-session-id)').get()
                        if not session_id:
                            continue

                        # Check if we've already processed this session
                        if session_id in self.processed_sessions:
                            self.logger.debug(f'Skipping already processed session: {session_id}')
                            continue
                        
                        # Add to processed sessions
                        self.processed_sessions.add(session_id)

                        time_str = session.css('span.time::text').get()
                        format_str = session.css('span.format::text').get()
                        language_str = session.css('span.language::text').get()
                        firstclass = session.css('span.firstclass::text').get()

                        # Yield session item
                        session_item = SessionItem()
                        session_item['sessionID'] = session_id
                        session_item['filmID'] = response.meta['film_id']
                        session_item['time'] = time_str.strip() if time_str else ''
                        session_item['date'] = response.meta['search_date']
                        session_item['format'] = format_str.strip() if format_str else ''
                        session_item['language'] = language_str.strip() if language_str else ''
                        session_item['firstClass'] = firstclass.strip() if firstclass else ''
                        session_item['cinemaID'] = theater_id

                        yield session_item

                        # Also get seat data for this session
                        yield from self.get_seat_data_request(
                            session_id, theater_id, theater_name, response.meta
                        )

        except json.JSONDecodeError as e:
            self.logger.error(f'Failed to parse schedule JSON: {e}')
        except Exception as e:
            self.logger.error(f'Error parsing schedule: {e}')

    def get_seat_data_request(self, session_id, theater_id, theater_name, meta):
        """Generate seat data request"""
        movie_url = meta['movie_url']
        film_id = meta['film_id']
        f_value = meta['f_value']
        fresh_nonce = meta['fresh_nonce']
        
        seats_url = 'https://www.bhdstar.vn/wp-admin/admin-ajax.php'
        seats_params = {
            'action': 'ldapp_order_get_seats',
            'cinemaID': theater_id,
            'sessionID': session_id,
            'f': f_value,
            'nonce': fresh_nonce
        }

        referer_url = f'https://www.bhdstar.vn/dat-ve/?f={film_id}'
        
        headers = {
            'host': 'www.bhdstar.vn',
            'connection': 'keep-alive',
            'sec-ch-ua-platform': '"Windows"',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'sec-ch-ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': referer_url,
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-US,en;q=0.9',
            'cookie': self.create_cookie_header()
        }

        self.logger.info(f'🎟️ Making seats API call for session: {session_id}')

        yield scrapy.Request(
            url=f'{seats_url}?{urlencode(seats_params)}',
            method='GET',
            headers=headers,
            callback=self.parse_seats_data,
            meta={
                'cinemaID': theater_id,
                'sessionID': session_id,
                'cinema_name': theater_name,
                'movie_title': meta['movie_title'],
                'film_id': film_id,
                'search_date': meta['search_date'],
                'cookiejar': 1,
                'dont_cache': True
            },
            dont_filter=True
        )

    def parse_seats_data(self, response):
        """Parse the seats data and create SeatDataItem"""
        cinema_id = response.meta.get('cinemaID')
        session_id = response.meta.get('sessionID')
        cinema_name = response.meta.get('cinema_name')
        movie_title = response.meta.get('movie_title')
        search_date = response.meta.get('search_date')

        self.logger.info(f'🎟️ Processing seats API response for session {session_id}')

        try:
            data = json.loads(response.text)
            
            if not data.get('success', False):
                self.logger.warning(f'Seats API returned success=false for session {session_id}')
                return

            seat_data = data.get('data', {})
            
            # Create seat data item
            seat_item = SeatDataItem()
            seat_item['session_id'] = session_id
            seat_item['cinema_id'] = cinema_id
            seat_item['cinema_name'] = cinema_name
            seat_item['movie_title'] = movie_title
            seat_item['movie_format'] = seat_data.get('format', '')
            seat_item['movie_language'] = seat_data.get('language', '')
            seat_item['movie_label'] = seat_data.get('label', '')
            seat_item['showtime'] = seat_data.get('showtime', '')
            seat_item['screen_name'] = seat_data.get('screen_name', '')
            seat_item['screen_number'] = seat_data.get('screen_number', '')
            seat_item['seats_available'] = seat_data.get('available_seats', 0)
            seat_item['expire_time'] = seat_data.get('expire_time', '')
            seat_item['search_date'] = search_date
            
            # Store complex data as JSON strings
            seat_item['tickets_data'] = json.dumps(seat_data.get('tickets', []))
            seat_item['seats_layout'] = json.dumps(seat_data.get('layout', {}))
            seat_item['concession_items'] = json.dumps(seat_data.get('concessions', []))
            
            # Price summary
            prices = seat_data.get('prices', {})
            seat_item['standard_price'] = prices.get('standard', 0)
            seat_item['vip_price'] = prices.get('vip', 0)
            seat_item['couple_price'] = prices.get('couple', 0)

            yield seat_item

        except json.JSONDecodeError as e:
            self.logger.error(f'Failed to parse seat data JSON for session {session_id}: {e}')
        except Exception as e:
            self.logger.error(f'Error parsing seat data for session {session_id}: {e}')