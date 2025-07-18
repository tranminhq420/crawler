import logging
from itemadapter import ItemAdapter
from sqlalchemy.orm import sessionmaker
from .models import db_connect, create_table, Film, Screentime, Theater, SeatData
from .items import TheaterItem, SessionItem, HanoicineItem, SeatDataItem
from scrapy.crawler import CrawlerRunner
from scrapy.signalmanager import dispatcher
from scrapy.utils.project import get_project_settings
from scrapy.exceptions import DropItem
from twisted.internet import reactor, defer
from datetime import datetime, time


class SQLAlchemyPipeline:
    """
    Pipeline for storing scraped items in the database
    """

    def __init__(self):
        """
        Initializes database connection and sessionmaker
        Creates tables if they don't exist
        """
        engine = db_connect()
        create_table(engine)
        self.Session = sessionmaker(bind=engine)
        self.hanoi_cine_first_run = True
        self.items = []  # Clear items list for fresh run

        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Pipeline initialized with empty items list")

    def process_item(self, item, spider):
        print(f"=== PIPELINE: process_item called ===")
        print(f"Spider: {spider.name}")
        print(f"Item type: {type(item)}")
        print(f"Item class name: {item.__class__.__name__}")

        if spider.name == "hanoicine":
            return self.process_hanoi_cine_data(item)
        elif spider.name == "rapquocgia":
            if isinstance(item, HanoicineItem):
                print("Routing to process_rapquocgia_film")
                return self.process_rapquocgia_film(item)
            elif isinstance(item, SessionItem):
                print("Routing to process_rapquocgia_session")
                return self.process_rapquocgia_session(item)
            elif isinstance(item, TheaterItem):
                print("Routing to process_rapquocgia_theater")
                return self.process_rapquocgia_theater(item)
            else:
                print(f"Unknown item type for rapquocgia spider: {type(item)}")
                return item
        elif spider.name == "bhd":
            if isinstance(item, TheaterItem):
                print("Routing to process_bhd_theater")
                return self.process_bhd_theater(item)
            elif isinstance(item, SessionItem):
                print("Routing to process_bhd_session")
                return self.process_bhd_session(item)
            elif isinstance(item, SeatDataItem):
                print("Routing to process_seat_data")
                return self.process_seat_data(item)
            else:
                print(f"Unknown item type for BHD spider: {type(item)}")
                return item
        else:
            print(f"Unknown spider: {spider.name}")
            return item

    def process_hanoi_cine_data(self, item):
        # Handle None items
        if item is None:
            raise DropItem("Item is None")

        # Check if any required fields are None/empty (handle tuple values)
        required_fields = ['age_limit', 'format']
        missing_fields = []

        for field in required_fields:
            value = item.get(field)
            # Handle tuple values - check if tuple contains None or is empty
            if isinstance(value, tuple):
                if not value or value[0] is None or not str(value[0]).strip():
                    missing_fields.append(field)
            # Handle regular values
            elif not value or not str(value).strip():
                missing_fields.append(field)

        if missing_fields:
            raise DropItem(f"Missing required fields: {missing_fields}")

        session = self.Session()

        try:
            if self.hanoi_cine_first_run:
                session.query(Film).delete()
                session.commit()
                self.hanoi_cine_first_run = False

            # Check if film already exists
            existing_film = session.query(Film).filter(
                Film.title == item.get('title')).first()

            if not existing_film:
                film = Film()

                # Map fields from item to model (extract from tuples if needed)
                film.title = item.get('title')
                film.age_limit = item.get('age_limit')
                film.movie_type = item.get('movie_type')
                film.format = item.get('format')
                film.genre = item.get('genre')
                film.image_url = item.get('image_url')
                film.booking_url = item.get('movie_url')

                session.add(film)
                session.commit()
                self.logger.info(f"Saved film: {film.title}")

        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Error processing film item {item.get('id')}: {e}")
            raise DropItem(f"Database error: {e}")
        finally:
            session.close()

        self.items.append({
            'movie_url': item.get('movie_url'),
            'movie_id': item.get('id'),  # This contains the data-id which becomes the f parameter
            'title': item.get('title')
        })
        return item

    def process_rapquocgia_film(self, item):
        """Process film items from rapquocgia spider"""
        print(f"=== PIPELINE: Processing rapquocgia film item ===")
        print(f"Film ID: {item.get('id')}")
        print(f"Film Title: {item.get('title')}")

        session = self.Session()

        try:
            # Check if film already exists by rapquocgia film ID
            rqg_film_id = item.get('rqg_film_id')
            existing_film = session.query(Film).filter(Film.rqg_film_id == rqg_film_id).first()

            if existing_film:
                print(f"Film '{item.get('title')}' (ID: {rqg_film_id}) already exists in database")
                # Update existing film with new data
                existing_film.title = item.get('title')
                existing_film.age_limit = item.get('age_limit')
                existing_film.movie_type = item.get('movie_type')
                existing_film.format = item.get('format')
                existing_film.genre = item.get('genre')
                existing_film.image_url = item.get('image_url')
                existing_film.booking_url = item.get('movie_url')
                print(f"Updated existing film: {existing_film.title}")
            else:
                print(f"Creating new film: '{item.get('title')}' (ID: {rqg_film_id})")
                film = Film()
                film.rqg_film_id = rqg_film_id
                film.title = item.get('title')
                film.age_limit = item.get('age_limit')
                film.movie_type = item.get('movie_type')
                film.format = item.get('format')
                film.genre = item.get('genre')
                film.image_url = item.get('image_url')
                film.booking_url = item.get('movie_url')
                
                session.add(film)
                print(f"Added new film: {film.title} (ID: {rqg_film_id})")

            session.commit()
            print(f"Successfully saved film: {item.get('title')}")

        except Exception as e:
            print(f"ERROR in process_rapquocgia_film: {e}")
            import traceback
            traceback.print_exc()
            session.rollback()
            raise
        finally:
            session.close()

        return item

    def process_rapquocgia_session(self, item):
        """Process session items from rapquocgia spider"""
        print(f"=== PIPELINE: Processing rapquocgia session item ===")
        print(f"Session ID: {item.get('sessionID')}")
        print(f"Film ID: {item.get('filmID')}")

        session = self.Session()

        try:
            # Check if session already exists
            session_id = item.get('sessionID')
            existing_session = session.query(Screentime).filter(
                Screentime.name == str(session_id)
            ).first()

            if existing_session:
                print(f"Session {session_id} already exists in database, skipping")
                return item

            screening = Screentime()
            screening.name = str(session_id)
            screening.format = item.get('format')
            
            # Parse ProjectTime (e.g., "2025-06-03T14:45:00")
            time_str = item.get('time')
            if time_str:
                try:
                    # Extract time from datetime string
                    from datetime import datetime
                    dt = datetime.fromisoformat(time_str.replace('Z', ''))
                    screening.time = dt.time()
                    screening.date = dt.date()
                except (ValueError, AttributeError):
                    print(f"Invalid time format: {time_str}")
                    screening.time = None
                    screening.date = None
            
            # Parse ProjectDate (e.g., "2025-06-03T00:00:00")
            date_str = item.get('date')
            if date_str and not screening.date:
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', ''))
                    screening.date = dt.date()
                except (ValueError, AttributeError):
                    print(f"Invalid date format: {date_str}")

            screening.language = item.get('language')
            screening.firstclass = str(item.get('firstClass', ''))
            screening.cinema_id = str(item.get('cinemaID', ''))
            screening.film_id = str(item.get('filmID', ''))

            session.add(screening)
            session.commit()
            print(f"Successfully saved session: {screening.name} for film: {screening.film_id}")

        except Exception as e:
            print(f"ERROR in process_rapquocgia_session: {e}")
            import traceback
            traceback.print_exc()
            session.rollback()
            raise
        finally:
            session.close()

        return item

    def process_rapquocgia_theater(self, item):
        """Process theater items from rapquocgia spider"""
        print(f"=== PIPELINE: Processing rapquocgia theater item ===")
        print(f"Theater Name: {item.get('name')}")
        print(f"Theater Address: {item.get('address')}")

        session = self.Session()

        try:
            # Check if theater already exists
            theater_id = item.get('theaterID')
            existing_theater = session.query(Theater).filter(
                Theater.theater_id == theater_id
            ).first()

            if existing_theater:
                print(f"Theater '{item.get('name')}' already exists in database, updating")
                # Update existing theater
                existing_theater.name = item.get('name')
                existing_theater.location = item.get('address')
                print(f"Updated existing theater: {existing_theater.name}")
            else:
                print(f"Creating new theater: '{item.get('name')}'")
                theater = Theater()
                theater.name = item.get('name')
                theater.location = item.get('address')
                theater.theater_id = theater_id
                
                session.add(theater)
                print(f"Added new theater: {theater.name}")

            session.commit()
            print(f"Successfully saved theater: {item.get('name')}")

        except Exception as e:
            print(f"ERROR in process_rapquocgia_theater: {e}")
            import traceback
            traceback.print_exc()
            session.rollback()
            raise
        finally:
            session.close()

        return item

    def process_bhd_theater(self, item):
        print(f"=== PIPELINE: Processing theater item ===")
        print(f"Item type: {type(item)}")
        print(f"Item dict: {dict(item)}")

        session = self.Session()

        try:
            # Get values from item
            theater_name = item.get('name')
            theater_address = item.get('address')
            theater_id = item.get('theaterID')

            print(f"Extracted values:")
            print(f"  Name: '{theater_name}'")
            print(f"  Address: '{theater_address}'")
            print(f"  ID: '{theater_id}'")

            if not theater_name:
                print("ERROR: Theater name is empty!")
                return item

            # Check if theater exists
            existing_theater = session.query(Theater).filter(
                Theater.name == theater_name).first()

            if existing_theater:
                print(f"Theater '{theater_name}' already exists in database")
            else:
                print(f"Creating new theater: '{theater_name}'")

                theater = Theater()
                theater.name = theater_name
                theater.location = theater_address
                theater.theater_id = theater_id

                print(f"Theater object created:")
                print(f"  theater.name = '{theater.name}'")
                print(f"  theater.location = '{theater.location}'")
                print(f"  theater.theater_id = '{theater.theater_id}'")

                session.add(theater)
                print("Theater added to session")

                session.commit()
                print("Session committed - theater should be saved!")

                # Verify it was saved
                verification = session.query(Theater).filter(
                    Theater.name == theater_name).first()
                if verification:
                    print(
                        f"SUCCESS: Theater verified in database with ID: {verification.id}")
                else:
                    print("ERROR: Theater not found after commit!")

        except Exception as e:
            print(f"ERROR in process_bhd_theater: {e}")
            import traceback
            traceback.print_exc()
            session.rollback()
            raise
        finally:
            session.close()

        return item

    def process_bhd_session(self, item):
        """Process session items"""
        self.logger.info(f"Processing session: {item}")
        session = self.Session()

        try:
            # Check if session already exists for this specific film to avoid duplicates
            session_id = item.get('sessionID')
            film_id = item.get('filmID')
            
            existing_session = session.query(Screentime).filter(
                Screentime.name == session_id,
                Screentime.film_id == film_id
            ).first()
            
            if existing_session:
                self.logger.info(f"Session {session_id} for film {film_id} already exists in database, skipping")
                return item
            
            screening = Screentime()
            screening.name = session_id
            screening.format = item.get('format')
            
            # Convert time string to time object
            time_str = item.get('time')  # e.g., '23:55'
            if time_str:
                try:
                    time_parts = time_str.split(':')
                    screening.time = time(hour=int(time_parts[0]), minute=int(time_parts[1]))
                except (ValueError, IndexError):
                    self.logger.warning(f"Invalid time format: {time_str}")
                    screening.time = None
            else:
                screening.time = None
            
            # Convert date string to datetime object
            date_str = item.get('date')  # e.g., '06/06/2025'
            if date_str:
                try:
                    # Parse MM/DD/YYYY format
                    screening.date = datetime.strptime(date_str, '%m/%d/%Y')
                except ValueError:
                    self.logger.warning(f"Invalid date format: {date_str}")
                    screening.date = None
            else:
                screening.date = None
            
            screening.language = item.get('language')
            screening.firstclass = item.get('firstClass')
            screening.cinema_id = item.get('cinemaID')
            screening.film_id = film_id  # Link session to film

            session.add(screening)
            session.commit()
            self.logger.info(f"Successfully saved session: {screening.name} for film: {screening.film_id}")

        except Exception as e:
            session.rollback()
            self.logger.error(f"Error saving session: {e}")
            raise
        finally:
            session.close()

        return item

    def process_seat_data(self, item):
        """Process seat data items"""
        self.logger.info(f"Processing seat data: session {item.get('session_id')}")
        session = self.Session()

        try:
            # Check if seat data already exists for this session
            existing_seat_data = session.query(SeatData).filter(
                SeatData.session_id == item.get('session_id'),
                SeatData.search_date == item.get('search_date')
            ).first()

            if existing_seat_data:
                self.logger.info(f"Seat data already exists for session {item.get('session_id')}")
                return item

            seat_data = SeatData()
            seat_data.session_id = item.get('session_id')
            seat_data.cinema_id = item.get('cinema_id')
            seat_data.cinema_name = item.get('cinema_name')
            seat_data.movie_title = item.get('movie_title')
            seat_data.movie_format = item.get('movie_format')
            seat_data.movie_language = item.get('movie_language')
            seat_data.movie_label = item.get('movie_label')
            seat_data.screen_name = item.get('screen_name')
            seat_data.screen_number = item.get('screen_number')
            seat_data.seats_available = item.get('seats_available')
            seat_data.search_date = item.get('search_date')
            
            # Handle datetime fields
            showtime_str = item.get('showtime')
            if showtime_str:
                try:
                    from datetime import datetime
                    seat_data.showtime = datetime.fromisoformat(showtime_str.replace('T', ' ').replace('Z', ''))
                except ValueError:
                    self.logger.warning(f"Invalid showtime format: {showtime_str}")
                    seat_data.showtime = None
            
            expire_time_str = item.get('expire_time')
            if expire_time_str:
                try:
                    seat_data.expire_time = datetime.strptime(expire_time_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    self.logger.warning(f"Invalid expire_time format: {expire_time_str}")
                    seat_data.expire_time = None
            
            # Store JSON data
            seat_data.tickets_data = item.get('tickets_data')
            seat_data.seats_layout = item.get('seats_layout')
            seat_data.concession_items = item.get('concession_items')
            
            # Store pricing summary
            seat_data.standard_price = item.get('standard_price')
            seat_data.vip_price = item.get('vip_price')
            seat_data.couple_price = item.get('couple_price')

            session.add(seat_data)
            session.commit()
            self.logger.info(f"Successfully saved seat data for session: {seat_data.session_id}")

        except Exception as e:
            session.rollback()
            self.logger.error(f"Error saving seat data: {e}")
            raise
        finally:
            session.close()

        return item

    @defer.inlineCallbacks
    def close_spider(self, spider):
        if spider.name == "hanoicine":
            self.logger.info(
                "Hanoicine spider finished, starting BHD spider...")

            self.logger.info(f"Total URLs collected: {len(self.items)}")
            self.logger.info(f"URLs to pass to BHD spider: {self.items}")

            # Create settings for the second spider
            settings = get_project_settings()
            settings.set('URLS', self.items)

            # Use CrawlerRunner instead of CrawlerProcess
            runner = CrawlerRunner(settings)

            try:
                # Start the second spider
                yield runner.crawl('bhd')
                self.logger.info("BHD spider completed successfully")
            except Exception as e:
                self.logger.error(f"Error running BHD spider: {e}")
            finally:
                # Stop the reactor when done
                if reactor.running:
                    reactor.stop()
