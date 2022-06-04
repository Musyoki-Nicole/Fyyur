#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
from datetime import datetime
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
import os
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate (app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(150))
    image_link = db.Column(db.String(500))
    past_shows_count = db.Column(db.Integer, default=0)
    upcoming_shows_count = db.Column(db.Integer, default=0)
    shows = db.relationship('Show', backref='venue', lazy=True, cascade='all, delete')

    def toDict(self):
       return dict(id=self.id, name=self.name)

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(150))
    image_link = db.Column(db.String(500))
    past_shows_count = db.Column(db.Integer, default=0)
    upcoming_shows_count = db.Column(db.Integer, default=0)
    shows = db.relationship('Show', backref='artist', lazy=True, cascade='all, delete')
    
    def toDict(self):
       return dict(id=self.id, name=self.name)

class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id', ondelete='CASCADE'))
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'))
    start_time = db.Column(db.DateTime, nullable=False)

    def toDict(self):
       return dict(id=self.id, artist_id=self.artist_id, venue_id=self.venue_id)

db.create_all()
db.session.commit()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
    if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
      format="EE MM, dd, y h:mma"
  else:
    date = value
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  data = []
  venues = Venue.query.all()

  for venue in venues:
    data.append({
      "city": venue.city, 
      "state": venue.state, 
      "venues": [{
        "id": venue.id, 
        "name": venue.name, 
        "num_upcoming_shows": len(filtered_upcomingshows)
      }]
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():

  ven_search = Venue.query.filter(Venue.name.ilike('%' + request.form.get('search_term', '') + '%')).all()
  response={
    "count": len(ven_search),
    "data": ven_search
  } 

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  ven = Venue.query.get(venue_id)
  show = Show.query.join(Artist).filter(Show.venue_id == ven.id).first()
  art = Artist.query.join(Show).filter(Artist.id==Show.artist_id).first()

  if ven.past_shows_count > 0 and ven.upcoming_shows_count > 0:
    data={
      'id': ven.id,
      'name': ven.name,
      'genres': ven.genres,
      'city': ven.city,
      'state': ven.state,
      'address': ven.address,
      'phone': ven.phone,
      'website': ven.website_link,
      'facebook_link': ven.facebook_link,
      'image_link': ven.image_link,
      'seeking_talent': ven.seeking_talent,
      'seeking_description': ven.seeking_description,
      'past_shows_count': ven.past_shows_count,
      'upcoming_shows_count': ven.upcoming_shows_count,
      "past_shows": [{
        "artist_id": show.artist_id,
        "artist_name": art.name,
        "artist_image_link": art.image_link,
        "start_time": show.start_time
      }],
      "upcoming_shows": [{
        "artist_id":show.artist_id,
        "artist_name": art.name,
        "artist_image_link": art.image_link,
        "start_time": show.start_time
      }]
      }
  elif ven.past_shows_count == 0 and ven.upcoming_shows_count > 0:
    data={
      'id': ven.id,
      'name': ven.name,
      'genres': ven.genres,
      'city': ven.city,
      'state': ven.state,
      'address': ven.address,
      'phone': ven.phone,
      'website': ven.website_link,
      'facebook_link': ven.facebook_link,
      'image_link': ven.image_link,
      'seeking_talent': ven.seeking_talent,
      'seeking_description': ven.seeking_description,
      'past_shows_count': ven.past_shows_count,
      'upcoming_shows_count': ven.upcoming_shows_count,
      "upcoming_shows": [{
        "artist_id":show.artist_id,
        "artist_name": art.name,
        "artist_image_link": art.image_link,
        "start_time": show.start_time
      }]
      }
  elif ven.past_shows_count > 0 and ven.upcoming_shows_count == 0 :
    data={
      'id': ven.id,
      'name': ven.name,
      'genres': ven.genres,
      'city': ven.city,
      'state': ven.state,
      'address': ven.address,
      'phone': ven.phone,
      'website': ven.website_link,
      'facebook_link': ven.facebook_link,
      'image_link': ven.image_link,
      'seeking_talent': ven.seeking_talent,
      'seeking_description': ven.seeking_description,
      'past_shows_count': ven.past_shows_count,
      'upcoming_shows_count': ven.upcoming_shows_count,
      "past_shows": [{
        "artist_id": show.artist_id,
        "artist_name": art.name,
        "artist_image_link": art.image_link,
        "start_time": show.start_time
      }]
      }
  else:
    data={
      'id': ven.id,
      'name': ven.name,
      'genres': ven.genres,
      'city': ven.city,
      'state': ven.state,
      'address': ven.address,
      'phone': ven.phone,
      'website': ven.website_link,
      'facebook_link': ven.facebook_link,
      'image_link': ven.image_link,
      'seeking_talent': ven.seeking_talent,
      'seeking_description': ven.seeking_description,
      'past_shows_count': ven.past_shows_count,
      'upcoming_shows_count': ven.upcoming_shows_count
      }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():

  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  error = False
  form = VenueForm(request.form)

  try:
    venue = Venue(
      name=form.name.data, 
      city=form.city.data, 
      state=form.state.data, 
      address=form.address.data, 
      phone=form.phone.data, 
      genres=form.genres.data, 
      facebook_link=form.facebook_link.data, 
      image_link=form.image_link.data, 
      website_link=form.website_link.data, 
      seeking_talent=form.seeking_talent.data, 
      seeking_description=form.seeking_description.data
      )
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    db.session.close()
    if error == True:
      abort(400)
      flash('An error occurred. Venue ' + Venue.name + ' could not be listed.')
    else:
      return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):

    error = False
    try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
      flash('Venue was successfully deleted!')
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Venue ' + Venue.name + ' could not be deleted.')
    finally:
      db.session.close()
      return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  data = []
  showartists = Artist.query.all()

  for artist in showartists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  art_search = Artist.query.filter(Artist.name.ilike('%' + request.form.get('search_term', '') + '%')).all()
  response={
    "count": len(art_search),
    "data": art_search
  } 

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  art = Artist.query.get(artist_id)
  show = Show.query.join(Artist).filter(Show.artist_id == art.id).first()
  art_db = Artist.query.join(Show).filter(Artist.id==Show.artist_id).first()

  if art.past_shows_count > 0 and art.upcoming_shows_count > 0:
    data={
      'id': art.id,
      'name': art.name,
      'genres': art.genres,
      'city': art.city,
      'state': art.state,
      'phone': art.phone,
      'website': art.website_link,
      'facebook_link': art.facebook_link,
      'image_link': art.image_link,
      'seeking_venue': art.seeking_venue,
      'seeking_description': art.seeking_description,
      'past_shows_count': art.past_shows_count,
      'upcoming_shows_count': art.upcoming_shows_count,
      "past_shows": [{
        "artist_id": show.artist_id,
        "artist_name": art_db.name,
        "artist_image_link": art_db.image_link,
        "start_time": show.start_time
      }],
      "upcoming_shows": [{
        "artist_id":show.artist_id,
        "artist_name": art_db.name,
        "artist_image_link": art_db.image_link,
        "start_time": show.start_time
      }]
    }
  elif art.past_shows_count == 0 and art.upcoming_shows_count > 0:
    data={
      'id': art.id,
      'name': art.name,
      'genres': art.genres,
      'city': art.city,
      'state': art.state,
      'phone': art.phone,
      'website': art.website_link,
      'facebook_link': art.facebook_link,
      'image_link': art.image_link,
      'seeking_venue': art.seeking_venue,
      'seeking_description': art.seeking_description,
      'past_shows_count': art.past_shows_count,
      'upcoming_shows_count': art.upcoming_shows_count,
      "upcoming_shows": [{
        "artist_id":show.artist_id,
        "artist_name": art_db.name,
        "artist_image_link": art_db.image_link,
        "start_time": show.start_time
      }]
    }
  elif art.past_shows_count > 0 and art.upcoming_shows_count == 0:
    data={
      'id': art.id,
      'name': art.name,
      'genres': art.genres,
      'city': art.city,
      'state': art.state,
      'phone': art.phone,
      'website': art.website_link,
      'facebook_link': art.facebook_link,
      'image_link': art.image_link,
      'seeking_venue': art.seeking_venue,
      'seeking_description': art.seeking_description,
      'past_shows_count': art.past_shows_count,
      'upcoming_shows_count': art.upcoming_shows_count,
      "past_shows": [{
        "artist_id": show.artist_id,
        "artist_name": art_db.name,
        "artist_image_link": art_db.image_link,
        "start_time": show.start_time
      }]
    }
  else:
    data={
      'id': art.id,
      'name': art.name,
      'genres': art.genres,
      'city': art.city,
      'state': art.state,
      'phone': art.phone,
      'website': art.website_link,
      'facebook_link': art.facebook_link,
      'image_link': art.image_link,
      'seeking_venue': art.seeking_venue,
      'seeking_description': art.seeking_description,
      'past_shows_count': art.past_shows_count,
      'upcoming_shows_count': art.upcoming_shows_count,
    }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  error = False
  form = ArtistForm(request.form)
  try:
    artist = Artist.query.get(artist_id)
    artist.name=form.name.data
    artist.city=form.city.data
    artist.state=form.state.data
    artist.phone=form.phone.data
    artist.genres=form.genres.data
    artist.facebook_link=form.facebook_link.data
    artist.image_link=form.image_link.data
    artist.website_link=form.website_link.data
    artist.seeking_venue=form.seeking_venue.data 
    artist.seeking_description=form.seeking_description.data
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    flash('Artist ' + artist.name + ' was successfully edited!')
    db.session.close()
    if error == True:
      abort(400)
      flash('An error occurred. Artist ' + artist.name + ' could not be edited.')
    else:
      return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  error = False
  form = VenueForm(request.form)
  try:
    venue = Venue.query.get(venue_id)
    venue.name=form.name.data
    venue.city=form.city.data
    venue.state=form.state.data
    venue.address=form.address.data
    venue.phone=form.phone.data
    venue.genres=form.genres.data
    venue.facebook_link=form.facebook_link.data
    venue.image_link=form.image_link.data
    venue.website_link=form.website_link.data
    venue.seeking_talent=form.seeking_talent.data 
    venue.seeking_description=form.seeking_description.data
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    flash('Venue ' + venue.name + ' was successfully edited!')
    db.session.close()
    if error == True:
      abort(400)
      flash('An error occurred. Venue ' + venue.name + ' could not be edited.')
    else:
      return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():

  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  error = False
  form = ArtistForm(request.form)
  try:
    artist = Artist(
      name=form.name.data, 
      city=form.city.data, 
      state=form.state.data,  
      phone=form.phone.data, 
      genres=form.genres.data, 
      facebook_link=form.facebook_link.data, 
      image_link=form.image_link.data, 
      website_link=form.website_link.data, 
      seeking_venue=form.seeking_venue.data, 
      seeking_description=form.seeking_description.data
      )
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
    if error == True:
      abort(400)
      flash('An error occurred. Artist ' + Artist.name + ' could not be listed.')
    else:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
      return render_template('pages/home.html')

@app.route('/artist/<artist_id>', methods=['POST'])
def delete_artist(artist_id):

    error = False
    try:
      artist = Artist.query.get(artist_id)
      db.session.delete(artist)
      db.session.commit()
      flash('Artist was successfully deleted!')
    except:
      error = True
      print(sys.exc_info())
      db.session.rollback()
      flash('An error occurred. Artist ' + artist.name + ' could not be deleted.')
    finally:
      db.session.close()
      return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  data = []
  showshows = Show.query.all()

  for show in showshows:
    artist = Artist.query.get(show.artist_id)
    venue = Venue.query.get(show.venue_id)
    data.append({
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  error = False
  form = ShowForm(request.form)
  try:
    show = Show( 
      artist_id=form.artist_id.data,
      venue_id=form.show.venue_id.data, 
      start_start=form.start_time.data
      )
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exec_info())
  finally:
    db.session.close()
    if error == True:
      abort(400)
      flash('An error occurred. Show could not be listed.')
    else:
      flash('Show was successfully listed!')
      return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#
'''
# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

